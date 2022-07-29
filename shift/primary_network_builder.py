""" Let's generate primary network from RoadNetwork """

from graph import OpenStreetRoadNetwork
from constants import MIN_POLE_TO_POLE_DISTANCE, MAX_POLE_TO_POLE_DISTANCE
from exceptions import (
    PoleToPoleDistanceNotInRange,
    IncompleteGeometryConfigurationDict,
)
from utils import slice_up_network_edges, get_nearest_points_in_the_network
from networkx.algorithms import approximation as ax
import networkx as nx
from constants import (
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
from exceptions import (
    AdjustmentFactorNotInRangeError,
    PowerFactorNotInRangeError,
    NegativeKVError,
    ZeroKVError,
    AttributeDoesNotExistError,
    PercentageNotInRangeError,
    OperationYearNotInRange,
    EmptyCatalog,
    ConductorNotFoundForKdrop,
    CatalogNotFoundError,
)
import math
from enums import ConductorType, NumPhase, Phase
import pandas as pd
from utils import df_validator, get_distance
from line_section import (
    GeometryBasedLine,
    OverheadLineGeometry,
    OverheadLinewithNeutralGeometry,
    LineGeometryConfiguration,
    UndergroundLineGeometry,
    Wire,
    Cable,
)
import uuid
import numpy as np
import copy
from abc import ABC, abstractmethod
import itertools


def choose_conductor(
    catalog,
    ampacity,
    k_drop,
    geometry_configuration,
    num_of_phase,
    kv_base,
    pf=0.9,
):

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

        # print('k_drop : ', k_drop, k_drop_computed, record['name'], record['ampacity'])
        if k_drop_computed <= k_drop:
            return record

    # print(k_drop_computed, k_drop, ampacity, record)
    # raise ConductorNotFoundForKdrop(k_drop)
    return record


def convert_oh_cond_info_to_wire(data):

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


def convert_ug_cond_info_to_cable(data):

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
):

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
            # catalog.loc[catalog[catalog['ampacity']>ampacity]['ampacity'].idxmin()].to_dict()
            line_geometry.phase_wire = convert_oh_cond_info_to_wire(
                phase_cond_dict
            )

            # Assuming neutral conductor would be one third of phase conductor ampacity for multi phase else same as phase conductor
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
    def __init__(
        self,
        network,
        conductor_type: ConductorType,
        configuration: dict,
        num_phase: NumPhase,
        phase: Phase,
        neutral_present: False,
        material: str = "all",
    ):

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
    def generate_primary_line_sections(self, k_drop, kv_base):

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
    def __init__(
        self,
        div_func,
        kv_ll: float,
        max_pole_to_pole_distance: float = 100,
        power_factor: float = 0.9,
        adjustment_factor: float = 1.2,
        planned_avg_annual_growth: float = 2,
        actual_avg_annual_growth: float = 4,
        actual_years_in_operation: float = 15,
        planned_years_in_operation: float = 10,
    ):

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

    def compute_ampacity(
        self, non_coincident_peak: float, num_of_customers: int
    ):

        """Initial step is to compute maximum diversified demand"""
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
        pass


class PrimaryNetworkFromRoad(BaseNetworkBuilder):
    def __init__(
        self,
        road_network: OpenStreetRoadNetwork,
        trans_cust_mapper: dict,
        substation_loc: tuple,
        div_func,
        kv_ll: float,
        max_pole_to_pole_distance: float = 100,
        power_factor: float = 0.9,
        adjustment_factor: float = 1.2,
        planned_avg_annual_growth: float = 2,
        actual_avg_annual_growth: float = 4,
        actual_years_in_operation: float = 15,
        planned_years_in_operation: float = 10,
        node_append_str: str = None,
    ):

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

        """ Get the road network from openstreet data"""
        self.node_append_str = node_append_str
        self.road_network = road_network
        self.road_network.get_network(node_append_str)
        self.trans_cust_mapper = trans_cust_mapper

        """ Get sliced graph"""
        self.sliced_graph = slice_up_network_edges(
            self.road_network.updated_network, self.max_pole_to_pole_distance
        )

        """ Get substation node """
        self.substation_node = [
            n
            for n in get_nearest_points_in_the_network(
                self.sliced_graph, [substation_loc]
            )
        ][0]
        self.substation_coords = self.sliced_graph.nodes[self.substation_node][
            "pos"
        ]

        trans_location_to_retain = [
            (t.longitude, t.latitude) for t in self.trans_cust_mapper
        ]
        self.retain_nodes = get_nearest_points_in_the_network(
            self.sliced_graph, trans_location_to_retain + [substation_loc]
        )

    def get_primary_network(self):

        """Alogorithm to convert road network into distribution system primary network"""
        return ax.steinertree.steiner_tree(
            self.sliced_graph, list(self.retain_nodes.keys())
        )

    def get_sliced_graph(self):

        """Return sliced graph"""
        return self.sliced_graph

    def get_network(self):
        """Returns a primary network with ampacity data"""

        if hasattr(self, "network"):
            mapping_dict, relabel_rnodes = {}, {}
            for node in self.retain_nodes:
                node_new_name = "_".join(node.split("_")[:2]) + "_htnode"
                mapping_dict[node] = node_new_name
                relabel_rnodes[node_new_name] = self.retain_nodes[node]

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

    def get_trans_node_mapping(self):
        return self.retain_nodes

    def get_longest_length_in_kvameter(self):
        return self.longest_length

    def update_network_with_ampacity(self):

        """Get primary network tree"""
        self.network = self.get_primary_network()

        """ Create a directed graph by providing source node """
        dfs_tree = nx.dfs_tree(self.network, source=self.substation_node)

        """ Mapping for transformer nodes """
        transformer_nodes = {}
        for node, node_dict in self.retain_nodes.items():
            for trans, cust_list in self.trans_cust_mapper.items():
                if (
                    trans.longitude == node_dict["centre"][0]
                    and trans.latitude == node_dict["centre"][1]
                ):
                    transformer_nodes[node] = cust_list

        for edge in dfs_tree.edges():

            """Compute distance from the source"""
            distance = nx.resistance_distance(
                self.network, self.substation_node, edge[1]
            )
            self.network[edge[0]][edge[1]]["distance"] = distance

            """ Perform a depth first traversal to find all successor nodes"""
            dfs_successors = nx.dfs_successors(dfs_tree, source=edge[1])

            """ Create a subgraph"""
            nodes_to_retain = [edge[1]]
            for k, v in dfs_successors.items():
                nodes_to_retain.extend(v)
            subgraph = self.network.subgraph(nodes_to_retain)

            """ Let's compute maximum diversified kva demand downward of this edge"""
            noncoincident_kws = 0
            num_of_customers = 0
            for node in subgraph.nodes():
                if node in transformer_nodes:
                    num_of_customers += len(transformer_nodes[node])
                    noncoincident_kws += sum(
                        [l.kw for l in transformer_nodes[node]]
                    )

            self.network[edge[0]][edge[1]]["ampacity"] = self.compute_ampacity(
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
