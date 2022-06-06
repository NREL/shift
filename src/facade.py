"""
Attempting to use Yaml file to generate feeder model
"""

from geometry import (BuildingsFromPlace, BuildingsFromPolygon, 
    BuildingsFromPoint, SimpleLoadGeometriesFromCSV)

from load_builder import (RandomPhaseAllocator, SimpleVoltageSetter, \
    DefaultConnSetter, ConstantPowerFactorBuildingGeometryLoadBuilder, \
    LoadBuilderEngineer)

from load_builder import PiecewiseBuildingAreaToConsumptionConverter
from soupsieve import match
from utils import get_nearest_points_in_the_network
from graph import RoadNetworkFromPlace
from utils import slice_up_network_edges
from clustering import KmeansClustering
from network_plots import PlotlyGISNetworkPlot
from constants import PLOTLY_FORMAT_CUSTOMERS_ONLY, PLOTLY_FORMAT_CUSTOMERS_AND_DIST_TRANSFORMERS_ONLY
import numpy as np
from transformer_builder import ClusteringBasedTransformerLoadMapper, SingleTransformerBuilder
from enums import TransformerConnection, NumPhase, Phase
from secondary_network_builder import SecondaryNetworkBuilder, SecondarySectionsBuilder
from constants import PLOTLY_FORMAT_SIMPLE_NETWORK
from enums import ConductorType, GeometryConfiguration
from line_section import (HorizontalThreePhaseConfiguration, HorizontalThreePhaseNeutralConfiguration,
    HorizontalSinglePhaseConfiguration)
from primary_network_builder import PrimaryNetworkFromRoad, PrimarySectionsBuilder
from graph import RoadNetworkFromPlace
from feeder_network import update_transformer_locations, SimpleTwoLayerDistributionNetworkBuilder, TwoLayerNetworkBuilderDirector
from constants import PLOTLY_FORMAT_CUSTOMERS_DIST_TRANSFORMERS_HT_LINE, PLOTLY_FORMAT_ALL_ASSETS
from exporter.opendss import ConstantPowerFactorLoadWriter, TwoWindingSimpleTransformerWriter, GeometryBasedLineWriter, OpenDSSExporter

import yaml


GEOMETRY_BUILDER_MAPPER = {
    str: BuildingsFromPlace,
    tuple : BuildingsFromPoint,
    list : BuildingsFromPolygon,
    'csv': SimpleLoadGeometriesFromCSV
}


def generate_feeder_from_yaml(yaml_file):

    with open(yaml_file, "r") as f:
        config = yaml.safe_load(f)

    # Location config
    location = config.get('location', {})
    if not location:
        raise Exception(f"`location` attribute missing from config {config}")
    

    # Get geometries
    if 'address' in location and isinstance(location['address'], list) \
        and isinstance(location['address'][0], float):
        location['address'] = tuple(location['address'])
        g = GEOMETRY_BUILDER_MAPPER[type(location['address'])](location['address'])
    else:
        if 'csv_file' in location:
            g = GEOMETRY_BUILDER_MAPPER['csv'](location['address'])

        else:
            raise Exception(f"either address or csv_file \
                field should exist in location {location}")

    # Generate geometries from geometry
    geometries = g.get_geometries()

    # load configs
    load_config = config.get('loads', {})
    if not load_config:
        raise Exception(f"`loads` attribute missing from config {config}")

    # Phase allocator
    if 'phase' not in load_config:
        raise Exception(f"`phase` attribute is missing in load config {load_config}")
    
    if load_config['phase']['method'] == 'random':
        pa = RandomPhaseAllocator(load_config['phase']['pct_single_phase'], \
            load_config['phase']['pct_two_phase']\
            load_config['phase']['pct_three_phase'], geometries)
    else:
        raise Exception(f"Unallowed method for setting phase {load_config['phase']['method']}")

    
    # Connection setter
    if 'conn' not in load_config:
        raise Exception(f"`conn` attribute is missing in load config {load_config}")
    
    if load_config['conn']['method'] == 'default':
        cs = DefaultConnSetter()
    else:
        raise Exception(f"Unallowed method for setting phase {load_config['conn']['method']}")

    # kv setter
    if 'kv' not in load_config:
        raise Exception(f"`kv` attribute is missing in load config {load_config}")
    
    if load_config['kv']['method'] == 'simple':
        vs = SimpleVoltageSetter(load_config['kv']['kv'])
    else:
        raise Exception(f"Unallowed method for setting phase {load_config['conn']['method']}")

    
    # kw setter
    if 'kw' not in load_config:
        raise Exception(f"`kw` attribute is missing in load config {load_config}")
    
    if load_config['kw']['method'] == 'piecewiselinear':
        kws = PiecewiseBuildingAreaToConsumptionConverter(load_config['kw']['curve'])
    else:
        raise Exception(f"Unallowed method for setting phase {load_config['kw']['method']}")

    
    # Generate all the loads
    loads = []
    for g in geometries:

        if 'type' not in load_config:
            raise Exception(f"`type` attribute is missing in load config {load_config}")
    
        if load_config['type']['name'] == 'constantpowerfactor':
            builder = ConstantPowerFactorBuildingGeometryLoadBuilder(g, pa, kws, vs, cs, load_config['type']['pf'])
        else:
            raise Exception(f"Unallowed method for setting phase {load_config['type']['name']}")
        
        #builder = ConstantPowerFactorSimpleLoadGeometryLoadBuilder(g,rpa,vs,cs,1.0)
        b = LoadBuilderEngineer(builder)
        loads.append(b.get_load())

    # Generate transformers
    trans_config = config['dist_xfmrs']

    if 'name' in trans_config['method']:
        pass
    else:
        raise Exception(f"")
    

if __name__ == '__main__':

    generate_feeder_from_yaml(r"C:\Users\KDUWADI\Desktop\NREL_Projects\ciff_track_2\seeds_new\src\examples\sample.yaml")