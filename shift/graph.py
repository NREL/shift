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

""" This module manages graph network representing roads from openstreet data.

Examples:

    >>> from shift.graph import RoadNetworkFromPlace
    >>> graph = RoadNetworkFromPlace('chennai, india')
    >>> graph.get_network()
"""

from abc import ABC
from typing import List, Union

import osmnx as ox
import networkx as nx
import shapely

from shift.exceptions import AttributeDoesNotExistError


class OpenStreetRoadNetwork(ABC):
    """Interface for getting road network from OpenStreet data

    Attributes:
        updated_network (nx.Graph): Graph of road network with udpated metadata

    Raises:
        AttributeDoesNotExistError: If `graph` attribute does not already exist.
    """

    def get_network(self, node_append_str=Union[str, None]) -> nx.Graph:
        """Returns a minimum spanning tree with updated metadata.

        Args:
            node_append_str (Union[str, None]): String to append in the
                name of all nodes
        """

        if hasattr(self, "graph"):
            # Converting diected graph to undirected graph
            network = self.graph.to_undirected()

            # Find a minimum spanning tree of the network
            network = nx.minimum_spanning_tree(network)

            if node_append_str:
                network = nx.relabel_nodes(
                    network,
                    {n: str(n) + node_append_str for n in network.nodes()},
                )

            self.updated_network = nx.Graph()
            for node in network.nodes.data():
                # x is longitude and y is latitude
                self.updated_network.add_node(
                    node[0],
                    pos=(node[1]["x"], node[1]["y"]),
                    type="node",
                    data=node[1],
                )
            for edge in network.edges():
                self.updated_network.add_edge(edge[0], edge[1], type="edge")

            return self.updated_network
        else:
            raise AttributeDoesNotExistError(
                "'graph' attribute does not exist yet \
                for OpenStreet type road netwwork!"
            )


class RoadNetworkFromPoint(OpenStreetRoadNetwork):
    """Getting road network from single point within bounding box.

    Attributes:
        point (tuple): (longitude, latitude) pair representing
            point location
        max_dist (float): Distance to be used to create bounding
            box around a point
        dist_type (str): Type of region to be created around the point
        network_type (str): Type of network to be retrived from
            openstreet data
    """

    def __init__(
        self,
        point: tuple,
        max_dist: float = 1000,
        dist_type: str = "bbox",
        network_type: str = "drive",
    ) -> None:
        """Constructor for `RoadNetworkFromPoint` class.

        Args:
            point (tuple): (longitude, latitude) pair representing
                point location
            max_dist (float): Distance to be used to create
                bounding box around a point
            dist_type (str): Type of region to be created
                around the point
            network_type (str): Type of network to be retrived
                from openstreet data
        """

        # e.g. (13.242134, 80.275948)
        self.point = point
        self.max_dist = max_dist
        self.dist_type = dist_type
        self.network_type = network_type

    def get_network(self, node_append_str: Union[str, None] = None) -> nx.Graph:
        """Refer to base class for more details."""
        self.graph = ox.graph.graph_from_point(
            self.point,
            dist=self.max_dist,
            dist_type=self.dist_type,
            network_type=self.network_type,
        )
        super().get_network(node_append_str)


class RoadNetworkFromPlace(OpenStreetRoadNetwork):
    """Getting road network from a place address within bounding box.

    Attributes:
        place (str): string representing location
        max_dist (float): Distance to be used to create
            bounding box around a point
        dist_type (str): Type of region to be
            created around the point
        network_type (str): Type of network to be
            retrived from openstreet data
    """

    def __init__(
        self,
        place: str,
        max_dist: float = 1000,
        dist_type: str = "bbox",
        network_type: str = "drive",
    ) -> None:
        """Constructor for `RoadNetworkFromPlace` class.

        Args:
            place (str): string representing location
            max_dist (float): Distance to be used to create
                bounding box around a point
            dist_type (str): Type of region to be created around the point
            network_type (str): Type of network to be retrived
                from openstreet data
        """
        # e.g. Chennai, India
        self.place = place
        self.max_dist = max_dist
        self.dist_type = dist_type
        self.network_type = network_type

    def get_network(self, node_append_str: Union[str, None] = None) -> nx.Graph:
        """Refer to base class for more details."""
        self.graph = ox.graph.graph_from_address(
            self.place,
            dist=self.max_dist,
            dist_type=self.dist_type,
            network_type=self.network_type,
        )
        super().get_network(node_append_str)


class RoadNetworkFromPolygon(OpenStreetRoadNetwork):
    """Getting road network from a given polygon.

    Attributes:
        polygon (List[list]): List of (lon, lat) pairs
        custom_filter (str): Valid osmnx type customer filter to be applied
    """

    def __init__(
        self, polygon: List[list], custom_filter: str = '["highway"]'
    ) -> None:
        """Constructor for `RoadNetworkFromPolygon` class.

        Args:
            polygon (List[list]): List of (lon, lat) pairs
            custom_filter (str): Valid osmnx type customer filter to be applied
        """

        # e.g. [[13.242134, 80.275948]]
        self.polygon = polygon
        self.custom_filter = custom_filter

    def get_network(self, node_append_str: Union[str, None] = None) -> nx.Graph:
        """Refer to base class for more details."""

        polygon = shapely.geometry.Polygon(self.polygon)
        self.graph = ox.graph.graph_from_polygon(
            polygon, custom_filter=self.custom_filter
        )
        super().get_network(node_append_str)
