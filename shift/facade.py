# -*- coding: utf-8 -*-
# Copyright (c) 2022, Alliance for Sustainable Energy, LLC

# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


""" This module is used to consume yaml file to produce synthetic feeeder. """

from typing import Union, List

# third-party imports
import numpy as np
import yaml
import time
import os
from multiprocessing import Pool

# internal imports
from shift.transformer import Transformer
from shift.geometry import (
    BuildingsFromPlace,
    BuildingsFromPolygon,
    BuildingsFromPoint,
    SimpleLoadGeometriesFromCSV,
)
from shift.load_builder import (
    RandomPhaseAllocator,
    SimpleVoltageSetter,
    DefaultConnSetter,
    ConstantPowerFactorBuildingGeometryLoadBuilder,
    LoadBuilderEngineer,
)
from shift.load_builder import PiecewiseBuildingAreaToConsumptionConverter
from shift.graph import (
    RoadNetworkFromPlace,
    RoadNetworkFromPoint,
    RoadNetworkFromPolygon,
)
from shift.clustering import KmeansClustering
from shift.transformer_builder import (
    ClusteringBasedTransformerLoadMapper,
    SingleTransformerBuilder,
)
from shift.enums import TransformerConnection, NumPhase, Phase, ConductorType
from shift.secondary_network_builder import (
    SecondaryNetworkBuilder,
    SecondarySectionsBuilder,
)
from shift.feeder_network import update_transformer_locations
from shift.line_section import (
    HorizontalSinglePhaseNeutralConfiguration,
    HorizontalThreePhaseConfiguration,
    HorizontalThreePhaseNeutralConfiguration,
    HorizontalSinglePhaseConfiguration,
)
from shift.primary_network_builder import (
    PrimaryNetworkFromRoad,
    PrimarySectionsBuilder,
)
from shift.exporter.opendss import (
    ConstantPowerFactorLoadWriter,
    TwoWindingSimpleTransformerWriter,
    GeometryBasedLineWriter,
    OpenDSSExporter,
)
from shift.exceptions import UnsupportedFeatureError
from shift.load import Load


TRANSFORMER_CONNECTION_MAPPER = {
    "delta": TransformerConnection.DELTA,
    "wye-grounded": TransformerConnection.STAR,
    "wye": TransformerConnection.STAR,
    "star_grounded": TransformerConnection.STAR,
}

NUM_PHASE_MAPPER = {1: NumPhase.SINGLE, 2: NumPhase.TWO, 3: NumPhase.THREE}

CONDUCTOR_MAPPING = {
    "overhead": ConductorType.OVERHEAD,
    "underground_concentric": ConductorType.UNDERGROUND_CONCENTRIC,
}


def _get_phase(
    num_phase: int, neutral_present: bool, phase_type: Union[None, str] = None
) -> Phase:
    """Get phase representation.

    Args:
        num_phase (int): Number of phase
        neutral_present (bool): Indicates whether neutral is present or not
        phase_type (Union[None, str]) : Phase type used of number of phase is 1

    Returns:
        Phase: phase object
    """

    if num_phase == 3 and neutral_present:
        return Phase.ABCN
    elif num_phase == 3 and not neutral_present:
        return Phase.ABC
    elif num_phase == 1:
        if neutral_present:
            return {"A": Phase.AN, "B": Phase.BN, "C": Phase.CN}[phase_type]
        else:
            return {"A": Phase.A, "B": Phase.B, "C": Phase.C}[phase_type]


def _get_configuration(config: dict, neutral_present: bool) -> dict:
    """Returns geometry configuration.

    Args:
        config (dict): Initial geometry configuration
        neutral_present (bool): Indicates whether neutral is present or not

    Returns:
        dict: Geometry configuration dictionary
    """

    configuration_ = {}
    if "three_phase" in config:
        if config["three_phase"]["type"] == "horizontal":
            if neutral_present:
                configuration_[
                    NumPhase.THREE
                ] = HorizontalThreePhaseNeutralConfiguration(
                    config["three_phase"]["height_of_top_conductor"],
                    config["three_phase"]["space_between_conductors"],
                    config["three_phase"]["height_of_neutral_conductor"],
                    config["three_phase"]["unit"],
                )
            else:
                configuration_[
                    NumPhase.THREE
                ] = HorizontalThreePhaseConfiguration(
                    config["three_phase"]["height_of_top_conductor"],
                    config["three_phase"]["space_between_conductors"],
                    config["three_phase"]["unit"],
                )
    if "single_phase" in config:
        if config["single_phase"]["type"] == "horizontal":
            if neutral_present:
                configuration_[
                    NumPhase.SINGLE
                ] = HorizontalSinglePhaseNeutralConfiguration(
                    config["single_phase"]["height_of_top_conductor"],
                    config["single_phase"]["space_between_conductors"],
                    config["single_phase"]["unit"],
                )
            else:
                configuration_[
                    NumPhase.SINGLE
                ] = HorizontalSinglePhaseConfiguration(
                    config["single_phase"]["height_of_top_conductor"],
                    config["single_phase"]["unit"],
                )

    return configuration_


