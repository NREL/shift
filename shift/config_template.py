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

""" Module handling config template validation. """

from typing import List, Union
from enum import Enum

from pydantic import BaseModel, conint, validator, confloat

from shift.constants import (
    KV_MIN,
    KV_MAX,
    MIN_POWER_FACTOR,
    MAX_POWER_FACTOR,
    MIN_ADJUSTMENT_FACTOR,
    MAX_ADJUSTMENT_FACTOR,
    MIN_YEAR_OPERATION,
    MAX_YEAR_OPERATION,
    MIN_PERCENTAGE,
    MAX_PERCENTAGE,
    MIN_POLE_TO_POLE_DISTANCE,
    MAX_POLE_TO_POLE_DISTANCE,
)


class Connection(str, Enum):
    delta = "delta"  # pylint: disable=all
    star_grounded = "star_grounded"
    star = "star"


class LoadPhaseMethod(str, Enum):
    random = "random"


class LoadKVMethod(str, Enum):
    simple = "simple"


class LoadConnectionMethod(str, Enum):
    default = "default"


class LoadKWMethod(str, Enum):
    piecewiselinear = "piecewiselinear"


class LoadTypeMethod(str, Enum):
    constantpowerfactor = "constantpowerfactor"


class DTMethodName(str, Enum):
    clustering = "clustering"


class DTClusterMethod(str, Enum):
    location_kmeans = "location_kmeans"


class ConductorType(str, Enum):
    overhead = "overhead"
    underground = "underground"


class ConductorGeometry(str, Enum):
    horizontal = "horizontal"
    vertical = "vertical"


class PrimaryNetworkMethod(str, Enum):
    openstreet = "openstreet"


class Location(BaseModel):
    address: Union[
        str, List[list[float, float]], tuple[float, float]
    ] = "chennai, india"
    distance: confloat(ge=200.0, le=10000.0) = 300.0


class TransformerPhase(BaseModel):
    num_phase: conint(ge=1, le=3) = 3
    phase_type: Union[None, str] = None
    neutral_present: bool = True


class Substation(BaseModel):
    location: tuple[float, float] = (80.2786311, 13.091658)
    circuit_name: str = "chennai"
    kv: confloat(ge=KV_MIN, le=KV_MAX) = 33.0
    freq: int = 50.0
    pu: confloat(ge=0.9, le=1.1) = 1.0
    phase: TransformerPhase = TransformerPhase()
    z1: list[float, float] = [0.001, 0.001]
    z0: list[float, float] = [0.001, 0.001]
    kv_levels: List[float] = [0.415, 11.0, 33.0]

    @validator("freq")
    def frequency_must_be_valid(cls, v):  # pylint: disable=no-self-argument
        if v not in [50, 60]:
            raise ValueError(f"Frequency must be either 50 or 60 and not {v}")
        return v


class TransformerKV(BaseModel):
    ht: confloat(ge=KV_MIN, le=KV_MAX) = 33.0
    lt: confloat(ge=KV_MIN, le=KV_MAX) = 11.0


class TransformerConnection(BaseModel):
    ht: Connection = Connection.delta
    lt: Connection = Connection.star_grounded


class DesignFactors(BaseModel):
    adj_factor: confloat(
        ge=MIN_ADJUSTMENT_FACTOR, le=MAX_ADJUSTMENT_FACTOR
    ) = 1.25
    planned_avg_annual_growth: confloat(
        ge=MIN_PERCENTAGE, le=MAX_PERCENTAGE
    ) = 2
    actual_avg_annual_growth: confloat(ge=MIN_PERCENTAGE, le=MAX_PERCENTAGE) = 4
    actual_years_in_operation: confloat(
        ge=MIN_YEAR_OPERATION, le=MAX_YEAR_OPERATION
    ) = 15
    planned_years_in_operation: confloat(
        ge=MIN_YEAR_OPERATION, le=MAX_YEAR_OPERATION
    ) = 10
    catalog_type: str = "ACSR"
    pf: confloat(le=MIN_POWER_FACTOR, ge=MAX_POWER_FACTOR) = 0.9
    voltage_drop: Union[float, None] = None
    catalog_type_lateral: Union[str, None] = "all"


class SubstationTransformer(BaseModel):
    div_func_coeff: list[float, float] = [0.3908524, 1.65180707]
    kv: TransformerKV = TransformerKV()
    phase: TransformerPhase = TransformerPhase()
    conn: TransformerConnection = TransformerConnection()
    design_factors: DesignFactors = DesignFactors()


class LoadPhase(BaseModel):
    method: LoadPhaseMethod = LoadPhaseMethod.random
    pct_single_phase: confloat(ge=MIN_PERCENTAGE, le=MAX_PERCENTAGE) = 100.0
    pct_two_phase: confloat(ge=MIN_PERCENTAGE, le=MAX_PERCENTAGE) = 0
    pct_three_phase: confloat(ge=MIN_PERCENTAGE, le=MAX_PERCENTAGE) = 0


