# -*- coding: utf-8 -*-
# Copyright (c) 2022, Alliance for Sustainable Energy, LLC

# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

""" This module contains classes for managing creation
of primary network sections. """
import math
import copy
from abc import ABC, abstractmethod
import itertools
import uuid
from typing import List, Union, Callable

import numpy as np
import pandas as pd
from networkx.algorithms import approximation as ax
import networkx as nx

from shift.graph import OpenStreetRoadNetwork
from shift.constants import MIN_POLE_TO_POLE_DISTANCE, MAX_POLE_TO_POLE_DISTANCE
from shift.exceptions import (
    PoleToPoleDistanceNotInRange,
    IncompleteGeometryConfigurationDict,
)
from shift.utils import (
    slice_up_network_edges,
    get_nearest_points_in_the_network,
)
from shift.constants import (
    MIN_ADJUSTMENT_FACTOR,
    MAX_ADJUSTMENT_FACTOR,
    MIN_POWER_FACTOR,
    MAX_POWER_FACTOR,
    MIN_PERCENTAGE,
    MAX_PERCENTAGE,
    MIN_YEAR_OPERATION,
    MAX_YEAR_OPERATION,
    OVERHEAD_CONDUCTOR_CATALOG_FILE,
    OVERHEAD_CONDUCTOR_CATALAOG_SCHEMA,
    UNDERGROUND_CONCENTRIC_CABLE_CATALOG_SCHEMA,
    UG_CONCENTRIC_CABLE_CATALOG_FILE,
    LENGTH_CONVERTER_TO_CM,
)
from shift.exceptions import (
    AdjustmentFactorNotInRangeError,
    PowerFactorNotInRangeError,
    NegativeKVError,
    ZeroKVError,
    AttributeDoesNotExistError,
    PercentageNotInRangeError,
    OperationYearNotInRange,
    EmptyCatalog,
    CatalogNotFoundError,
)
from shift.enums import ConductorType, NumPhase, Phase
from shift.utils import df_validator, get_distance
from shift.line_section import (
    GeometryBasedLine,
    OverheadLineGeometry,
    OverheadLinewithNeutralGeometry,
    LineGeometryConfiguration,
    UndergroundLineGeometry,
    Wire,
    Cable,
    Line,
)


def choose_conductor(
    catalog: pd.DataFrame,
    ampacity: float,
    k_drop: float,
    geometry_configuration: LineGeometryConfiguration,
    num_of_phase: NumPhase,
    kv_base: float,
    pf: float = 0.9,
) -> dict:
    """Handles selection of conductor from the catalog.

    Args:
        catalog (pd.DataFrame): Dataframe containing all the catalogs
        ampacity (float): Minimum ampacity required
        k_drop (float): Percentage drop per kva per miles expected
        geometry_configuration (LineGeometryConfiguration):
            LineGeometryConfiguration instance
        num_of_phase (NumPhase): NumPhase Instance
        kv_base (float): Line to line kv base to be used to compute kva
        pf (float): Power factor to be used to compute kva

    Raises:
        CatalogNotFoundError: If the catalog record is not
            found for given ampacity

    Returns:
        dict: Catalog record in dict format
    """

    # First thing is to find catalog for higher amps than required
    conductors_above_ampacity = catalog[catalog["ampacity"] > ampacity]
    if conductors_above_ampacity.empty:
        raise CatalogNotFoundError(
            f"No conductor exists for ampacity {ampacity}A in the filtered set!"
        )

    conductors_above_ampacity = conductors_above_ampacity.sort_values(
        by=["ampacity"]
    )
    for record in conductors_above_ampacity.to_dict(orient="records"):

        # Get configuration array for conductors
        x_array = geometry_configuration.get_x_array()[:num_of_phase]

        # Compute the equivalent distance
        deq = (
            np.power(
                np.prod(
                    [
                        abs(el[0] - el[1])
                        for el in itertools.combinations(x_array, 2)
                    ]
                ),
                1 / len(x_array),
            )
            if len(x_array) != 1
            else record["gmrac"]
        )

        # Get the unit for deq
        deq_unit = (
            geometry_configuration.unit
            if len(x_array) != 1
            else record["gmrunit"]
        )

        # Convert deq to ft
        deq_ft = deq * LENGTH_CONVERTER_TO_CM[deq_unit] * 0.0328084

        # Convert gmr to ft
        gmr_ft = (
            record["gmrac"]
            * LENGTH_CONVERTER_TO_CM[record["gmrunit"]]
            * 0.0328084
        )

        # Convert rac to ohm/mile
        r_mile = (
            record["rac"] * LENGTH_CONVERTER_TO_CM[record["runit"]] / 160934
        )

        # Compute positive sequence impedance ohm/mile
        zpos = complex(r_mile, 0.12134 * np.log(deq_ft / gmr_ft))

        # Current
        current = complex(
            ampacity * pf, -ampacity * np.power(1 - pf * pf, 1 / 2)
        )

        # voltage drop
        vdrop_pct = (
            (zpos * current).real * 100 * math.sqrt(3) / (kv_base * 1000)
        )

        # Compute kdrop
        if ampacity == 0:
            ampacity = 1
        k_drop_computed = vdrop_pct / (ampacity * kv_base * math.sqrt(3))

        # print('k_drop : ', k_drop, k_drop_computed,
        # record['name'], record['ampacity'])
        if k_drop_computed <= k_drop:
            return record

    # print(k_drop_computed, k_drop, ampacity, record)
    # raise ConductorNotFoundForKdrop(k_drop)
    return record  # pylint: disable=undefined-loop-variable


