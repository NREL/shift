""" Operations related to graph!"""
from abc import ABC, abstractmethod
import osmnx as ox
import networkx as nx
from shift.exceptions import AttributeDoesNotExistError
from typing import List
import shapely

""" Interface for getting network from OpenStreet data """
class OpenStreetRoadNetwork(ABC):

    def get_network(self, node_append_str=None):
        
        if hasattr(self, 'graph'):
            # Converting diected graph to undirected graph
            network = self.graph.to_undirected()

            # Find a minimum spanning tree of the network
            network = nx.minimum_spanning_tree(network)

            if node_append_str:
                network = nx.relabel_nodes(network, {n : str(n) + node_append_str for n in network.nodes()})

            self.updated_network = nx.Graph()
            for node in network.nodes.data():
                # x is longitude and y is latitude
                self.updated_network.add_node(
                    node[0], pos=(node[1]['x'], node[1]['y']),
                    type='node', data = node[1]
                )
            for edge in network.edges():
                self.updated_network.add_edge(edge[0], edge[1], type='edge')

            return self.updated_network
        else:
            raise AttributeDoesNotExistError(f"'graph' attribute does not exist yet \
                for OpenStreet type road netwwork!")


""" Getting road network from single point within bounding box"""
class RoadNetworkFromPoint(OpenStreetRoadNetwork):

    def __init__(self, point: tuple, max_dist=1000, dist_type="bbox", network_type="drive"):

        # e.g. (13.242134, 80.275948)
        self.point = point
        self.max_dist = max_dist
        self.dist_type = dist_type
        self.network_type = network_type

    def get_network(self, node_append_str=None):
        
        self.graph = ox.graph.graph_from_point(self.point, dist=self.max_dist, dist_type=self.dist_type, network_type=self.network_type)
        super().get_network(node_append_str)


""" Getting road network from a place address within bounding box"""
class RoadNetworkFromPlace(OpenStreetRoadNetwork):

    def __init__(self, place: str, max_dist=1000, dist_type="bbox", network_type="drive"):

        # e.g. Chennai, India
        self.place = place
        self.max_dist = max_dist
        self.dist_type = dist_type
        self.network_type = network_type

    def get_network(self, node_append_str=None):
        self.graph =  ox.graph.graph_from_address(self.place, dist=self.max_dist, dist_type=self.dist_type, network_type=self.network_type)
        super().get_network(node_append_str)


""" Getting road network from a given polygon """
class RoadNetworkFromPolygon(OpenStreetRoadNetwork):

    def __init__(self, polygon: List[list], custom_filter='["highway"]'):

        # e.g. [[13.242134, 80.275948]]
        self.polygon = polygon
        self.custom_filter = custom_filter

    def get_network(self, node_append_str=None):

        polygon = shapely.geometry.Polygon(self.polygon)
        self.graph = ox.graph.graph_from_polygon(polygon, custom_filter=self.custom_filter)
        super().get_network(node_append_str)

if __name__ == '__main__':

    graph = RoadNetworkFromPlace('chennai, india')
    graph.get_network()
    from utils import slice_up_network_edges
    g = slice_up_network_edges(graph.updated_network, 100)

    from network_plots import PlotlyGISNetworkPlot
    from constants import PLOTLY_FORMAT_SIMPLE_NETWORK
    p = PlotlyGISNetworkPlot(
            g,
            'pk.eyJ1Ijoia2R1d2FkaSIsImEiOiJja3cweHpmM3YwYnk3MnVwamphNTd1ZG44In0.tsKgUvzpPVi4m1p3ekedaQ',
            'satellite',
            asset_specific_style=PLOTLY_FORMAT_SIMPLE_NETWORK
        )
    p.show()
        
