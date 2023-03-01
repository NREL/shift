# standard imports
from typing import List 

# third party imports
import networkx as nx

# internal imports
from shift.network.utility.slice_graph import slice_up_network_edges
from shift.network.utility.helpers import get_nearest_nodes_in_the_network
from shift.utility.model import Location, NumPhase
from networkx.algorithms import approximation as ax
from shift.transformers.model import Transformer


def get_primary_network(
    road_graph: nx.Graph,
    transformers: List[Transformer],
    pole_to_pole_meter: int   
):

    road_network = slice_up_network_edges(road_graph, pole_to_pole_meter)

    nearest_nodes = get_nearest_nodes_in_the_network(
        road_network, [Location(longitude=tr.longitude, latitude=tr.latitude) 
                       for tr in transformers]
    )
    graph_mst = ax.steinertree.steiner_tree(road_network, nearest_nodes)
    
    node_data = { node[0]: node[1] for node in road_network.nodes.data() }
    
    for edge in graph_mst.edges:
        graph_mst[edge[0]][edge[1]]['numphase'] = NumPhase.three

    for node in graph_mst.nodes:
        graph_mst.nodes[node]['data'] = node_data[node]

    return graph_mst