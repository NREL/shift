
# Manage python imports
from load import Load
from transformer import Transformer
from utils import (triangulate_using_mesh, set_node_edge_type, 
    get_nearest_points_in_the_network, get_distance)
import networkx as nx 
from primary_network_builder import BaseNetworkBuilder
from enums import ConductorType, NumPhase, Phase
from line_section import (LineGeometryConfiguration)
from exceptions import CustomerInvalidPhase, PhaseMismatchError, IncompleteGeometryConfigurationDict
from primary_network_builder import (BaseSectionsBuilder, geometry_based_line_section_builder)


class SecondarySectionsBuilder(BaseSectionsBuilder):

    def __init__(self,
                secondary_network: nx.Graph,
                conductor_type: ConductorType,
                configuration: dict,
                lateral_configuration: dict,
                num_phase: NumPhase,
                phase: Phase,
                neutral_present: True,
                material: str = 'all',
                lateral_material: str = 'all'
                ):

        super().__init__(secondary_network, conductor_type, configuration, num_phase, phase, neutral_present, material)
        self.lateral_material = lateral_material
        self.lateral_configuration = lateral_configuration


    def generate_secondary_line_sections(self, k_drop, kv_base):

        line_sections = []
        node_data_dict = {node[0]: node[1] for node in self.network.nodes.data()}
        for edge in self.network.edges():
            edge_data = self.network.get_edge_data(*edge)

            # Find edge that connects load and this should be cable
            if 'load' in self.network.nodes[edge[0]] or 'load' in self.network.nodes[edge[1]]:

                load_node = 0 if 'load' in self.network.nodes[edge[0]] else 1
                load_obj = self.network.nodes[edge[load_node]]['object']
                # fromnode_phase = load_obj.phase if load_node == 0 else self.phase
                # tonode_phase = load_obj.phase if load_node == 1 else self.phase
                
                if load_obj.num_phase.value > self.num_phase.value:
                    raise CustomerInvalidPhase(load_obj.num_phase, self.num_phase)

                # Let's check for phase mismatch if any
                if self.num_phase.value == load_obj.num_phase.value:
                    if self.phase != load_obj.phase:
                        raise PhaseMismatchError(load_obj.phase, self.phase)

                if load_obj.num_phase not in self.lateral_configuration:
                    raise IncompleteGeometryConfigurationDict(load_obj.num_phase, self.lateral_configuration)

                
                line_section = geometry_based_line_section_builder(
                                        edge[0],
                                        edge[1],
                                        load_obj.num_phase,
                                        load_obj.phase,
                                        load_obj.phase,
                                        get_distance(node_data_dict[edge[0]]['pos'], node_data_dict[edge[1]]['pos']),
                                        'm',
                                        edge_data['ampacity'],
                                        self.catalog_dict[ConductorType.UNDERGROUND_CONCENTRIC],
                                        self.neutral_present,
                                        ConductorType.UNDERGROUND_CONCENTRIC,
                                        self.lateral_configuration[load_obj.num_phase],
                                        k_drop,
                                        kv_base,
                                        self.lateral_material
                )
                
            else:
                if self.num_phase not in self.geometry_configuration:
                    raise IncompleteGeometryConfigurationDict(self.num_phase, self.geometry_configuration)
                line_section = geometry_based_line_section_builder(
                                        edge[0],
                                        edge[1],
                                        self.num_phase,
                                        self.phase,
                                        self.phase,
                                        get_distance(node_data_dict[edge[0]]['pos'], node_data_dict[edge[1]]['pos']),
                                        'm',
                                        edge_data['ampacity'],
                                        self.catalog_dict[self.conductor_type],
                                        self.neutral_present,
                                        self.conductor_type,
                                        self.geometry_configuration[self.num_phase],
                                        k_drop,
                                        kv_base,
                                        self.material
                )

            line_sections.append(line_section)

        return line_sections


