""" Exports a OpenDSS writer """

from cmath import phase
from attr import has
from exporter.base import BaseExporter
from abc import ABC, abstractmethod
from load import Load
from transformer import Transformer
from line_section import Line
from typing import List
from exceptions import FolderNotFoundError
import os
from enums import Phase, NumPhase
from constants import VALID_FREQUENCIES
from exceptions import UnsupportedFrequencyError


def remove_invalid_chars(name):
    """ Remove invalid OpenDSS charaters """

    name = str(name)
    for char in ['.', ' ', '!']:
        name = name.replace(char, '_')
    return name


class DSSWriter(ABC):
    """ Writer for generaing load.dss"""

    def __init__(self):
        """ Initialize the dss files written by the class as empty"""

        self.files = []
        self.coord_dict = {}

    def get_filenames(self):
        """ Returns the dss files exported by the class 
        assuming subclass will update this attribute
        """

        return self.files

    def write(self, folder_location: str):

        """ Includes basic feature of testing whether the directory exists 
        or not is extended by subclass"""

        if not os.path.exists(folder_location):
            raise FolderNotFoundError(folder_location)

    def get_coords(self):
        return self.coord_dict



class LoadWriter(DSSWriter):
    """Base load writer inherits from DSS writer"""

    def __init__(self, loads: List[Load], file_name: str):
        """ Provide list of load names and file name for 
            exporting the content """

        super().__init__()
        self.loads = loads
        self.file_name = file_name


class ConstantPowerFactorLoadWriter(LoadWriter):
    """ Constant Power Factor load writer inherits from Load writer"""

    def __init__(self, loads: List[Load], mapping_dict,file_name:str):
        super().__init__(loads, file_name)
        self.mapping_dict = mapping_dict

    def write(self, folder_location):
        super().write(folder_location)
        
        load_contents = []
        for load in self.loads:
            bus1 = f"{remove_invalid_chars(self.mapping_dict[load.name])}.{load.phase.value}"
            load_contents.append(
                f"new load.{remove_invalid_chars(load.name)} "+ \
                f"phases={load.num_phase.value} bus1={bus1} " + \
                f"kv={load.kv} kw={load.kw} pf={load.pf} " + \
                f"conn={load.conn_type.value}\n\n"
            )
            self.coord_dict[bus1.split('.')[0]] = (load.longitude, load.latitude)
        
        if load_contents:
            with open(os.path.join(folder_location, \
                self.file_name), "w") as f:
                f.writelines(load_contents)

            self.files.append(self.file_name)


class TransformerWriter(DSSWriter):
    """ Transformer writer inherits from DSS writer"""

    def __init__(self, transformers: List[Transformer], file_name: str):
        """ Provide list of transformer and file name"""

        super().__init__()
        self.transformers = transformers
        self.file_name = file_name
    

class TwoWindingSimpleTransformerWriter(TransformerWriter):
    """ Simple two winding trasformer writer"""
    
    def write(self, folder_location):
        super().write(folder_location)
        
        trans_contents = []
        for trans in self.transformers:
            bus = f"{remove_invalid_chars(trans.longitude)}_" + \
                    f"{remove_invalid_chars(trans.latitude)}"
            bus1 = f"{bus}_htnode.{trans.primary_phase.value}"
            bus2 = f"{bus}_ltnode.{trans.secondary_phase.value}"
            trans_contents.append(
                f"new transformer.{remove_invalid_chars(trans.name)} " + \
                f"phases={trans.num_phase.value} buses=[{bus1}, {bus2}] " + \
                f"conns=[{trans.primary_con.value}, {trans.secondary_con.value}] " + \
                f"kvs=[{trans.primary_kv}, {trans.secondary_kv}] " + \
                f"kvas=[{trans.kva}, {trans.kva}] xhl={trans.xhl} " + \
                f"%noloadloss={trans.pct_noloadloss} %r={trans.pct_r} leadlag=lead\n\n"
            )

            self.coord_dict[bus1.split('.')[0]] = (trans.longitude, trans.latitude)
            self.coord_dict[bus2.split('.')[0]] = (trans.longitude, trans.latitude)
        
        if trans_contents:
            with open(os.path.join(folder_location, \
                self.file_name), "w") as f:
                f.writelines(trans_contents)
            self.files.append(self.file_name)


