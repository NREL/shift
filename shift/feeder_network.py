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

""" This module manages connecting various power system
components to build a network. """

from abc import ABC, abstractmethod
from typing import List

import networkx as nx

from shift.load import Load
from shift.enums import NetworkAsset
from shift.transformer import Transformer
from shift.line_section import Line


def update_transformer_locations(
    retain_nodes: List[str],
    transformers_cust_mapper: dict,
    primary_lines: List[Line],
) -> dict:
    """Updated the location of transformers by connecting it
    to nearest primary node.

    Args:
        retain_nodes (List[str]): list of nodes to be retained
        transformers_cust_mapper (dict): A dictionary with key r
            epresenting `Transformer` object values
            list of `Load` objects
        primary_lines (List[Line]): List of line objects
            representing primary line sections.

    Returns:
        dict: New transformer to customer or loads mapping
    """
    rnode_to_trans_mapping = {}
    for rnode, rdict in retain_nodes.items():
        for trans, cust_list in transformers_cust_mapper.items():
            if rdict["centre"] == (trans.longitude, trans.latitude):
                rnode_to_trans_mapping[rnode] = {
                    "trans": trans,
                    "longitude": rdict["longitude"],
                    "latitude": rdict["latitude"],
                    "cust_list": cust_list,
                }
    new_transformers_cust_mapper = {}
    for edge in primary_lines:
        for node in [edge.fromnode, edge.tonode]:
            if node in rnode_to_trans_mapping:
                trans_obj = rnode_to_trans_mapping[node]["trans"]
                trans_obj.longitude = rnode_to_trans_mapping[node]["longitude"]
                trans_obj.latitude = rnode_to_trans_mapping[node]["latitude"]
                new_transformers_cust_mapper[
                    trans_obj
                ] = rnode_to_trans_mapping[node]["cust_list"]

    return new_transformers_cust_mapper


class TwoLayerDistributionNetworkBuilder(ABC):
    """Interface to build two layer (low tension +
    high tension) distribution network"""

    @abstractmethod
    def add_load_nodes(self, loads: List[Load]) -> None:
        """Abstract method to add customer nodes
        to the distribution network"""
        pass

    @abstractmethod
    def add_distribution_transformers(
        self, transformers: List[Transformer]
    ) -> None:
        """Abstract method to add distribution transformer nodes"""
        pass

    @abstractmethod
    def add_low_tension_network(self, edges: List[Line]) -> None:
        """Abstract method to add low tension network"""
        pass

    @abstractmethod
    def add_high_tension_network(self, edges: List[Line]) -> None:
        """Abstract method to add high tension network"""
        pass

    @abstractmethod
    def add_substation(self):
        """Abstract method to add substation"""
        pass


class TwoLayerNetworkBuilderDirector:
    """Builder for creating two layer distribution network.

    Attributes:
        builder (TwoLayerDistributionNetworkBuilder): Instance
            of `TwoLayerDistributionNetworkBuilder` class
    """

    def __init__(
        self,
        loads: List[Load],
        transformers: List[Transformer],
        primary_edges: List[Line],
        secondary_edges: List[Line],
        builder: TwoLayerDistributionNetworkBuilder,
    ) -> None:
        """Constructor method for TwoLayerNetworkBuilderDirector class.

        Args:
            loads (List[Load]): List of `Load` objects
            transformers (List[Transformer]): List of `Transformer` objects
            primary_edges (List[Line]): List of `Line` objects
                representing primary sections
            secondary_edges (List[Line]): List of `Line` objects representing
                secondary sections
            builder (TwoLayerDistributionNetworkBuilder): Instance of builder
                type `TwoLayerDistributionNetworkBuilder`
        """

        self.builder = builder
        self.builder.add_load_nodes(loads)
        self.builder.add_distribution_transformers(transformers)
        self.builder.add_high_tension_network(primary_edges)
        self.builder.add_low_tension_network(secondary_edges)

    def get_network(self):
        """Returns a distribution network"""
        return self.builder.feeder


class SimpleTwoLayerDistributionNetworkBuilder(
    TwoLayerDistributionNetworkBuilder
):
    """Class for creating distribution assets for
    developing two layer distribution network.

    Attributes:
        feeder (nx.Graph): Instance of networkx graph
    """

    def __init__(self) -> None:
        """Constructor for SimpleTwoLayerDistributionNetworkBuilder class"""

        self.feeder = nx.Graph()

    def add_load_nodes(self, loads: List[Load]) -> None:
        """Add load nodes to the network.

        Args:
            loads (List[Load]): List of `Load` objects
        """

        # Loop over all the load and add to the network
        for load in loads:

            self.feeder.add_node(
                load.name,
                pos=(load.longitude, load.latitude),
                type=NetworkAsset.LOAD,
                data=load.__dict__,
                object=load,
            )

    def add_distribution_transformers(
        self, transformers: List[Transformer]
    ) -> None:
        """Add transformer nodes to the network.

        Args:
            transformers (List[Transformer]): List of `Transformer` objects
        """
        for xfmr in transformers:

            self.feeder.add_node(
                xfmr.name,
                pos=(xfmr.longitude, xfmr.latitude),
                type=NetworkAsset.DISTXFMR,
                data=xfmr.__dict__,
                object=xfmr,
            )

    def add_low_tension_network(self, edges: List[Line]) -> None:
        """Add low tension line segments to the network.

        Args:
            edges (List[Line]): List of `Line` objects representing
                secondary line segments
        """

        for edge in edges:

            if not self.feeder.has_node(edge.fromnode):
                self.feeder.add_node(
                    edge.fromnode,
                    pos=(
                        float(edge.fromnode.split("_")[0]),
                        float(edge.fromnode.split("_")[1]),
                    ),
                    type=NetworkAsset.LTNODE,
                    data={},
                )
            if not self.feeder.has_node(edge.tonode):
                self.feeder.add_node(
                    edge.tonode,
                    pos=(
                        float(edge.tonode.split("_")[0]),
                        float(edge.tonode.split("_")[1]),
                    ),
                    type=NetworkAsset.LTNODE,
                    data={},
                )
            self.feeder.add_edge(
                edge.fromnode,
                edge.tonode,
                type=NetworkAsset.LTLINE,
                data={},
                object=edge,
            )

    def add_high_tension_network(self, edges: List[Line]) -> None:
        """Add high tension line segments to the network.

        Args:
            edges (List[Line]): List of `Line` objects representing
                primary line segments
        """
        for edge in edges:
            self.feeder.add_node(
                edge.fromnode,
                pos=(
                    float(edge.fromnode.split("_")[0]),
                    float(edge.fromnode.split("_")[1]),
                ),
                type=NetworkAsset.HTNODE,
                data={},
            )
            self.feeder.add_node(
                edge.tonode,
                pos=(
                    float(edge.tonode.split("_")[0]),
                    float(edge.tonode.split("_")[1]),
                ),
                type=NetworkAsset.HTNODE,
                data={},
            )
            self.feeder.add_edge(
                edge.fromnode,
                edge.tonode,
                type=NetworkAsset.HTLINE,
                data={},
                object=edge,
            )

        # Make correction to transformer node:
        # Pull the transformer node to network node and convert to edge

    def add_substation(self):
        """Add substation"""
        pass