class SecondaryNetworkBuilder(BaseNetworkBuilder):

    def __init__(self,
                    load_list: list[Load],
                    transformer: Transformer,
                    div_func,
                    kv_ll: float,
                    node_append_str: str,
                    forbidden_areas: str = None,
                    max_pole_to_pole_distance: float = 100,
                    power_factor: float = 0.9,
                    adjustment_factor: float = 1.2,
                    planned_avg_annual_growth: float = 2,
                    actual_avg_annual_growth: float = 4,
                    actual_years_in_operation: float = 15,
                    planned_years_in_operation: float = 10
                    ):

        super().__init__(div_func,
                        kv_ll,
                        max_pole_to_pole_distance,
                        power_factor,
                        adjustment_factor,
                        planned_avg_annual_growth,
                        actual_avg_annual_growth,
                        actual_years_in_operation,
                        planned_years_in_operation)
        self.transformer = transformer
        self.load_to_node_mapping = {}

        load_locations = [[l.longitude, l.latitude] for l in load_list]

        if len(load_locations) > 2:
            
            # We use meshed approach to come up with network graph
            self.network, self.points, self.customer_to_node_mapping = \
                triangulate_using_mesh(load_locations, forbidden_areas=forbidden_areas, \
                    node_append_str=node_append_str)
            
            # Unfreeze the network if already frozen
            if nx.is_frozen(self.network):
                self.network = nx.Graph(self.network)

            self.source_node = [n for n in get_nearest_points_in_the_network(self.network, \
                [(self.transformer.longitude, self.transformer.latitude)])][0]

            # Connect the customers as well

            for load in load_list:
                to_node = self.customer_to_node_mapping[f'{load.longitude}_{load.latitude}_customer']
                self.network.add_node(load.name, pos=(load.longitude, load.latitude), object=load, load=True)
                self.network.add_edge(load.name, to_node, load_present=True)
                self.load_to_node_mapping[load.name] = to_node

            self.tr_lt_node = f"{self.transformer.longitude}_{self.transformer.latitude}_ltnode"
            self.network.add_node(self.tr_lt_node, pos=(self.transformer.longitude, self.transformer.latitude ))
            self.network.add_edge(self.tr_lt_node, self.source_node)
            
            self.network = set_node_edge_type(self.network)
        else:
            raise Exception(f"Hey invalid number of customers for transformers!")
        

    def get_load_to_node_mapping(self):
        return self.load_to_node_mapping

    def get_network(self):
        return self.network

    def get_longest_length_in_kvameter(self):
        return self.longest_length
    
    def update_network_with_ampacity(self):

        """ Create a directed graph by providing source node """
        dfs_tree = nx.dfs_tree(self.network,source=self.source_node)

        """ Perform a depth first traversal to find all successor nodes"""
        x, y = [], []
        for edge in dfs_tree.edges():
            
            """ Compute distance from the source"""
            distance = nx.resistance_distance(self.network, self.source_node, edge[1])
            self.network[edge[0]][edge[1]]['distance'] = distance

            """ Perform a depth first traversal to find all successor nodes"""
            dfs_successors = nx.dfs_successors(dfs_tree, source=edge[1])

            """ Create a subgraph"""
            nodes_to_retain = [edge[1]]
            for k, v in dfs_successors.items():
                nodes_to_retain.extend(v)
            subgraph = self.network.subgraph(nodes_to_retain)

            """ Let's compute maximum diversified kva demand downward of this edge"""
            noncoincident_kws = 0
            num_of_customers = 0
            for node in subgraph.nodes():
                if 'load' in subgraph.nodes[node]:
                    num_of_customers += 1
                    noncoincident_kws += subgraph.nodes[node]['object'].kw

            self.network[edge[0]][edge[1]]['ampacity'] = self.compute_ampacity(noncoincident_kws, num_of_customers)
            x.append(distance)
            y.append(self.network[edge[0]][edge[1]]['ampacity'])

        
        node_data_dict = {node[0]: node[1] for node in self.network.nodes.data()}
        bfs_tree = nx.bfs_tree(self.network, self.source_node)
        for edge in bfs_tree.edges():
            try:
                bfs_tree[edge[0]][edge[1]]['cost'] = get_distance(node_data_dict[edge[0]]['pos'], node_data_dict[edge[1]]['pos'])*\
                self.network[edge[0]][edge[1]]['ampacity']*1.732*self.kv_ll
            except Exception as e:
                print(e)
                print('help')
        self.longest_length = nx.dag_longest_path_length(bfs_tree, weight="cost")
    


        
    


           