class LineWriter(DSSWriter):
    """ Base line writer inherits from DSS writer """
    
    def __init__(self, lines: List[Line], file_name):
        """ Proivide list of line objects and file name"""
        
        super().__init__()
        self.lines = lines
        self.file_name = file_name


class GeometryBasedLineWriter(LineWriter):
    """ Geometry based line writer"""

    def __init__(self, lines: List[Line], line_file_name, 
        geometry_file_name, wire_file_name, cable_file_name):
        """ Provide list of line objects as well as some file names """

        super().__init__(lines, line_file_name)
        self.geometry_file_name = geometry_file_name
        self.wire_file_name = wire_file_name
        self.cable_file_name = cable_file_name

    def write(self, folder_location: str):
        super().write(folder_location)

        """ To keep the contents for parts of line segments """
        line_contents, geometry_contents, wire_contents, \
            cable_contents = [], [], [], []
        
        """ To keep track of geometry objects """
        geom_objects_dict= {}

        for line in self.lines:

            """ Check if the geom already exists in the object list """
            geom = line.geometry
            gk = geom.__class__

            if gk not in geom_objects_dict:
                geom_objects_dict[gk] =  []

            if geom not in geom_objects_dict[gk]:
                geom_objects_dict[gk].append(geom)
            else:
                geom = geom_objects_dict[gk][geom_objects_dict[gk].index(geom)]

            bus1 = f"{remove_invalid_chars(line.fromnode)}.{line.fromnode_phase.value}"
            bus2 = f"{remove_invalid_chars(line.tonode)}.{line.tonode_phase.value}"
            line_contents.append(
                f"new line.{remove_invalid_chars(line.name)} " + \
                f"bus1={bus1} " + \
                f"bus2={bus2} " + \
                f"length={line.length if line.length !=0 else 0.0001} geometry={geom.name} units={line.length_unit}\n\n"
            )

            self.coord_dict[bus1.split('.')[0]] = (line.fromnode.split('_')[0], line.fromnode.split('_')[1])
            self.coord_dict[bus2.split('.')[0]] = (line.tonode.split('_')[0], line.tonode.split('_')[1])
        
        geom_object_list = [obj for _, obj_arr in geom_objects_dict.items() for obj in obj_arr]

            
        """ Loop over all the geometries """

        """ To keep track of wire objects """
        wire_object_list, cable_object_list = [], []

        for geom in geom_object_list:

            """ Check if the geom already exists in the object list """

            if hasattr(geom, 'phase_wire'):
                wire_attr = 'wire'
                if geom.phase_wire in wire_object_list:
                    phase_cond = wire_object_list[wire_object_list.index(geom.phase_wire)]
                else:
                    phase_cond = geom.phase_wire 
                    wire_object_list.append(phase_cond)

                if hasattr(geom, 'neutral_wire'):
                    if geom.neutral_wire in wire_object_list:
                        neutral_wire = wire_object_list[wire_object_list.index(geom.neutral_wire)]
                    else:
                        neutral_wire = geom.neutral_wire 
                        wire_object_list.append(neutral_wire)
            else:
                wire_attr = 'cncable'
                if geom.phase_cable in cable_object_list:
                    phase_cond = cable_object_list[cable_object_list.index(geom.phase_cable)]
                else:
                    phase_cond = geom.phase_cable 
                    cable_object_list.append(phase_cond) 

            geom_x_array = geom.configuration.get_x_array()
            geom_h_array = geom.configuration.get_h_array()

            geom_content = f"new linegeometry.{geom.name} " + \
                f"nconds={geom.num_conds} nphases={geom.num_phase.value} " +\
                f"reduce=no\n"
        
            for id, items in enumerate(zip(geom_x_array, geom_h_array)):
                if id == len(geom_x_array)-1 and hasattr(geom, 'neutral_wire'):
                    geom_content += f"~ cond={id+1} {wire_attr}={neutral_wire.name} " + \
                        f"x={items[0]} h={items[1]} units={geom.configuration.unit}\n" 
                else:
                    geom_content += f"~ cond={id+1} {wire_attr}={phase_cond.name} " + \
                        f"x={items[0]} h={items[1]} units={geom.configuration.unit}\n" 
            geom_content += '\n' 
            geometry_contents.append(geom_content)

        """ Let's create wire and cables """
        for wire in wire_object_list:

            
            wire_contents.append(f"new wiredata.{remove_invalid_chars(wire.name)} " + \
                f"diam={wire.diam} gmrac={wire.gmrac} " + \
                f"gmrunits={wire.gmrunits} normamps={wire.normamps} " + \
                f"rac={wire.rac} runits={wire.runits} " + \
                f"radunits={wire.radunits}\n\n")
        
        for wire in cable_object_list:

                """ Define concentric cable """
                if not hasattr(wire, 'taplayer'):
                    cable_contents.append(f"new CNData.{remove_invalid_chars(wire.name)}\n"
                        f"~ runits={wire.runits} radunits={wire.radunits} gmrunits={wire.gmrunits}\n" +\
                        f"~ inslayer={wire.inslayer} diains={wire.diains} diacable={wire.diacable} epsr=2.3\n" + \
                        f"~ rac={wire.rac} gmrac={wire.gmrac} diam={wire.diam}\n" + \
                        f"~ rstrand={wire.rstrand} gmrstrand={wire.gmrstrand} diastrand={wire.diastrand} k={wire.k} normamps={wire.normamps}\n\n")

                else:
                    # TODO: Implement some thing for tap shielded cable
                    raise Exception(f"Writer for this type {wire} is not developed yet!")

        for file_, contents in zip([self.wire_file_name, self.cable_file_name, \
                 self.geometry_file_name, self.file_name], \
            [wire_contents, cable_contents, geometry_contents, line_contents]):
            if contents:
                with open(os.path.join(folder_location, file_), "w") as f:
                    f.writelines(contents)
                self.files.append(file_)


