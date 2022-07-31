""" This module is intended to be used as example code. """
import time

import numpy as np

from shift.geometry import BuildingsFromPlace
from shift.load_builder import (
    RandomPhaseAllocator,
    SimpleVoltageSetter,
    DefaultConnSetter,
    ConstantPowerFactorBuildingGeometryLoadBuilder,
    LoadBuilderEngineer,
)
from shift.load_builder import PiecewiseBuildingAreaToConsumptionConverter
from shift.graph import RoadNetworkFromPlace
from shift.clustering import KmeansClustering
from shift.transformer_builder import (
    ClusteringBasedTransformerLoadMapper,
    SingleTransformerBuilder,
)
from shift.enums import TransformerConnection, NumPhase, Phase
from shift.secondary_network_builder import (
    SecondaryNetworkBuilder,
    SecondarySectionsBuilder,
)
from shift.enums import ConductorType
from shift.line_section import (
    HorizontalThreePhaseConfiguration,
    HorizontalThreePhaseNeutralConfiguration,
    HorizontalSinglePhaseConfiguration,
)
from shift.primary_network_builder import (
    PrimaryNetworkFromRoad,
    PrimarySectionsBuilder,
)
from shift.feeder_network import update_transformer_locations
from shift.exporter.opendss import (
    ConstantPowerFactorLoadWriter,
    TwoWindingSimpleTransformerWriter,
    GeometryBasedLineWriter,
    OpenDSSExporter,
)

# pylint: disable-next=line-too-long
# g = SimpleLoadGeometriesFromCSV(r'C:\Users\KDUWADI\Desktop\NREL_Projects\ciff_track_2\data\grp_customers_reduced.csv')
# pylint: enable-next=line-too-long
g = BuildingsFromPlace("Chennai, India")
geometries = g.get_geometries()
rpa = RandomPhaseAllocator(100, 0, 0, geometries)
vs = SimpleVoltageSetter(0.415)
cs = DefaultConnSetter()
area_to_kw_curve = [(0, 0), (10, 15.0), (20, 35), (50, 80)]
pbacc = PiecewiseBuildingAreaToConsumptionConverter(area_to_kw_curve)

loads = []
for g in geometries:
    builder = ConstantPowerFactorBuildingGeometryLoadBuilder(
        g, rpa, pbacc, vs, cs, 1.0
    )
    # builder = ConstantPowerFactorSimpleLoadGeometryLoadBuilder(g,rpa,vs,cs,1.0)
    b = LoadBuilderEngineer(builder)
    loads.append(b.get_load())

kmeans_cluster = KmeansClustering(20)
trans_builder = ClusteringBasedTransformerLoadMapper(
    loads,
    clustering_object=kmeans_cluster,
    diversity_factor_func=lambda x: 0.3908524 * np.log(x) + 1.65180707,
    ht_kv=11.0,
    lt_kv=0.4,
    ht_conn=TransformerConnection.DELTA,
    lt_conn=TransformerConnection.STAR,
    ht_phase=Phase.ABC,
    lt_phase=Phase.ABCN,
    num_phase=NumPhase.THREE,
    power_factor=0.9,
    adjustment_factor=1.15,
)

t = trans_builder.get_transformer_load_mapping()


graph = RoadNetworkFromPlace("chennai, india")
pnet = PrimaryNetworkFromRoad(
    graph,
    t,
    (80.2786311, 13.091658),
    lambda x: 0.3908524 * np.log(x) + 1.65180707,
    11.0,
    100,
)

s_node = pnet.substation_node
s_coords = pnet.substation_coords

pnet.update_network_with_ampacity()
longest_length = pnet.get_longest_length_in_kvameter() / 1609.34
k_drop = 2 / (longest_length)

psections = PrimarySectionsBuilder(
    pnet.get_network(),
    ConductorType.OVERHEAD,
    {NumPhase.THREE: HorizontalThreePhaseConfiguration(9, 0.4, "m")},
    NumPhase.THREE,
    Phase.ABC,
    False,
    material="ACSR",
)

l_sections = psections.generate_primary_line_sections(k_drop, 11.0)
r_nodes = pnet.get_trans_node_mapping()
t = update_transformer_locations(r_nodes, t, l_sections)