def convert_oh_cond_info_to_wire(data: dict) -> Wire:
    """Converts catalog record into wire object.

    Args:
        data (dict): Catalog record

    Returns:
        Wire: Wire object instance
    """

    data = copy.deepcopy(data)

    wire = Wire()
    wire.name = data["name"]
    wire.diam = data["diameter"]
    wire.gmrac = data["gmrac"]
    wire.gmrunits = data["gmrunit"]
    wire.normamps = data["ampacity"]
    wire.rac = data["rac"]
    wire.runits = data["runit"]
    wire.radunits = data["diameterunit"]

    return wire


def convert_ug_cond_info_to_cable(data: dict) -> Cable:
    """Converts catalog record into cable object.

    Args:
        data (dict): Catalog record

    Returns:
        Cable: Cable object instance
    """

    data = copy.deepcopy(data)

    cable = Cable()
    cable.name = data["name"]
    cable.diam = data["diam"]
    cable.gmrac = data["gmrac"]
    cable.gmrunits = data["gmrunit"]
    cable.normamps = data["ampacity"]
    cable.rac = data["rac"]
    cable.runits = data["runit"]
    cable.radunits = data["radunits"]
    cable.inslayer = data["inslayer"]
    cable.diains = data["diains"]
    cable.diacable = data["diacable"]
    cable.rstrand = data["rstrand"]
    cable.gmrstrand = data["gmrstrand"]
    cable.diastrand = data["diastrand"]
    cable.k = data["k"]
    return cable


