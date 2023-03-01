# third-party imports 
import networkx as nx
import numpy as np 


# internal imports
from shift.network.utility.helpers import get_distance
from shift.utility.model import Location

def slice_up_network_edges(graph: nx.Graph, slice_in_meter: float) -> nx.Graph:

    """Creates a new graph with edges sliced by given distance in meter.

    Args:
        graph (nx.Graph): Networkx graph instance
        slice_in_meter (float): Maximum length of edge in meter for
            use in slicing

    Returns:
        nx.Graph: Sliced network
    """

    sliced_graph = nx.Graph()
    graph_nodes = {x[0]: x[1] for x in graph.nodes.data()}

    for edge in graph.edges():
        
        x1, y1 = (graph_nodes[edge[0]]['loc'].longitude, graph_nodes[edge[0]]['loc'].latitude)
        x2, y2 = (graph_nodes[edge[1]]['loc'].longitude, graph_nodes[edge[1]]['loc'].latitude)

        edge_length = get_distance((x1, y1),(x2, y2))
        
        edge_slices = [
            x / edge_length for x in np.arange(0, edge_length, slice_in_meter)
        ] + [1]

    
        sliced_nodes = []
        for slice_ in edge_slices:
            new_x, new_y = x1 + (x2 - x1) * slice_, y1 + (y2 - y1) * slice_
            sliced_graph.add_node(
                f"{new_x}_{new_y}_node",
                type="node",
                loc=Location(longitude=new_x, latitude=new_y),
            )
            sliced_nodes.append(f"{new_x}_{new_y}_node")

        for i in range(len(sliced_nodes) - 1):
            sliced_graph.add_edge(
                sliced_nodes[i], sliced_nodes[i + 1]
            )

    return sliced_graph
