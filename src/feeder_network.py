
# Handle python imports
import networkx as nx
from abc import ABC, abstractmethod
from load import Load
from enums import NetworkAsset
from transformer import Transformer
from line_section import Line
from typing import List


def update_transformer_locations(retain_nodes, transformers_cust_mapper, primary_lines):

    rnode_to_trans_mapping = {}
    for rnode, rdict in retain_nodes.items():
        for trans, cust_list in transformers_cust_mapper.items():
            if rdict['centre'] == (trans.longitude, trans.latitude):
                rnode_to_trans_mapping[rnode] = {
                                                'trans': trans, 
                                                'longitude': rdict['longitude'],
                                                'latitude': rdict['latitude'],
                                                'cust_list' : cust_list
                }
    new_transformers_cust_mapper = {}
    for edge in primary_lines:
        for node in [edge.fromnode, edge.tonode]:
            if node in rnode_to_trans_mapping:
                trans_obj = rnode_to_trans_mapping[node]['trans']
                trans_obj.longitude = rnode_to_trans_mapping[node]['longitude']
                trans_obj.latitude = rnode_to_trans_mapping[node]['latitude']
                new_transformers_cust_mapper[trans_obj] = rnode_to_trans_mapping[node]['cust_list']

    return new_transformers_cust_mapper



class TwoLayerDistributionNetworkBuilder(ABC):

    """ Interface to build two layer (low tension + high tension) distribution network """


    """ Abstract method to add customer nodes to the distribution network """
    @abstractmethod
    def add_load_nodes(self):
        pass
    
    
    """ Abstract method to add distribution transformer nodes"""
    @abstractmethod
    def add_distribution_transformers(self, loads: List[Load]):
        pass


    """ Abstract method to add low tension network """
    @abstractmethod
    def add_low_tension_network(self):
        pass


    """ Abstract method to add high tension network"""
    @abstractmethod
    def add_high_tension_network(self):
        pass

    """ Abstract method to add substation """
    @abstractmethod
    def add_substation(self):
        pass

class TwoLayerNetworkBuilderDirector:

    def __init__(self,
                    loads:  List[Load],
                    transformers: List[Transformer],
                    primary_edges: List[Line],
                    secondary_edges: List[Line],
                    builder: TwoLayerDistributionNetworkBuilder):
        
        self.builder = builder
        self.builder.add_load_nodes(loads)
        self.builder.add_distribution_transformers(transformers)
        self.builder.add_high_tension_network(primary_edges)
        self.builder.add_low_tension_network(secondary_edges)
        
    def get_network(self):
        return self.builder.feeder
        

class SimpleTwoLayerDistributionNetworkBuilder(TwoLayerDistributionNetworkBuilder):
    
    def __init__(self):
        
        self.feeder  = nx.Graph()

    def add_load_nodes(self, loads: List[Load]):

        """ Loop over all the load and add to the network """
        for load in loads:
            
            self.feeder.add_node(
                load.name, pos=(load.longitude, load.latitude),
                type=NetworkAsset.LOAD,
                data=load.__dict__,
                object = load
            )
            
    def add_distribution_transformers(self, transformers: List[Transformer]):
        
        
        for xfmr in transformers:
            
            self.feeder.add_node(
                xfmr.name, pos=(xfmr.longitude, xfmr.latitude),
                type=NetworkAsset.DISTXFMR,
                data=xfmr.__dict__,
                object = xfmr
            )

    def add_low_tension_network(self, edges: List[Line]):
        
        for edge in edges:

            if not self.feeder.has_node(edge.fromnode):
                self.feeder.add_node(
                    edge.fromnode,
                    pos = (float(edge.fromnode.split('_')[0]), float(edge.fromnode.split('_')[1])),
                    type = NetworkAsset.LTNODE,
                    data = {}
                )
            if not self.feeder.has_node(edge.tonode):
                self.feeder.add_node(
                    edge.tonode,
                    pos = (float(edge.tonode.split('_')[0]), float(edge.tonode.split('_')[1])),
                    type = NetworkAsset.LTNODE,
                    data = {}
                )
            self.feeder.add_edge(
                edge.fromnode, 
                edge.tonode, 
                type = NetworkAsset.LTLINE,
                data = {}, 
                object=edge
            )

    def add_high_tension_network(self, edges: List[Line]):


        for edge in edges:
            self.feeder.add_node(
                edge.fromnode,
                pos = (float(edge.fromnode.split('_')[0]), float(edge.fromnode.split('_')[1])),
                type = NetworkAsset.HTNODE,
                data = {}
            )
            self.feeder.add_node(
                edge.tonode,
                pos = (float(edge.tonode.split('_')[0]), float(edge.tonode.split('_')[1])),
                type = NetworkAsset.HTNODE,
                data = {}
            )
            self.feeder.add_edge(
                edge.fromnode, 
                edge.tonode, 
                type = NetworkAsset.HTLINE,
                data = {}, 
                object=edge
            )

        # Make correction to transformer node:
        # Pull the transformer node to network node and convert to edge 

    def add_substation(self):
        pass


if __name__ == '__main__':
   pass

    

    

    




    


        






