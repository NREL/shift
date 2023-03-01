
# standard imports
from typing import List 

# third-party imports
import geopy.distance
import networkx as nx

# internal imports
from shift.utility.model import Location

def get_distance(
    point1: List[float], point2: List[float], latlon=False
) -> float:
    """Returns distance between two geopoints in meter assuming
        eliposoidal earth model.

    Args:
        point1 (List[float]): location coordinate for point 1
        point2 (List[float]): location coordinate for point 2
        latlon (bool): Specfies that latitude is first and
            longitude is second if true

    Returns:
        float: distance in meter
    """

    # Assuming point1 and point2 are tuples with
    # first element representing longitude and
    # second element representing latitude

    # Geopy however requires (lat, lon) pair
    if not latlon:
        return (
            geopy.distance.distance(
                (point1[1], point1[0]), (point2[1], point2[0])
            ).km
            * 1000
        )
    else:
        return geopy.distance.distance(point1, point2).km * 1000
    


def get_nearest_nodes_in_the_network(
    graph: nx.Graph, points: List[Location]
) -> dict:
    """Retrieve nearest node from the graph for given points

    Args:
        graph (nx.Graph): Networkx graph instance
        points (List[Location]): List of location objects for which nearest
            nodes are to be found

    Todo:
        * Fix the issue if returned nodes are same for two points.

    Returns:
        dict: mapping between nearest node and point

    """

    nearest_points = {}
    graph_node_data = { node[0]: node[1] for node in graph.nodes.data() }

    for point in points:
        
        min_distance, nearest_node = None, None
        for node, data in graph_node_data.items():
            distance =  (point.longitude - data['loc'].longitude)**2 + \
                (point.latitude - data['loc'].latitude)**2
            
            #get_distance(point, coords)
            if min_distance is None:
                min_distance = distance
                nearest_node = node

            else:
                if distance < min_distance:
                    min_distance = distance
                    nearest_node = node

        nearest_points[nearest_node] = point

    return nearest_points