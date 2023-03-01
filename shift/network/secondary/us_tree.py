
# standard imports
from typing import List

# third-party imports
import networkx as nx

# internal imports
from shift.utility.model import Location, NumPhase
from shift.parcels.model import Building
from shift.network.utility.slice_graph import slice_up_network_edges
from shift.network.utility.helpers import get_nearest_nodes_in_the_network
from networkx.algorithms import approximation as ax


def get_polygon_from_locations(
    locations: List[Location]
):

    longitudes = [loc.longitude for loc in locations]
    latitudes = [loc.latitude for loc in locations]

    north_west = (min(longitudes), max(latitudes))
    north_east = (max(longitudes), max(latitudes))
    south_west = (min(longitudes), min(latitudes))
    south_east = (max(longitudes), min(latitudes))

    return [north_west, north_east, south_east, south_west, north_west]


# bounding_polygon = _get_polygon_from_locations(
#         [Location(latitude=b.latitude, longitude=b.longitude) \
#          for b in buildings]
#     )

def secondary_backbone(
    buildings: List[Building],
    road_graph: nx.Graph,
    pole_to_pole_meter: 20
):

    road_network = slice_up_network_edges(road_graph, pole_to_pole_meter)
    nearest_nodes = get_nearest_nodes_in_the_network(
        road_network, [Location(longitude=b.longitude, latitude=b.latitude) 
                       for b in buildings]
    )
    graph_mst = ax.steinertree.steiner_tree(road_network, nearest_nodes)

    node_data = { node[0]: node[1] for node in road_network.nodes.data() }
    
    for edge in graph_mst.edges:
        graph_mst[edge[0]][edge[1]]['numphase'] = NumPhase.three

    for node in graph_mst.nodes:
        graph_mst.nodes[node]['data'] = node_data[node]

    return graph_mst