sub_trans_builder = SingleTransformerBuilder(
    loads,
    s_coords[0],
    s_coords[1],
    diversity_factor_func=lambda x: 0.3908524 * np.log(x) + 1.65180707,
    ht_kv=33,
    lt_kv=11,
    ht_conn=TransformerConnection.DELTA,
    lt_conn=TransformerConnection.STAR,
    ht_phase=Phase.ABC,
    lt_phase=Phase.ABCN,
    num_phase=NumPhase.THREE,
    power_factor=0.9,
    adjustment_factor=1.15,
)
st = sub_trans_builder.get_transformer_load_mapping()


s_sections = []
counter = 0
load_to_node_mapping_dict = {}


print(len(t))
for trans, cust_list in t.items():

    start_time = time.time()
    sn = SecondaryNetworkBuilder(
        cust_list,
        trans,
        lambda x: 0.3908524 * np.log(x) + 1.65180707,
        0.4,
        f"_secondary_{id}",
    )
    sn.update_network_with_ampacity()
    load_to_node_mapping_dict.update(sn.get_load_to_node_mapping())
    longest_length = sn.get_longest_length_in_kvameter() / 1609.34
    k_drop = 3 / (200 * 2)  # 5/(longest_length)
    sc = SecondarySectionsBuilder(
        sn.get_network(),
        ConductorType.OVERHEAD,
        {
            NumPhase.THREE: HorizontalThreePhaseNeutralConfiguration(
                9, 0.4, 9.4, "m"
            )
        },
        {
            NumPhase.SINGLE: HorizontalSinglePhaseConfiguration(9, "m"),
        },
        NumPhase.THREE,
        Phase.ABCN,
        True,
        material="ACSR",
    )

    s_sections.extend(sc.generate_secondary_line_sections(k_drop, 0.4))
    end_time = time.time()
    print(f"Id: {id}, time spent {end_time - start_time} seconds")
    counter += 1


lw = ConstantPowerFactorLoadWriter(
    loads, load_to_node_mapping_dict, "loads.dss"
)
tw = TwoWindingSimpleTransformerWriter(list(t.keys()), "dist_xfmrs.dss")
stw = TwoWindingSimpleTransformerWriter(list(st.keys()), "sub_trans.dss")
sw = GeometryBasedLineWriter(
    l_sections + s_sections,
    line_file_name="lines.dss",
    geometry_file_name="line_geometry.dss",
    wire_file_name="wiredata.dss",
    cable_file_name="cabledata.dss",
)


dw = OpenDSSExporter(
    [tw, stw, sw, lw],
    r"C:\Users\KDUWADI\Desktop\NREL_Projects\ciff_track_2\exports\opendss_new",
    "master.dss",
    "chennai",
    33.0,
    50,
    Phase.ABCN,
    NumPhase.THREE,
    f"{s_node.split('_')[0]}_{s_node.split('_')[1]}_htnode",
    [0.001, 0.001],
    [0.001, 0.001],
    [0.4, 11.0, 33.0],
)
dw.export()
# p = PlotlyGISNetworkPlot(
# sn.G,
# 'pk.eyJ1Ijoia2R1d2FkaSIsImEiOiJja3cweHpmM3YwYnk3MnVwamphNTd1ZG44In0.tsKgUvzpPVi4m1p3ekedaQ',
# 'light',
# asset_specific_style=PLOTLY_FORMAT_SIMPLE_NETWORK
# )
# p.show()

# road_network = RoadNetworkFromPlace("chennai, india")
# road_network.get_network()
# sliced_graph = slice_up_network_edges(road_network.updated_network, 60)
# nearest_nodes = get_nearest_points_in_the_network(sliced_graph, clusters['centre'])


# print([[l.longitude, l.latitude] for l in loads])
# quit()

# network_builder = SimpleTwoLayerDistributionNetworkBuilder()
# n = TwoLayerNetworkBuilderDirector(
#     loads,
#     list(t.keys()),
#     l_sections,
#     s_sections,
#     network_builder)
# p = PlotlyGISNetworkPlot(
#     n.get_network(),
#     'pk.eyJ1Ijoia2R1d2FkaSIsImEiOiJja3cweHpmM3YwYnk3MnVwamphNTd1ZG44In0.tsKgUvzpPVi4m1p3ekedaQ',
#     'light',
#     asset_specific_style=PLOTLY_FORMAT_ALL_ASSETS
# )
# p.show()