def geometry_based_line_section_builder(
    from_node: str,
    to_node: str,
    num_phase: NumPhase,
    from_phase: Phase,
    to_phase: Phase,
    length: float,
    length_unit: str,
    ampacity: float,
    catalog: pd.DataFrame,
    neutral_present: bool,
    conductor_type: ConductorType,
    geometry_configuration: LineGeometryConfiguration,
    k_drop: float,
    kv_base: float,
    material: str = "all",
) -> Line:
    """Builds a line section.

    Args:
        from_node (str): From node
        to_node (str): To node
        num_phase (NumPhase): NumPhase Instance
        from_phase (Phase): Phase instance for from node
        to_phase (Phase): Phase instance for to node
        length (float): Length of line segment
        length_unit (str): Unit for line length
        ampacity (float): Ampacity for the conductor
        catalog (pd.DataFrame): DataFrame containing all the catalaogs
        neutral_present (bool): Indicates whether neutral is present or not
        conductor_type (ConductorType): ConductorType instance
        geometry_configuration (LineGeometryConfiguration):
            LineGeometryConfiguration instance
        k_drop (float): Expected percentage voltage drop per kva per mile
        kv_base (float): kV base for computing kVA
        material (str): Material for choosing conductor

    Raises:
        EmptyCatalog: If the material is not found in catalog

    Returns:
        Line: Line instance
    """

    if material != "all":
        catalog = catalog.loc[catalog["material"] == material]
        if catalog.empty:
            raise EmptyCatalog(f"Catalog of material {material} not found!")

    line_section = GeometryBasedLine()
    line_section.name = from_node + "__" + to_node
    line_section.fromnode = from_node
    line_section.tonode = to_node
    line_section.length = length
    line_section.length_unit = length_unit
    line_section.num_phase = num_phase
    line_section.fromnode_phase = from_phase
    line_section.tonode_phase = to_phase

    # Get the geometry object
    if conductor_type == ConductorType.OVERHEAD:
        if neutral_present:
            line_geometry = OverheadLinewithNeutralGeometry()

            # Let's find the condcutor to be used
            phase_cond_dict = choose_conductor(
                catalog,
                ampacity,
                k_drop,
                geometry_configuration,
                num_phase.value,
                kv_base,
            )
            # catalog.loc[catalog[catalog['ampacity']>ampacity]
            # ['ampacity'].idxmin()].to_dict()
            line_geometry.phase_wire = convert_oh_cond_info_to_wire(
                phase_cond_dict
            )

            # Assuming neutral conductor would be one third of
            # phase conductor ampacity for multi phase else
            # same as phase conductor
            neutral_cond_dict = (
                phase_cond_dict
                if num_phase == NumPhase.SINGLE
                else choose_conductor(
                    catalog,
                    ampacity / 3,
                    k_drop,
                    geometry_configuration,
                    num_phase.value,
                    kv_base,
                )
            )

            line_geometry.neutral_wire = convert_oh_cond_info_to_wire(
                neutral_cond_dict
            )
            line_geometry.num_conds = num_phase.value + 1

        else:
            line_geometry = OverheadLineGeometry()
            phase_cond_dict = choose_conductor(
                catalog,
                ampacity,
                k_drop,
                geometry_configuration,
                num_phase.value,
                kv_base,
            )
            line_geometry.phase_wire = convert_oh_cond_info_to_wire(
                phase_cond_dict
            )
            line_geometry.num_conds = num_phase.value

    else:
        line_geometry = UndergroundLineGeometry()
        if num_phase == NumPhase.THREE:
            catalog = catalog[catalog["neutral_type"] == "1/3 Neutral"]
        else:
            catalog = catalog[catalog["neutral_type"] == "Full Neutral"]

        cable_dict = choose_conductor(
            catalog,
            ampacity,
            k_drop,
            geometry_configuration,
            num_phase.value,
            kv_base,
        )
        line_geometry.phase_cable = convert_ug_cond_info_to_cable(cable_dict)
        line_geometry.num_conds = num_phase.value

    line_geometry.name = str(uuid.uuid4()) + "_linegeometry"
    line_geometry.num_phase = num_phase
    line_geometry.configuration = geometry_configuration
    line_section.geometry = line_geometry
    return line_section