def _develop_secondaries(
    sec_id: str,
    transformer: Transformer,
    customer_list: List[Load],
    div_coeff: List[float],
    config: dict,
) -> dict:
    """Develops secondaries for a given transformer and list of customers.

    Args:
        sec_id (str): Unique id for secondary network
        transformer (Transformer): Transformer object
        customer_list (List[Load]): List of load objects
        div_coeff (List[float]): Coefficients for diversity factor function
        config (dict): Configuration for creating secondaries

    Returns:
        dict: contains secondary sections and load to node mapping
    """

    start_time = time.time()
    sn = SecondaryNetworkBuilder(
        customer_list,
        transformer,
        lambda x: div_coeff[0] * np.log(x) + div_coeff[1],
        config["kv"],
        f"_secondary_{sec_id}",
    )

    sn.update_network_with_ampacity()
    load_to_node_mapping = sn.get_load_to_node_mapping()
    longest_length = sn.get_longest_length_in_kvameter() / 1609.34

    k_drop = config["design_factors"]["voltage_drop"] / (longest_length)

    sc = SecondarySectionsBuilder(
        sn.get_network(),
        conductor_type=CONDUCTOR_MAPPING[config["cond_type"]],
        configuration=_get_configuration(
            config["configuration"], config["phase"]["neutral_present"]
        ),
        lateral_configuration=_get_configuration(
            config["configuration"], config["phase"]["service_drop_neutral"]
        ),
        num_phase=NUM_PHASE_MAPPER[config["phase"]["num_phase"]],
        phase=_get_phase(
            config["phase"]["num_phase"],
            config["phase"]["neutral_present"],
            config["phase"]["phase_type"],
        ),
        neutral_present=config["phase"]["neutral_present"],
        material=config["design_factors"]["catalog_type"],
        lateral_material=config["design_factors"]["catalog_type_lateral"],
    )

    end_time = time.time()
    print(f"Id: {sec_id}, time spent {end_time - start_time} seconds")
    print(len(customer_list), transformer.name, len(load_to_node_mapping))
    return {
        "secondary_sections": sc.generate_secondary_line_sections(
            k_drop, config["kv"]
        ),
        "load2node_mapping": load_to_node_mapping,
    }


