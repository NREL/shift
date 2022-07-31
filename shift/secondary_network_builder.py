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

""" This module contains classes for managing
creation of secondary network sections. """

# Manage python imports
from typing import List, Union, Callable

import networkx as nx

from shift.load import Load
from shift.transformer import Transformer
from shift.utils import (
    triangulate_using_mesh,
    set_node_edge_type,
    get_nearest_points_in_the_network,
    get_distance,
)
from shift.primary_network_builder import BaseNetworkBuilder
from shift.enums import ConductorType, NumPhase, Phase
from shift.line_section import Line

# pylint: disable=redefined-builtin
from shift.exceptions import (
    CustomerInvalidPhase,
    PhaseMismatchError,
    IncompleteGeometryConfigurationDict,
    NotImplementedError,
)
from shift.primary_network_builder import (
    BaseSectionsBuilder,
    geometry_based_line_section_builder,
)


class SecondarySectionsBuilder(BaseSectionsBuilder):
    """Class handling generation of secondary line sections.

    Refer to base class for attributes present in base class

    Attributes:
        lateral_configuration (dict): Drop line configuration data
        lateral_material (str): Conductor material for drop line
    """

    def __init__(
        self,
        secondary_network: nx.Graph,
        conductor_type: ConductorType,
        configuration: dict,
        lateral_configuration: dict,
        num_phase: NumPhase,
        phase: Phase,
        neutral_present: True,
        material: str = "all",
        lateral_material: str = "all",
    ) -> None:
        """Constructor for SecondarySectionsBuilder class.

        Refer to base class arguments.

        Args:
            lateral_configuration (dict): Drop line configuration data
            lateral_material (str): Conductor material for drop line
        """

        super().__init__(
            secondary_network,
            conductor_type,
            configuration,
            num_phase,
            phase,
            neutral_present,
            material,
        )
        self.lateral_material = lateral_material
        self.lateral_configuration = lateral_configuration

    def generate_secondary_line_sections(
        self, k_drop: float, kv_base: float
    ) -> List[Line]:
        """Method for creating secondary line sections.

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

            # Find edge that connects load and this should be cable
            if (
                "load" in self.network.nodes[edge[0]]
                or "load" in self.network.nodes[edge[1]]
            ):

                load_node = 0 if "load" in self.network.nodes[edge[0]] else 1
                load_obj = self.network.nodes[edge[load_node]]["object"]

                # pylint: disable-next=line-too-long
                # fromnode_phase = load_obj.phase if load_node == 0 else self.phase
                # tonode_phase = load_obj.phase if load_node == 1 else self.phase

                if load_obj.num_phase.value > self.num_phase.value:
                    raise CustomerInvalidPhase(
                        load_obj.num_phase, self.num_phase
                    )

                # Let's check for phase mismatch if any
                if self.num_phase.value == load_obj.num_phase.value:
                    if self.phase != load_obj.phase:
                        raise PhaseMismatchError(load_obj.phase, self.phase)

                if load_obj.num_phase not in self.lateral_configuration:
                    raise IncompleteGeometryConfigurationDict(
                        load_obj.num_phase, self.lateral_configuration
                    )

                line_section = geometry_based_line_section_builder(
                    edge[0],
                    edge[1],
                    load_obj.num_phase,
                    load_obj.phase,
                    load_obj.phase,
                    get_distance(
                        node_data_dict[edge[0]]["pos"],
                        node_data_dict[edge[1]]["pos"],
                    ),
                    "m",
                    edge_data["ampacity"],
                    self.catalog_dict[ConductorType.UNDERGROUND_CONCENTRIC],
                    self.neutral_present,
                    ConductorType.UNDERGROUND_CONCENTRIC,
                    self.lateral_configuration[load_obj.num_phase],
                    k_drop,
                    kv_base,
                    self.lateral_material,
                )

            else:
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


class SecondaryNetworkBuilder(BaseNetworkBuilder):
    """Builds secondary network.

    Refer to base class for base attributes.

    Attributes:
        transformer (Transformer): `Transformer` instance
        load_to_node_mapping (dict): Mapping between load
            object and  secondary node
        customer_to_node_mapping (dict): Mapping between
            load name and secondary node
        network (nx.Graph): Seondary network
        points (dict): Mapping between load and coordinates
        source_node (str): Source node for the secondary network
        tr_lt_node (str): LT node of the transformer
    """

    def __init__(
        self,
        load_list: List[Load],
        transformer: Transformer,
        div_func: Callable[[float], float],
        kv_ll: float,
        node_append_str: str,
        forbidden_areas: Union[str, None] = None,
        max_pole_to_pole_distance: float = 100,
        power_factor: float = 0.9,
        adjustment_factor: float = 1.2,
        planned_avg_annual_growth: float = 2,
        actual_avg_annual_growth: float = 4,
        actual_years_in_operation: float = 15,
        planned_years_in_operation: float = 10,
    ):
        """Constructor for SecondaryNetworkBuilder class.

        Args:
            load_list (List[Load]): List of `Load` instances
            transformer (Transformer): `Transformer` instance
            node_append_str (str): Unique string to be appended
                to all primary nodes
            forbidden_areas (Union[str, None]): Path to .shp
                file containing forbidden polygons

        Raises:
            NotImplementedError: If transformer has 0 loads
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
        self.transformer = transformer
        self.load_to_node_mapping = {}

        load_locations = [[l.longitude, l.latitude] for l in load_list]

        if len(load_locations) > 0:

            if len(load_locations) == 1:

                self.network = nx.Graph()

                # pylint: disable-next=line-too-long
                load_node = f"{load_locations[0][0]}_{load_locations[0][1]}_{node_append_str}_node"
                self.network.add_node(
                    load_node,
                    pos=(load_locations[0][0], load_locations[0][1]),
                )
                customer_node = (
                    f"{load_locations[0][0]}_{load_locations[0][1]}_customer"
                )
                self.customer_to_node_mapping = {customer_node: load_node}
                self.points = {
                    key: val["pos"]
                    for key, val in dict(self.network.nodes(data=True)).items()
                }

            else:
                # We use meshed approach to come up with network graph
                (
                    self.network,
                    self.points,
                    self.customer_to_node_mapping,
                ) = triangulate_using_mesh(
                    load_locations,
                    forbidden_areas=forbidden_areas,
                    node_append_str=node_append_str,
                )

            # Unfreeze the network if already frozen
            if nx.is_frozen(self.network):
                self.network = nx.Graph(self.network)

            self.source_node = list(
                get_nearest_points_in_the_network(
                    self.network,
                    [(self.transformer.longitude, self.transformer.latitude)],
                )
            )[0]

            # Connect the customers as well

            for load in load_list:
                to_node = self.customer_to_node_mapping[
                    f"{load.longitude}_{load.latitude}_customer"
                ]
                self.network.add_node(
                    load.name,
                    pos=(load.longitude, load.latitude),
                    object=load,
                    load=True,
                )
                self.network.add_edge(load.name, to_node, load_present=True)
                self.load_to_node_mapping[load.name] = to_node

            # pylint: disable-next=line-too-long
            self.tr_lt_node = f"{self.transformer.longitude}_{self.transformer.latitude}_ltnode"
            self.network.add_node(
                self.tr_lt_node,
                pos=(self.transformer.longitude, self.transformer.latitude),
            )
            self.network.add_edge(self.tr_lt_node, self.source_node)

            self.network = set_node_edge_type(self.network)
        else:
            raise NotImplementedError("Transformers can not have 0 loads")

    def get_load_to_node_mapping(self) -> dict:
        """Returns load to node mapping."""
        return self.load_to_node_mapping

    def get_network(self) -> nx.Graph:
        """Returns secondary network."""
        return self.network

    def get_longest_length_in_kvameter(self):
        """Returns longest length in kva meter"""
        return self.longest_length

    def update_network_with_ampacity(self):
        """Method to update all line sections with ampacity"""

        # Create a directed graph by providing source node
        dfs_tree = nx.dfs_tree(self.network, source=self.source_node)

        # Perform a depth first traversal to find all successor nodes"""
        x, y = [], []
        for edge in dfs_tree.edges():

            # Compute distance from the source"""
            distance = nx.resistance_distance(
                self.network, self.source_node, edge[1]
            )
            self.network[edge[0]][edge[1]]["distance"] = distance

            # Perform a depth first traversal to find all successor nodes"""
            dfs_successors = nx.dfs_successors(dfs_tree, source=edge[1])

            # Create a subgraph"""
            nodes_to_retain = [edge[1]]
            for _, v in dfs_successors.items():
                nodes_to_retain.extend(v)
            subgraph = self.network.subgraph(nodes_to_retain)

            # Let's compute maximum diversified kva
            # demand downward of this edge"""
            noncoincident_kws = 0
            num_of_customers = 0
            for node in subgraph.nodes():
                if "load" in subgraph.nodes[node]:
                    num_of_customers += 1
                    noncoincident_kws += subgraph.nodes[node]["object"].kw

            self.network[edge[0]][edge[1]]["ampacity"] = self._compute_ampacity(
                noncoincident_kws, num_of_customers
            )
            x.append(distance)
            y.append(self.network[edge[0]][edge[1]]["ampacity"])

        node_data_dict = {
            node[0]: node[1] for node in self.network.nodes.data()
        }
        bfs_tree = nx.bfs_tree(self.network, self.source_node)
        for edge in bfs_tree.edges():
            try:
                bfs_tree[edge[0]][edge[1]]["cost"] = (
                    get_distance(
                        node_data_dict[edge[0]]["pos"],
                        node_data_dict[edge[1]]["pos"],
                    )
                    * self.network[edge[0]][edge[1]]["ampacity"]
                    * 1.732
                    * self.kv_ll
                )
            # pylint: disable=broad-except
            except Exception as e:
                print(e)
                print("help")
        self.longest_length = nx.dag_longest_path_length(
            bfs_tree, weight="cost"
        )