class BaseSectionsBuilder:
    """Interface for sections builder.

    Attributes:
        network (nx.Graph): Graph instance
        conductor_type (ConductorType): ConductorType instance
        geometry_configuration (dict): Line configuration data
        num_phase (NumPhase): NumPhase instance
        phase (Phase): Phase instance
        neutral_present (bool): Indicates whether neutral is present or not
        material (str): Conductor material
        overhead_conductor_catalog (pd.DataFrame): DataFrame
            containing catalogs for overhead conductors
        concentric_cable_catalog (pd.DataFrame): DataFrame
            containing catalogs for concentric cables
        catalog_dict (dict): Mapping between conductor
            type and conductor catalogs
    """

    def __init__(
        self,
        network: nx.Graph,
        conductor_type: ConductorType,
        configuration: dict,
        num_phase: NumPhase,
        phase: Phase,
        neutral_present: bool = False,
        material: str = "all",
    ) -> None:
        """Constructor for `BaseSectionsBuilder` class.

        Args:
            network (nx.Graph): Graph instance
            conductor_type (ConductorType): ConductorType instance
            configuration (dict): Line configuration data
            num_phase (NumPhase): NumPhase instance
            phase (Phase): Phase instance
            neutral_present (bool): Indicates whether neutral is present or not
            material (str): Conductor material
        """

        self.network = network
        self.conductor_type = conductor_type
        self.geometry_configuration = configuration
        self.num_phase = num_phase
        self.neutral_present = neutral_present
        self.material = material
        self.phase = phase

        self.overhead_conductor_catalog = pd.read_excel(
            OVERHEAD_CONDUCTOR_CATALOG_FILE
        )
        df_validator(
            OVERHEAD_CONDUCTOR_CATALAOG_SCHEMA, self.overhead_conductor_catalog
        )

        self.concentric_cable_catalog = pd.read_excel(
            UG_CONCENTRIC_CABLE_CATALOG_FILE
        )
        df_validator(
            UNDERGROUND_CONCENTRIC_CABLE_CATALOG_SCHEMA,
            self.concentric_cable_catalog,
        )

        self.catalog_dict = {
            ConductorType.OVERHEAD: self.overhead_conductor_catalog,
            ConductorType.UNDERGROUND_CONCENTRIC: self.concentric_cable_catalog,
        }


class PrimarySectionsBuilder(BaseSectionsBuilder):
    """Class handling generation of primary line sections."""

    def generate_primary_line_sections(
        self, k_drop: float, kv_base: float
    ) -> List[Line]:
        """Method for creating primary line sections.

        Args:
            k_drop (float): Expected percentage voltage drop per mile per kva
            kv_base (float): KV base used for computing kVA

        Returns:
            List[Line]: List of `Line` instances
        """

        line_sections = []
        node_data_dict = {
            node[0]: node[1] for node in self.network.nodes.data()
        }

        for edge in self.network.edges():
            edge_data = self.network.get_edge_data(*edge)

            if self.num_phase not in self.geometry_configuration:
                raise IncompleteGeometryConfigurationDict(
                    self.num_phase, self.geometry_configuration
                )

            line_section = geometry_based_line_section_builder(
                edge[0],
                edge[1],
                self.num_phase,
                self.phase,
                self.phase,
                get_distance(
                    node_data_dict[edge[0]]["pos"],
                    node_data_dict[edge[1]]["pos"],
                ),
                "m",
                edge_data["ampacity"],
                self.catalog_dict[self.conductor_type],
                self.neutral_present,
                self.conductor_type,
                self.geometry_configuration[self.num_phase],
                k_drop,
                kv_base,
                self.material,
            )
            line_sections.append(line_section)

        return line_sections