def generate_feeder_from_yaml(yaml_file: str) -> None:
    """Generates synthetic feeder model by taking in yamk file.

    Args:
        yaml_file (str): yaml file path containing user configurations.

    Examples:

        >>> from shift.facade import generate_feeder_from_yaml
        >>> generate_feeder_from_yaml(r"sample-1.yaml")
    """

    with open(yaml_file, "r", encoding="utf-8") as fpointer:
        config = yaml.safe_load(fpointer)

    # Location config
    location = config.get("location", {})

    # Get geometries
    address = location.get("address", None)
    distance = location.get("distance", None)
    div_func_coeffs = config["div_func_coeff"]

    if address:

        if isinstance(address, str):
            g = BuildingsFromPlace(address, distance)
        elif isinstance(address, list) and isinstance(address[0], list):
            g = BuildingsFromPolygon(address)
        else:
            g = BuildingsFromPoint(address, distance)

    else:
        g = SimpleLoadGeometriesFromCSV(location["csv_file"])

    # Generate geometries from geometry
    geometries = g.get_geometries()

    # load configs
    load_config = config.get("loads", {})

    if load_config["phase"]["method"] == "random":
        pa = RandomPhaseAllocator(
            load_config["phase"]["pct_single_phase"],
            load_config["phase"]["pct_two_phase"],
            load_config["phase"]["pct_three_phase"],
            geometries,
        )

    # Connection setter
    if load_config["conn"]["method"] == "default":
        cs = DefaultConnSetter()

    # kv setter
    if load_config["kv"]["method"] == "simple":
        vs = SimpleVoltageSetter(load_config["kv"]["kv"])

    # kw setter
    if load_config["kw"]["method"] == "piecewiselinear":
        kws = PiecewiseBuildingAreaToConsumptionConverter(
            load_config["kw"]["curve"]
        )

    # Generate all the loads
    loads = []
    for g in geometries:

        if load_config["type"]["name"] == "constantpowerfactor":
            builder = ConstantPowerFactorBuildingGeometryLoadBuilder(
                g, pa, kws, vs, cs, load_config["type"]["pf"]
            )

        b = LoadBuilderEngineer(builder)
        loads.append(b.get_load())

    # Generate transformers
    trans_config = config["dist_xfmrs"]
    if trans_config["method"]["name"] == "clustering":

        kmeans_cluster = KmeansClustering(
            int(
                len(loads)
                / trans_config["method"]["estimated_customers_per_transformer"]
            )
        )

        trans_builder = ClusteringBasedTransformerLoadMapper(
            loads,
            clustering_object=kmeans_cluster,
            diversity_factor_func=lambda x: div_func_coeffs[0] * np.log(x)
            + div_func_coeffs[1],
            ht_kv=trans_config["kv"]["ht"],
            lt_kv=trans_config["kv"]["lt"],
            ht_conn=TRANSFORMER_CONNECTION_MAPPER[trans_config["conn"]["ht"]],
            lt_conn=TRANSFORMER_CONNECTION_MAPPER[trans_config["conn"]["lt"]],
            ht_phase=_get_phase(
                trans_config["phase"]["num_phase"],
                trans_config["conn"]["ht"] == "wye-grounded",
                trans_config["phase"]["phase_type"],
            ),
            lt_phase=_get_phase(
                trans_config["phase"]["num_phase"],
                trans_config["conn"]["lt"] == "wye-grounded",
                trans_config["phase"]["phase_type"],
            ),
            num_phase=NUM_PHASE_MAPPER.get(trans_config["phase"]["num_phase"]),
            catalog_type=trans_config["design_factors"]["catalog_type"],
            power_factor=trans_config["design_factors"]["pf"],
            adjustment_factor=trans_config["design_factors"]["adj_factor"],
            planned_avg_annual_growth=trans_config["design_factors"][
                "planned_avg_annual_growth"
            ],
            actual_avg_annual_growth=trans_config["design_factors"][
                "actual_avg_annual_growth"
            ],
            actual_years_in_operation=trans_config["design_factors"][
                "actual_years_in_operation"
            ],
            planned_years_in_operation=trans_config["design_factors"][
                "planned_years_in_operation"
            ],
        )
        transformers = trans_builder.get_transformer_load_mapping()

    # Get the primary network
    primary_config = config.get("primary_network", {})
    substation_config = config.get("substation", {})
    substation_tr_config = config.get("substation_xfmr", {})

    if primary_config["method"] == "openstreet":

        if address:
            if isinstance(address, str):
                road_network = RoadNetworkFromPlace(address, distance)
            elif isinstance(address, list) and isinstance(address[0], list):
                road_network = RoadNetworkFromPolygon(address)
            else:
                road_network = RoadNetworkFromPoint(address, distance)

        elif primary_config["method"] == "openstreet":
            UnsupportedFeatureError(
                "Road network from buildings locations\
                only is still need to be updated!"
            )

        pnet = PrimaryNetworkFromRoad(
            road_network,
            transformers,
            substation_config["location"],
            lambda x: div_func_coeffs[0] * np.log(x) + div_func_coeffs[1],
            primary_config["kv"],
            primary_config["max_pp_distance"],
            power_factor=primary_config["design_factors"]["pf"],
            adjustment_factor=primary_config["design_factors"]["adj_factor"],
            planned_avg_annual_growth=primary_config["design_factors"][
                "planned_avg_annual_growth"
            ],
            actual_avg_annual_growth=primary_config["design_factors"][
                "actual_avg_annual_growth"
            ],
            actual_years_in_operation=primary_config["design_factors"][
                "actual_years_in_operation"
            ],
            planned_years_in_operation=primary_config["design_factors"][
                "planned_years_in_operation"
            ],
        )

        substation_node = pnet.substation_node
        substation_coords = pnet.substation_coords

        pnet.update_network_with_ampacity()
        longest_length = pnet.get_longest_length_in_kvameter() / 1609.34
        k_drop = primary_config["design_factors"]["voltage_drop"] / (
            longest_length
        )

        psections = PrimarySectionsBuilder(
            pnet.get_network(),
            conductor_type=CONDUCTOR_MAPPING[primary_config["cond_type"]],
            configuration=_get_configuration(
                primary_config["configuration"],
                primary_config["phase"]["neutral_present"],
            ),
            num_phase=NUM_PHASE_MAPPER[primary_config["phase"]["num_phase"]],
            phase=_get_phase(
                primary_config["phase"]["num_phase"],
                primary_config["phase"]["neutral_present"],
                primary_config["phase"]["phase_type"],
            ),
            neutral_present=primary_config["phase"]["neutral_present"],
            material=primary_config["design_factors"]["catalog_type"],
        )

        primary_sections = psections.generate_primary_line_sections(
            k_drop, primary_config["kv"]
        )
        r_nodes = pnet.get_trans_node_mapping()
        print(len(r_nodes), len(transformers), r_nodes)
        transformers = update_transformer_locations(
            r_nodes, transformers, primary_sections
        )
        print(len(transformers))

    # Model the substation
    sub_trans_builder = SingleTransformerBuilder(
        loads,
        substation_coords[0],
        substation_coords[1],
        diversity_factor_func=lambda x: div_func_coeffs[0] * np.log(x)
        + div_func_coeffs[1],
        ht_kv=substation_tr_config["kv"]["ht"],
        lt_kv=substation_tr_config["kv"]["lt"],
        ht_conn=TRANSFORMER_CONNECTION_MAPPER[
            substation_tr_config["conn"]["ht"]
        ],
        lt_conn=TRANSFORMER_CONNECTION_MAPPER[
            substation_tr_config["conn"]["lt"]
        ],
        ht_phase=_get_phase(
            substation_tr_config["phase"]["num_phase"],
            substation_tr_config["conn"]["ht"] == "wye-grounded",
            substation_tr_config["phase"]["phase_type"],
        ),
        lt_phase=_get_phase(
            substation_tr_config["phase"]["num_phase"],
            substation_tr_config["conn"]["lt"] == "wye-grounded",
            substation_tr_config["phase"]["phase_type"],
        ),
        num_phase=NUM_PHASE_MAPPER[substation_tr_config["phase"]["num_phase"]],
        power_factor=substation_tr_config["design_factors"]["pf"],
        adjustment_factor=substation_tr_config["design_factors"]["adj_factor"],
        planned_avg_annual_growth=substation_tr_config["design_factors"][
            "planned_avg_annual_growth"
        ],
        actual_avg_annual_growth=substation_tr_config["design_factors"][
            "actual_avg_annual_growth"
        ],
        actual_years_in_operation=substation_tr_config["design_factors"][
            "actual_years_in_operation"
        ],
        planned_years_in_operation=substation_tr_config["design_factors"][
            "planned_years_in_operation"
        ],
    )
    substation_transformer = sub_trans_builder.get_transformer_load_mapping()

    # Model secondaries
    secondary_config = config.get("secondary_network", {})
    secondary_sections = []
    load_to_node_mapping_dict = {}

    with Pool(min(os.cpu_count(), len(transformers))) as pool:
        secondaries = pool.starmap(
            _develop_secondaries,
            [
                [
                    sec_id,
                    trans,
                    transformers[trans],
                    div_func_coeffs,
                    secondary_config,
                ]
                for sec_id, trans in enumerate(transformers)
            ],
        )

    for result in secondaries:
        secondary_sections.extend(result["secondary_sections"])
        load_to_node_mapping_dict.update(result["load2node_mapping"])
        print(
            len(load_to_node_mapping_dict),
            len(result["load2node_mapping"]),
            len(load_to_node_mapping_dict) - len(result["load2node_mapping"]),
            len(loads),
        )

    # print('--', load_to_node_mapping_dict)
    # Now export the model

    if config["exporter"]["type"] == "opendss":

        if load_config["type"]["name"] == "constantpowerfactor":
            load_writer = ConstantPowerFactorLoadWriter(
                loads, load_to_node_mapping_dict, "loads.dss"
            )

        dist_xfmr_writer = TwoWindingSimpleTransformerWriter(
            list(transformers.keys()), "dist_xfmrs.dss"
        )
        substation_xfmre_writer = TwoWindingSimpleTransformerWriter(
            list(substation_transformer.keys()), "sub_trans.dss"
        )
        sections_writer = GeometryBasedLineWriter(
            primary_sections + secondary_sections,
            line_file_name="lines.dss",
            geometry_file_name="line_geometry.dss",
            wire_file_name="wiredata.dss",
            cable_file_name="cabledata.dss",
        )

        opendss_writer = OpenDSSExporter(
            [
                dist_xfmr_writer,
                substation_xfmre_writer,
                sections_writer,
                load_writer,
            ],
            config["exporter"]["path"],
            "master.dss",
            config["substation"]["circuit_name"],
            config["substation"]["kv"],
            config["substation"]["freq"],
            _get_phase(
                config["substation"]["phase"]["num_phase"],
                config["substation"]["phase"]["neutral_present"],
                config["substation"]["phase"]["phase_type"],
            ),
            NUM_PHASE_MAPPER[config["substation"]["phase"]["num_phase"]],
            # pylint: disable-next=line-too-long
            f"{substation_node.split('_')[0]}_{substation_node.split('_')[1]}_htnode",
            config["substation"]["z1"],
            config["substation"]["z1"],
            config["substation"]["kv_levels"],
        )
        opendss_writer.export()