""" OpenDSS Exporter Class"""
class OpenDSSExporter(BaseExporter):

    def __init__(self,
        writers: List[DSSWriter],
        folder_location: str, 
        master_file_name: str,
        circuit_name: str,
        circuit_kv: float,
        circuit_freq: float,
        circuit_phase: Phase,
        circuit_num_phase: NumPhase,
        circuit_bus: str,
        circuit_z1: List[float],
        circuit_z0: List[float],
        kv_arrays: List[float]
    ):

        if circuit_freq not in VALID_FREQUENCIES:
            raise UnsupportedFrequencyError(circuit_freq)
        self.writers = writers
        self.folder_location = folder_location
        self.master_file_name = master_file_name
        self.circuit_name = circuit_name
        self.circuit_kv = circuit_kv
        self.circuit_freq = circuit_freq
        self.kv_arrays = kv_arrays
        self.circuit_phase = circuit_phase
        self.circuit_bus = circuit_bus
        self.circuit_num_phase = circuit_num_phase
        self.circuit_z1 = circuit_z1
        self.circuit_z0 = circuit_z0

        if not os.path.exists(self.folder_location):
            raise FolderNotFoundError(folder_location)

    
    def export(self):

        files = []
        coord_dict = {}
        for writer in self.writers:
            writer.write(self.folder_location)
            files += writer.get_filenames()
            coord_dict.update(writer.get_coords())
        
        coord_content = ''
        for key, vals in coord_dict.items():
            coord_content += f"{key}, {vals[0]}, {vals[1]}\n"
        
        with open(os.path.join(self.folder_location, 'buscoords.dss'), "w") as f:
            f.writelines(coord_content)


        master_file_content = f"clear\n\n" + \
            f"new circuit.{self.circuit_name} basekv={self.circuit_kv} " + \
            f"basefreq={self.circuit_freq} pu=1.0 phases={self.circuit_num_phase.value} " + \
            f"Z1={self.circuit_z1} Z0={self.circuit_z0} " + \
            f"bus1={remove_invalid_chars(self.circuit_bus)}.{self.circuit_phase.value} \n\n"


        for file in files:
            master_file_content += f"redirect {file}\n\n"

        

        master_file_content += f"set voltagebases={self.kv_arrays}\n\nCalcvoltagebases\n\n"
        master_file_content += f"Buscoords buscoords.dss\n\nsolve"

        with open(os.path.join(self.folder_location, self.master_file_name), "w") as f:
            f.writelines(master_file_content)

        

        


        


    