class BaseNetworkBuilder(ABC):
    """Interface for building distribution network.

    Attributes:
        div_func (Callable[[float], float]): Diversity factor
            function coefficients
        kv_ll (float): Line to line voltage in KV
        max_pole_to_pole_distance (float): Maximum pole to
            pole distance in meter
        power_factor (float): Power factor used to compute kva
        adjustment_factor (float): Adjustment factor for
            adjusting kva
        planned_avg_annual_growth (float): Planned average annual
            load growth rate in percentage
        actual_avg_annual_growth (float): Actual average annual
            load growth rate in percentage
        actual_years_in_operation (float): Actual years in operation
        planned_years_in_operation (float): Planned years in operation
    """

    def __init__(
        self,
        div_func: Callable[[float], float],
        kv_ll: float,
        max_pole_to_pole_distance: float = 100,
        power_factor: float = 0.9,
        adjustment_factor: float = 1.2,
        planned_avg_annual_growth: float = 2,
        actual_avg_annual_growth: float = 4,
        actual_years_in_operation: float = 15,
        planned_years_in_operation: float = 10,
    ) -> None:
        """Constructor for `BaseNetworkBuilder` class.

        Args:
            div_func (Callable[[float], float]): Diversity factor
                function coefficients
            kv_ll (float): Line to line voltage in KV
            max_pole_to_pole_distance (float): Maximum pole to
                pole distance in meter
            power_factor (float): Power factor used to compute kva
            adjustment_factor (float): Adjustment factor for
                adjusting kva
            planned_avg_annual_growth (float): Planned average annual
                load growth rate in percentage
            actual_avg_annual_growth (float): Actual average annual load
                growth rate in percentage
            actual_years_in_operation (float): Actual years in operation
            planned_years_in_operation (float): Planned years in operation

        Raises:
            NegativeKVError: If `kv_ll` is negative
            ZeroKVError: If `kv_ll` is zero
            AdjustmentFactorNotInRangeError: If invalid adjustement
                factor is passed
            PowerFactorNotInRangeError: If power factor is not in valid range
            PoleToPoleDistanceNotInRange: If pole to pole distance
                passed in invalid
            PercentageNotInRangeError: If percentages passed are not valid
            OperationYearNotInRange: If operation year passed is invalid
        """

        self.max_pole_to_pole_distance = max_pole_to_pole_distance
        self.div_func = div_func

        self.kv_ll = kv_ll
        self.adjustment_factor = adjustment_factor
        self.power_factor = power_factor

        self.planned_avg_annual_growth = planned_avg_annual_growth
        self.actual_avg_annual_growth = actual_avg_annual_growth
        self.actual_years_in_operation = actual_years_in_operation
        self.planned_years_in_operation = planned_years_in_operation

        if self.kv_ll < 0:
            raise NegativeKVError(self.kv_ll)
        if self.kv_ll == 0:
            raise ZeroKVError()

        if (
            self.adjustment_factor < MIN_ADJUSTMENT_FACTOR
            or self.adjustment_factor > MAX_ADJUSTMENT_FACTOR
        ):
            raise AdjustmentFactorNotInRangeError(self.adjustment_factor)

        if (
            self.power_factor < MIN_POWER_FACTOR
            or self.power_factor > MAX_POWER_FACTOR
        ):
            raise PowerFactorNotInRangeError(self.power_factor)

        if (
            self.max_pole_to_pole_distance < MIN_POLE_TO_POLE_DISTANCE
            or self.max_pole_to_pole_distance > MAX_POLE_TO_POLE_DISTANCE
        ):
            raise PoleToPoleDistanceNotInRange(self.max_pole_to_pole_distance)

        if (
            self.planned_avg_annual_growth < MIN_PERCENTAGE
            or self.planned_avg_annual_growth > MAX_PERCENTAGE
        ):
            raise PercentageNotInRangeError(self.planned_avg_annual_growth)

        if (
            self.actual_avg_annual_growth < MIN_PERCENTAGE
            or self.actual_avg_annual_growth > MAX_PERCENTAGE
        ):
            raise PercentageNotInRangeError(self.actual_avg_annual_growth)

        if (
            self.actual_years_in_operation < MIN_YEAR_OPERATION
            or self.actual_years_in_operation > MAX_YEAR_OPERATION
        ):
            raise OperationYearNotInRange(self.actual_years_in_operation)

        if (
            self.planned_years_in_operation < MIN_YEAR_OPERATION
            or self.planned_years_in_operation > MAX_YEAR_OPERATION
        ):
            raise OperationYearNotInRange(self.planned_years_in_operation)

    def _compute_ampacity(
        self, non_coincident_peak: float, num_of_customers: int
    ) -> float:
        """Private method to compute ampacity.

        Args:
            non_coincident_peak (float): Non coincident peak consumption
            num_of_customers (int): Number of customers

        Returns:
            float: conductor ampacity
        """

        # Initial step is to compute maximum diversified demand
        div_factor = (
            self.div_func(num_of_customers) if num_of_customers > 1 else 1
        )
        max_diversified_demand = non_coincident_peak / div_factor
        max_diversified_kva = (
            max_diversified_demand * self.adjustment_factor / self.power_factor
        )
        max_diversified_ampacity = max_diversified_kva / (1.732 * self.kv_ll)

        original_max_diversified_ampacity = max_diversified_ampacity / math.pow(
            1 + self.actual_avg_annual_growth / 100,
            self.actual_years_in_operation,
        )
        conductor_ampacity = original_max_diversified_ampacity * math.pow(
            1 + self.planned_avg_annual_growth / 100,
            self.planned_years_in_operation,
        )
        return conductor_ampacity

    @abstractmethod
    def update_network_with_ampacity(self):
        """Abstract method for updating ampacity for all line sections."""
        pass