class LoadKV(BaseModel):
    method: LoadKVMethod = LoadKVMethod.simple
    kv: confloat(ge=KV_MIN, le=KV_MAX) = 0.415


class LoadConnection(BaseModel):
    method: LoadConnectionMethod = LoadConnectionMethod.default


class LoadKW(BaseModel):
    method: LoadKWMethod = LoadKWMethod.piecewiselinear
    curve: List[list[float, float]] = [[0, 0], [10, 15.0], [20, 35], [50, 80]]


class LoadType(BaseModel):
    name: LoadTypeMethod = LoadTypeMethod.constantpowerfactor
    pf: confloat(le=MIN_POWER_FACTOR, ge=MAX_POWER_FACTOR) = 1.0


class Loads(BaseModel):
    phase: LoadPhase = LoadPhase()
    kv: LoadKV = LoadKV()
    conn: LoadConnection = LoadConnection()
    kw: LoadKW = LoadKW()
    type: LoadType = LoadType()


class DTMethod(BaseModel):
    name: DTMethodName = DTMethodName.clustering
    cluster_method: DTClusterMethod = DTClusterMethod.location_kmeans
    estimated_customers_per_transformer: conint(ge=20, le=300) = 100


class DistributionTransformers(BaseModel):
    method: DTMethod = DTMethod()
    div_func_coeff: list[float, float] = [0.3908524, 1.65180707]
    kv: TransformerKV = TransformerKV(ht=11.0, lt=0.415)
    phase: TransformerPhase = TransformerPhase()
    conn: TransformerConnection = TransformerConnection()
    design_factors: DesignFactors = DesignFactors()


class ConductorPhase(BaseModel):
    num_phase: conint(ge=1, le=3) = 3
    phase_type: Union[float, None] = None
    neutral_present: bool = False


class SecondaryConductorPhase(BaseModel):
    num_phase: conint(ge=1, le=3) = 3
    phase_type: Union[float, None] = None
    neutral_present: bool = False
    service_drop_neutral: bool = False


class ThreePhaseConductorConfiguration(BaseModel):
    height_of_top_conductor: confloat(ge=-9.0, le=20.0) = 9
    space_between_conductors: confloat(ge=0, le=20.0) = 0.4
    unit: str = "m"
    type: ConductorGeometry = ConductorGeometry.horizontal


class SinglePhaseConductorConfiguration(BaseModel):
    height_of_top_conductor: confloat(ge=-9.0, le=20.0) = 9
    unit: str = "m"
    type: ConductorGeometry = ConductorGeometry.horizontal


class PrimaryNetworkConfiguration(BaseModel):
    three_phase: ThreePhaseConductorConfiguration = (
        ThreePhaseConductorConfiguration()
    )


class SecondaryNetworkConfiguration(BaseModel):
    three_phase: ThreePhaseConductorConfiguration = (
        ThreePhaseConductorConfiguration()
    )
    single_phase: SinglePhaseConductorConfiguration = (
        SinglePhaseConductorConfiguration()
    )


class PrimaryNetwork(BaseModel):
    method: PrimaryNetworkMethod = PrimaryNetworkMethod.openstreet
    kv: confloat(ge=KV_MIN, le=KV_MAX) = 11.0
    max_pp_distance: confloat(
        le=MIN_POLE_TO_POLE_DISTANCE, ge=MAX_POLE_TO_POLE_DISTANCE
    ) = 100
    cond_type: ConductorType = ConductorType.overhead
    phase: ConductorPhase = ConductorPhase()
    configuration: PrimaryNetworkConfiguration = PrimaryNetworkConfiguration()
    design_factors: DesignFactors = DesignFactors(voltage_drop=2)


class SecondaryNetwork(BaseModel):
    kv: confloat(ge=KV_MIN, le=KV_MAX) = 0.415
    max_pp_distance: confloat(
        le=MIN_POLE_TO_POLE_DISTANCE, ge=MAX_POLE_TO_POLE_DISTANCE
    ) = 100
    cond_type: ConductorType = ConductorType.overhead
    phase: SecondaryConductorPhase = SecondaryConductorPhase()
    configuration: SecondaryNetworkConfiguration = (
        SecondaryNetworkConfiguration()
    )
    design_factors: DesignFactors = DesignFactors(voltage_drop=5)


class Exporter(BaseModel):
    type: str = "opendss"
    path: str = "."


class ConfigTemplate(BaseModel):
    location: Location = Location()
    div_func_coeff: list[float, float] = [0.3908524, 1.65180707]
    substation: Substation = Substation()
    substation_xfmr: SubstationTransformer = SubstationTransformer()
    loads: Loads = Loads()
    dist_xfmrs: DistributionTransformers = DistributionTransformers()
    primary_network: PrimaryNetwork = PrimaryNetwork()
    secondary_network: SecondaryNetwork = SecondaryNetwork()
    exporter: Exporter = Exporter()
