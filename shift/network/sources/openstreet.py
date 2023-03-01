from abc import ABC
from typing import List, Union

import osmnx as ox
import networkx as nx
import shapely

from shift.exceptions import AttributeDoesNotExistError
from shift.utility.model import Location


def _prune_graph(graph: nx.Graph) -> nx.Graph:

    network = nx.minimum_spanning_tree(graph.to_undirected())

    # if node_append_str:
    #     network = nx.relabel_nodes(
    #         network,
    #         {n: str(n) + node_append_str for n in network.nodes()},
    #     )

    updated_network = nx.Graph()
    for node in network.nodes.data():
        
        # x is longitude and y is latitude
        updated_network.add_node(
            node[0],
            # pos=(node[1]["x"], node[1]["y"]),
            # type="node",
            loc=Location(latitude=node[1]["y"], longitude=node[1]["x"]),
        )
    
    for edge in network.edges():
        updated_network.add_edge(edge[0], edge[1]) # type="edge"

    return updated_network

def get_road_network_from_point(
        point: tuple, max_dist: float = 1000,
        dist_type: str = "bbox", network_type: str = "drive",
) -> nx.Graph:
    
    return _prune_graph(ox.graph.graph_from_point(
            point,
            dist=max_dist,
            dist_type=dist_type,
            network_type=network_type,
        ))


def get_road_network_from_place(
        place: str, max_dist: float = 1000,
        dist_type: str = "bbox", network_type: str = "drive",
) -> nx.Graph:
    
    return _prune_graph(ox.graph.graph_from_address(
            place,
            dist=max_dist,
            dist_type=dist_type,
            network_type=network_type,
        ))

def get_road_network_from_polygon(
        polygon: List[list], custom_filter: str = '["highway"]',
        network_type: str = "drive"
) -> nx.Graph:
    
    return _prune_graph(ox.graph.graph_from_polygon(
            shapely.geometry.Polygon(polygon), 
            network_type=network_type
            # custom_filter=custom_filter
        ))

