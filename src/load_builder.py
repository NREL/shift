
from abc import ABC, abstractmethod
import osmnx as ox
import pandas as pd
from geometry import BuildingGeometry, Geometry, SimpleLoadGeometriesFromCSV
from load import ConstantPowerFactorLoad
from utils import get_point_from_curve
import random
from typing import List
from load import Load
from exceptions import PercentageSumNotHundred, NegativeKVError, ZeroKVError
from enums import Phase, NumPhase, LoadConnection
import math


class BuildingAreaToConsumptionConverter(ABC):
    
    @abstractmethod
    def convert(self, area: float) -> float:
        pass

class PiecewiseBuildingAreaToConsumptionConverter(BuildingAreaToConsumptionConverter):
    
    def __init__(self, area_to_kw_curve: list):
        self.curve = area_to_kw_curve

    def convert(self, area:float) -> float:
        return get_point_from_curve(self.curve, area)

class ProportionalBuildingAreaToConsumptionConverter(BuildingAreaToConsumptionConverter):
    
    def __init__(self, min_kw, max_kw, max_area, min_area):
        
        self.min_kw = min_kw
        self.max_kw = max_kw
        self.max_area = max_area
        self.min_area = min_area

        if self.min_kw >= self.max_kw:
            raise Exception(f"Min kW  {min_kw} is greater than or equal to Max kW {max_kw}")

    def convert(self, area: float) -> float:
        
        if self.max_area !=0:
            kw = self.min_kw + (self.max_kw - self.min_kw)*(area- self.min_area)/(self.max_area - self.min_area) 
        else:
            kws = self.min_kw

        return kws

class PhaseAllocator(ABC):

    @abstractmethod
    def get_phase(self):
        pass

    @abstractmethod
    def get_num_phase(self):
        pass


class RandomPhaseAllocator(PhaseAllocator):

    def __init__(self, 
                    pct_single_phases: float,
                    pct_two_phases: float,
                    pct_three_phases: float,
                    geometries: List[Geometry]
                    ):

        self.pct_single_phases = pct_single_phases
        self.pct_two_phases = pct_two_phases
        self.pct_three_phases = pct_three_phases
        self.geometries = geometries

        if pct_single_phases + pct_two_phases + pct_three_phases != 100:
            raise PercentageSumNotHundred(pct_single_phases + pct_two_phases + pct_three_phases)

        random.shuffle(self.geometries)

        
        three_phase_geometries = self.geometries[:int(len(self.geometries)*self.pct_three_phases/100)]
        self.geometry_to_phase = { g : Phase.ABCN for g in three_phase_geometries}
        self.geometry_to_numphase = { g : NumPhase.THREE for g in three_phase_geometries}

        single_phases = [Phase.AN, Phase.BN, Phase.CN]
        two_phases = [Phase.AB, Phase.BC, Phase.CA]

        two_phase_geometries = self.geometries[int(len(self.geometries)*self.pct_three_phases/100):int(len(self.geometries)*self.pct_two_phases/100)]
        self.geometry_to_phase.update({g : random.choice(two_phases) for g in two_phase_geometries})
        self.geometry_to_numphase.update({ g : NumPhase.TWO for g in two_phase_geometries})

        single_phase_geometries = [g for g in self.geometries if g not in self.geometry_to_phase]
        self.geometry_to_phase.update({g : random.choice(single_phases) for g in single_phase_geometries})
        self.geometry_to_numphase.update({ g : NumPhase.SINGLE for g in single_phase_geometries})


    def get_phase(self, geometry: Geometry):
        return self.geometry_to_phase[geometry]

    def get_num_phase(self, geometry: Geometry):
        return self.geometry_to_numphase[geometry]

class VoltageSetter(ABC):

    @abstractmethod
    def get_kv(self, load: Load) -> float:
        pass


class SimpleVoltageSetter:

    def __init__(self, line_line_voltage: float):

        self.line_to_line_voltage = line_line_voltage
        if self.line_to_line_voltage < 0:
            raise NegativeKVError(self.line_to_line_voltage)

        if self.line_to_line_voltage == 0:
            raise ZeroKVError()

        self.voltage_dict = {
            NumPhase.SINGLE : round(self.line_to_line_voltage/math.sqrt(3),3),
            NumPhase.TWO : self.line_to_line_voltage,
            NumPhase.THREE: self.line_to_line_voltage
        }

    def get_kv(self, load: Load):
        return self.voltage_dict[load.num_phase]


class ConnSetter(ABC):

    @abstractmethod
    def get_conn(self, load: Load) -> float:
        pass


class DefaultConnSetter(ConnSetter):

    def get_conn(self, load: Load):
        return LoadConnection.DELTA if load.num_phase == NumPhase.TWO else LoadConnection.STAR