class PrimaryNetworkFromRoad(BaseNetworkBuilder):
    """Builds primary network from OpenStreet road data.

    Refer to base class for base attributes.

    Attributes:
        road_network (OpenStreetRoadNetwork): OpenStreetRoadNetwork instance
        trans_cust_mapper (dict): Mapping between `Transformer` object
            and list of `Load` objects
        node_append_str (Union[str, None]): Unique string to be
            appended to all primary nodes
        sliced_graph (nx.Graph): Sliced road network
        substation_node (str): Node representing substation
        substation_coords (Sequence): Actual substation coordinate
        retain_nodes (List[str]): List of primary nodes to be retained
    """

    def __init__(
        self,
        road_network: OpenStreetRoadNetwork,
        trans_cust_mapper: dict,
        substation_loc: tuple,
        div_func: Callable[[float], float],
        kv_ll: float,
        max_pole_to_pole_distance: float = 100,
        power_factor: float = 0.9,
        adjustment_factor: float = 1.2,
        planned_avg_annual_growth: float = 2,
        actual_avg_annual_growth: float = 4,
        actual_years_in_operation: float = 15,
        planned_years_in_operation: float = 10,
        node_append_str: Union[str, None] = None,
    ) -> None:
        """Constructor for `PrimaryNetworkFromRoad` class.

        Refer to base class for base class arguments.

        Args:
            road_network (OpenStreetRoadNetwork): OpenStreetRoadNetwork instance
            trans_cust_mapper (dict): Mapping between `Transformer` object
                and list of `Load` objects
            substation_loc (tuple): Tentative location for siting substation
                (longitude, latitude) pair
            node_append_str (Union[str, None]): Unique string to be
                appended to all primary nodes
        """

        super().__init__(
            div_func,
            kv_ll,
            max_pole_to_pole_distance,
            power_factor,
            adjustment_factor,
            planned_avg_annual_growth,
            actual_avg_annual_growth,
            actual_years_in_operation,
            planned_years_in_operation,
        )

        # Get the road network from openstreet data
        self.node_append_str = node_append_str
        self.road_network = road_network
        self.road_network.get_network(node_append_str)
        self.trans_cust_mapper = trans_cust_mapper

        # Get sliced graph
        self.sliced_graph = slice_up_network_edges(
            self.road_network.updated_network, self.max_pole_to_pole_distance
        )

        # Get substation node
        self.substation_node = list(
            get_nearest_points_in_the_network(
                self.sliced_graph, [substation_loc]
            )
        )[0]
        self.substation_coords = self.sliced_graph.nodes[self.substation_node][
            "pos"
        ]

        trans_location_to_retain = [
            (t.longitude, t.latitude) for t in self.trans_cust_mapper
        ]
        self.retain_nodes = get_nearest_points_in_the_network(
            self.sliced_graph, trans_location_to_retain + [substation_loc]
        )

    def get_primary_network(self) -> nx.Graph:
        """Algorithm to convert road network into
        distribution system primary network"""
        return ax.steinertree.steiner_tree(
            self.sliced_graph, list(self.retain_nodes.keys())
        )

    def get_sliced_graph(self) -> nx.Graph:
        """Return sliced graph"""
        return self.sliced_graph

    def get_network(self) -> nx.Graph:
        """Returns a primary network with ampacity data.

        Raises:
            AttributeDoesNotExistError: If `update_network_with_ampacity`
                is not called first, absence of `network` attribute

        Returns:
            nx.Graph: primary network with ampacity data
        """

        if hasattr(self, "network"):
            mapping_dict, relabel_rnodes = {}, {}
            for node, node_val in self.retain_nodes.items():
                node_new_name = "_".join(node.split("_")[:2]) + "_htnode"
                mapping_dict[node] = node_new_name
                relabel_rnodes[node_new_name] = node_val

            relable_snode = (
                "_".join(self.substation_node.split("_")[:2]) + "_ltnode"
            )
            mapping_dict[self.substation_node] = relable_snode
            relabel_rnodes[relable_snode] = self.retain_nodes[
                self.substation_node
            ]
            self.network = nx.relabel_nodes(self.network, mapping_dict)
            self.retain_nodes = relabel_rnodes

            return self.network
        else:
            raise AttributeDoesNotExistError(
                "Please call 'update_network_with_ampacity' \
                 method first before trying to access primary"
            )

    def get_trans_node_mapping(self) -> dict:
        """Returns transformer to primary node mapping"""
        return self.retain_nodes

    def get_longest_length_in_kvameter(self) -> float:
        """Returns longest length in kva meter"""
        return self.longest_length

    def update_network_with_ampacity(self) -> None:
        """Method to update all line sections with ampacity"""

        # Get primary network tree
        self.network = self.get_primary_network()

        # Create a directed graph by providing source node """
        dfs_tree = nx.dfs_tree(self.network, source=self.substation_node)

        # Mapping for transformer nodes """
        transformer_nodes = {}
        for node, node_dict in self.retain_nodes.items():
            for trans, cust_list in self.trans_cust_mapper.items():
                if (
                    trans.longitude == node_dict["centre"][0]
                    and trans.latitude == node_dict["centre"][1]
                ):
                    transformer_nodes[node] = cust_list

        for edge in dfs_tree.edges():

            # Compute distance from the source"""
            distance = nx.resistance_distance(
                self.network, self.substation_node, edge[1]
            )
            self.network[edge[0]][edge[1]]["distance"] = distance

            # Perform a depth first traversal to find all successor nodes"""
            dfs_successors = nx.dfs_successors(dfs_tree, source=edge[1])

            # Create a subgraph"""
            nodes_to_retain = [edge[1]]
            for _, v in dfs_successors.items():
                nodes_to_retain.extend(v)
            subgraph = self.network.subgraph(nodes_to_retain)

            # Let's compute maximum diversified
            # kva demand downward of this edge"""
            noncoincident_kws = 0
            num_of_customers = 0
            for node in subgraph.nodes():
                if node in transformer_nodes:
                    num_of_customers += len(transformer_nodes[node])
                    noncoincident_kws += sum(
                        l.kw for l in transformer_nodes[node]
                    )

            self.network[edge[0]][edge[1]]["ampacity"] = self._compute_ampacity(
                noncoincident_kws, num_of_customers
            )

        node_data_dict = {
            node[0]: node[1] for node in self.network.nodes.data()
        }
        bfs_tree = nx.bfs_tree(self.network, self.substation_node)
        for edge in bfs_tree.edges():
            bfs_tree[edge[0]][edge[1]]["cost"] = (
                get_distance(
                    node_data_dict[edge[0]]["pos"],
                    node_data_dict[edge[1]]["pos"],
                )
                * self.network[edge[0]][edge[1]]["ampacity"]
                * 1.732
                * self.kv_ll
            )
        self.longest_length = nx.dag_longest_path_length(
            bfs_tree, weight="cost"
        )