""" Interface for getting list of all loads"""
class LoadBuilder(ABC):

    @abstractmethod
    def set_name_and_location(self):
        pass

    @abstractmethod
    def set_power_data(self):
        pass

    @abstractmethod
    def set_phase_data(self):
        pass

    @abstractmethod
    def set_kv_and_conn(self):
        pass


""" Base implementation for geometry based load builder """
class GeometryLoadBuilder(LoadBuilder):

    def __init__(self,
                geometry: Geometry,
                phaseallocator: PhaseAllocator,
                kv_setter: VoltageSetter,
                conn_setter: ConnSetter,
                load: Load):

        self.geometry = geometry
        self.load = load
        self.phase_allocator = phaseallocator
        self.kvsetter = kv_setter
        self.connsetter = conn_setter
        
    def set_name_and_location(self):
        self.load.name = f"{self.geometry.longitude}_{self.geometry.latitude}_load"
        self.load.latitude = self.geometry.latitude
        self.load.longitude = self.geometry.longitude

    @abstractmethod
    def set_power_data(self):
        pass

    def set_phase_data(self):
        self.load.phase = self.phase_allocator.get_phase(self.geometry)
        self.load.num_phase = self.phase_allocator.get_num_phase(self.geometry)

    def set_kv_and_conn(self):
        self.load.kv = self.kvsetter.get_kv(self.load)
        self.load.conn_type = self.connsetter.get_conn(self.load)


""" Concerete implementation for building constant power factor type load from geometry object"""
class ConstantPowerFactorBuildingGeometryLoadBuilder(GeometryLoadBuilder):

    def __init__(self, 
                geometry: Geometry,
                phaseallocator: PhaseAllocator,
                area_converter: BuildingAreaToConsumptionConverter,
                kv_setter: VoltageSetter,
                conn_setter: ConnSetter,
                power_factor: float
                ):
 
            super().__init__(geometry, 
                phaseallocator,
                kv_setter,
                conn_setter,
                ConstantPowerFactorLoad())
            self.power_factor = power_factor
            self.area_converter = area_converter
            
    def set_power_data(self):
        self.load.pf = self.power_factor
        self.load.kw = self.area_converter.convert(self.geometry.area)

""" Concerete implementation for building constant power factor type load from simple load point geometry object"""
class ConstantPowerFactorSimpleLoadGeometryLoadBuilder(GeometryLoadBuilder):

    def __init__(self, 
                geometry: Geometry,
                phaseallocator: PhaseAllocator,
                kv_setter: VoltageSetter,
                conn_setter: ConnSetter,
                power_factor: float
                ):
 
            super().__init__(geometry, 
                phaseallocator,
                kv_setter,
                conn_setter,
                ConstantPowerFactorLoad())
            self.power_factor = power_factor
            
    def set_power_data(self):
        self.load.pf = self.power_factor
        self.load.kw = self.geometry.kw
        
      
""" Director for building loads"""
class LoadBuilderEngineer:

    def __init__(self, builder: LoadBuilder):

        self.builder = builder
        self.builder.set_name_and_location()
        self.builder.set_power_data()
        self.builder.set_phase_data()
        self.builder.set_kv_and_conn()

    def get_load(self):
        return self.builder.load


if __name__ == '__main__':

    # g1 = BuildingGeometry()
    # g1.latitude = 56.567
    # g1.longitude = 67.8889
    # g1.area = 2

    # g2 = BuildingGeometry()
    # g2.latitude = 56.567
    # g2.longitude = 67.8889
    # g2.area = 2
    
    # builder = ConstantPowerFactorBuildingGeometryLoadBuilder(
    #     g1,
    #     RandomPhaseAllocator(50, 0, 50, [g1,g2]),
    #     ProportionalBuildingAreaToConsumptionConverter(2,5,0,10),
    #     SimpleVoltageSetter(13.2),
    #     DefaultConnSetter(),
    #     1.0
    # )

    # b = LoadBuilderEngineer(builder)
    # print(b.get_load())

    g = SimpleLoadGeometriesFromCSV(r'C:\Users\KDUWADI\Desktop\NREL_Projects\ciff_track_2\data\grp_customers_reduced.csv')
    geometries = g.get_geometries()
    rpa = RandomPhaseAllocator(100, 0, 0, geometries)
    vs = SimpleVoltageSetter(13.2)
    cs = DefaultConnSetter()

    loads = []
    for g in geometries:
        builder = ConstantPowerFactorSimpleLoadGeometryLoadBuilder(g,rpa,vs,cs,1.0)
        b = LoadBuilderEngineer(builder)
        loads.append(b.get_load())

    print(loads[:10])