
from abc import ABC, abstractmethod
from types import TracebackType
from exceptions import (NegativeLineLengthError, InvalidLengthUnitError, 
    NegativeDiameterError, NegativeGMRError, NegativeResistanceError,
    NegativeAmpacityError, NegativeStrandsError)
from constants import VALID_LENGTH_UNITS
from enums import NumPhase, Phase

class Wire:
    
    @property
    def name(self) -> str:
        """ Name property of a wire"""
        return self._name


    @name.setter
    def name(self, name: str) -> None:
        """ Name setter method of a wire """
        self._name = name

    @property
    def runits(self) -> str:
        """ Unit for reistance property of a wire"""
        return self._runits


    @runits.setter
    def runits(self, unit: str) -> None:
        """ runits setter method for a wire"""
        if unit not in VALID_LENGTH_UNITS:
            raise InvalidLengthUnitError(unit)
        self._runits = unit 

    @property
    def gmrunits(self) -> str:
        """ gmrunits for diamater property for a wire"""
        return self._gmrunits


    @gmrunits.setter
    def gmrunits(self, unit: str) -> None:
        """ gmrunits setter method for a wire"""
        if unit not in VALID_LENGTH_UNITS:
            raise InvalidLengthUnitError(unit)
        self._gmrunits = unit  

    @property
    def radunits(self) -> str:
        """ Units for diamater property for a wire"""
        return self._radunits


    @radunits.setter
    def radunits(self, unit: str) -> None:
        """ radunits setter method for a wire"""
        if unit not in VALID_LENGTH_UNITS:
            raise InvalidLengthUnitError(unit)
        self._radunits = unit

    @property
    def rac(self) -> float:
        """ AC resistance property for a wire"""
        return self._rac


    @rac.setter
    def rac(self, r: float) -> None:
        """ AC resistance property setter method for a wire"""
        if r <0:
            raise NegativeResistanceError(r) 
        self._rac = r

    @property
    def diam(self) -> float:
        """ Diameter property of a wire"""
        return self._diam


    @diam.setter
    def diam(self, diameter: float) -> None:
        """ Diameter setter method for a wire"""
        if diameter < 0:
            raise NegativeDiameterError(diameter)
        self._diam = diameter


    @property
    def gmrac(self) -> float:
        """ gmrac property of a wire"""
        return self._gmrac


    @gmrac.setter
    def gmrac(self, gmr: float) -> None:
        """ gmrac setter method for a wire"""
        if gmr <0:
            raise NegativeGMRError(gmr) 
        self._gmrac = gmr
    
    @property
    def normamps(self) -> float:
        """ Normal ampacity property of a wire"""
        return self._normamps


    @normamps.setter
    def normamps(self, current: float) -> None:
        """ AC resistance property setter method for a wire"""
        if current <0:
            raise NegativeAmpacityError(current) 
        self._normamps = current

    def __eq__(self, other):

        if (self.name == other.name and self.runits == other.runits \
            and self.gmrunits == other.gmrunits and self.radunits == other.radunits \
            and self.rac == other.rac and self.diam == other.diam \
            and self.gmrac == other.gmrac and self.normamps == other.normamps):
            return True
        else:
            False

    def __repr__(self):
        return f"{self.__class__.__name__}(Name = {self._name}, Resistance unit = {self._runits}, GMR unit = {self._gmrunits}, Radius unit = {self._radunits}" + \
            f", AC resistance (ohm per) = {self._rac}, Diameter = {self._diam}, GMR AC = {self._gmrac}, Ampacity = {self._normamps})"



class Cable(Wire):
    """ Interface for cable data """

    @property
    def inslayer(self) -> float:
        """  Thickness of insulation property of a cable"""
        return self._inslayer


    @inslayer.setter
    def inslayer(self, diameter: float) -> None:
        """ Insulation thickness setter method for a cable"""
        if diameter < 0:
            raise NegativeDiameterError(diameter)
        self._inslayer = diameter

    
    @property
    def diains(self) -> float:
        """  Diameter over insulation property of a cable"""
        return self._diains


    @diains.setter
    def diains(self, diameter: float) -> None:
        """ Diameter over insulation setter method for a cable"""
        if diameter < 0:
            raise NegativeDiameterError(diameter)
        self._diains = diameter


    @property
    def diacable(self) -> float:
        """  Diameter of cable property of a cable"""
        return self._diacable


    @diacable.setter
    def diacable(self, diameter: float) -> None:
        """ Diameter of cable setter method for a cable"""
        if diameter < 0:
            raise NegativeDiameterError(diameter)
        self._diacable = diameter

    @property
    def rstrand(self) -> float:
        """ Resistance of neutral strand property for a cable"""
        return self._rstrand


    @rstrand.setter
    def rstrand(self, r: float) -> None:
        """ Resistance of neutral strand property setter method for a wire"""
        if r <0:
            raise NegativeResistanceError(r) 
        self._rstrand = r


    @property
    def gmrstrand(self) -> float:
        """ gmrac of neutral strand property of a wire"""
        return self._gmrstrand


    @gmrstrand.setter
    def gmrstrand(self, gmr: float) -> None:
        """ gmrac of neutral strand setter method for a wire"""
        if gmr <0:
            raise NegativeGMRError(gmr) 
        self._gmrstrand = gmr

    @property
    def diastrand(self) -> float:
        """  Diameter of neutral strand property of a cable"""
        return self._diastrand


    @diastrand.setter
    def diastrand(self, diameter: float) -> None:
        """ Diameter of neutral strand setter method for a cable"""
        if diameter < 0:
            raise NegativeDiameterError(diameter)
        self._diastrand = diameter

    @property
    def k(self) -> int:
        """  Number of neutral strands property of a cable"""
        return self._k


    @k.setter
    def k(self, num_of_strand: int) -> None:
        """ Number of neutral strands setter method for a cable"""
        if num_of_strand < 0:
            raise NegativeStrandsError(num_of_strand)
        self._k = num_of_strand

    def __eq__(self, other):

        if (super().__eq__(other) and self.inslayer == other.inslayer \
            and self.diains == other.diains and self.diacable == other.diacable and self.rstrand == other.rstrand \
            and self.gmrstrand == other.gmrstrand and self.diastrand == other.diastrand and self.k == other.k):
            return True
        else:
            False

    def __repr__(self):
        repr = super().__repr__()
        return f"{self.__class__.__name__}({repr.split('(')[1].split(')')[0]}, Insulation thickness = {self._inslayer}, Diameter over insulation = {self._diains}" +\
            f" Diameter of cable = {self._diacable}, Neutral strand resistance (ohm per) = {self._rstrand}, Neutral strand GMR = {self._gmrstrand}" + \
                f"Neutral strand diameter = {self._diastrand}, Number of neutral strands = {self._k})"


class LineGeometryConfiguration(ABC):
    """ Interface for line """

    @property
    def unit(self) -> str:
        """ Unit property for configuration """
        return self._unit


    @unit.setter
    def unit(self, unit_: str) -> None:
        """ Name setter method for a line geometry """
        if unit_ not in VALID_LENGTH_UNITS:
            raise InvalidLengthUnitError(unit_)
        self._unit = unit_

    @abstractmethod
    def get_x_array(self) -> list:
        pass

    @abstractmethod
    def get_h_array(self) -> list:
        pass

    def __eq__(self, other):

        if (self.unit == other.unit and self.get_x_array() == other.get_x_array() \
            and self.get_h_array() == other.get_h_array()):
            return True
        else:
            return False

class HorizontalSinglePhaseConfiguration(LineGeometryConfiguration):

    def __init__(self, height_of_conductor, unit):

        self.unit = unit
        self.height_of_conductor = height_of_conductor

    def get_x_array(self):
        return [0]

    def get_h_array(self) -> list:
        return [self.height_of_conductor]


class HorizontalSinglePhaseNeutralConfiguration(LineGeometryConfiguration):

    def __init__(self, height_of_conductor, separation_between_conductor, unit):

        self.unit = unit
        self.height_of_conductor = height_of_conductor
        self.separation_between_conductor = separation_between_conductor

    def get_x_array(self):
        return [-self.separation_between_conductor/2, self.separation_between_conductor/2]

    def get_h_array(self) -> list:
        return [self.height_of_conductor, self.height_of_conductor]



class HorizontalThreePhaseConfiguration(LineGeometryConfiguration):

    def __init__(self, height_of_conductor, separation_between_conductor, unit):

        self.unit = unit
        self.height_of_conductor = height_of_conductor
        self.separation_between_conductor = separation_between_conductor

    def get_x_array(self):
        return [-self.separation_between_conductor, 0, self.separation_between_conductor]

    def get_h_array(self) -> list:
        return [self.height_of_conductor, self.height_of_conductor, self.height_of_conductor]


class HorizontalThreePhaseNeutralConfiguration(LineGeometryConfiguration):

    def __init__(self, 
                    height_of_conductor, 
                    separation_between_conductor,  
                    height_of_neutral_conductor
                    ,unit):

        self.unit = unit
        self.height_of_conductor = height_of_conductor
        self.separation_between_conductor = separation_between_conductor
        self.height_of_neutral_conductor = height_of_neutral_conductor

    def get_x_array(self):
        return [-self.separation_between_conductor, 0, self.separation_between_conductor, 0]

    def get_h_array(self) -> list:
        return [self.height_of_conductor, self.height_of_conductor, self.height_of_conductor, self.height_of_neutral_conductor]



class LineGeometry(ABC):
    """ Interface for line geometry"""
    @property
    def name(self) -> str:
        """ Name property of a line geometry"""
        return self._name


    @name.setter
    def name(self, name: str) -> None:
        """ Name setter method for a line geometry """
        self._name = name

    @property
    def num_phase(self) -> NumPhase:
        """ Number of phase property of the line geometry """
        return self._num_phase

    @num_phase.setter
    def num_phase(self, num_phase : NumPhase) -> None:
        """ Number of phase setter method for a line geometry """
        self._num_phase = num_phase

    @property
    def num_conds(self) -> int:
        """ Number of conductors property of the line geometry """
        return self._num_conds

    @num_conds.setter
    def num_conds(self, num_of_conds : int) -> None:
        """ Number of conductors setter method for a line geometry """
        self._num_conds = num_of_conds 

    @property
    def configuration(self) -> LineGeometryConfiguration:
        """ Phase wire property of a line geometry"""
        return self._configuration

    @configuration.setter
    def configuration(self, configuration : LineGeometryConfiguration) -> None:
        """ Phase wire setter method for a line geometry """
        self._configuration = configuration

    def __eq__(self, other):

        if (self.num_phase == other.num_phase and self.num_conds == other.num_conds \
            and self.configuration == other.configuration):
            return True
        else:
            False


    def __repr__(self):
        return f"{self.__class__.__name__}(Name = {self._name}, NumPhase = {self._num_phase}, Number of conductors = {self._num_conds}, Configuration = {self._configuration})"


class OverheadLineGeometry(LineGeometry):
    """ Interface for overhead three phase line geometry"""

    @property
    def phase_wire(self) -> Wire:
        """ Phase wire property of a line geometry"""
        return self._phase_wire

    @phase_wire.setter
    def phase_wire(self, wire : Wire) -> None:
        """ Phase wire setter method for a line geometry """
        self._phase_wire = wire 

    def __eq__(self, other):
        
        if super().__eq__(other) and self.phase_wire == other.phase_wire:
            return True
        else:
            False

    def __repr__(self):
        repr = super().__repr__()
        return f"{self.__class__.__name__}({repr.split('(')[1].split(')')[0]}, Phase wire = {self._phase_wire})"

class OverheadLinewithNeutralGeometry(OverheadLineGeometry):
    
    @property
    def neutral_wire(self) -> str:
        """ Neutral wire property of a line geometry"""
        return self._neutral_wire

    @neutral_wire.setter
    def neutral_wire(self, wire : Wire) -> None:
        """ Neutral wire setter method for a line geometry """
        self._neutral_wire = wire 

    def __eq__(self, other):

        if super().__eq__(other) and self.neutral_wire == other.neutral_wire:
            return True
        else:
            False

    def __repr__(self):
        repr = super().__repr__()
        return f"{self.__class__.__name__}({repr.split('(')[1].split(')')[0]}, Neutral wire = {self._neutral_wire})"


class UndergroundLineGeometry(LineGeometry):
    """ Interface for underground three phase line geometry"""

    @property
    def phase_cable(self) -> Cable:
        """ Phase cable property of a line geometry"""
        return self._phase_cable

    @phase_cable.setter
    def phase_cable(self, cable : Cable) -> None:
        """ Phase cable setter method for a line geometry """
        self._phase_cable = cable

    def __eq__(self, other):

        if super().__eq__(other) and self.phase_cable == other.phase_cable:
            return True
        else:
            False

    def __repr__(self):
        repr = super().__repr__()
        return f"{self.__class__.__name__}({repr.split('(')[1].split(')')[0]}, Phase cable = {self._phase_cable})"


""" Interface for line section representation"""

class Line(ABC):

    @property
    def name(self) -> str:
        """ Name property of a line element"""
        return self._name


    @name.setter
    def name(self, name: str) -> None:
        """ Name setter method for a line element """
        self._name = name

    
    @property
    def fromnode(self) -> str:
        """ From node property of a line element"""
        return self._fromnode

    @fromnode.setter
    def fromnode(self, node: str):
        """ From node setter method for a line element"""
        self._fromnode = node

    @property
    def tonode(self) -> str:
        """ To node property of a line element"""
        return self._tonode

    @tonode.setter
    def tonode(self, node: str):
        """ To node setter method for a line element"""
        self._tonode = node

    @property
    def length(self) -> float:
        """ Length property of a line element"""
        return self._length

    @length.setter
    def length(self, length: float):
        """ Length setter method for a line element"""
        if length <0:
            raise NegativeLineLengthError(length)
        self._length = length

    @property
    def length_unit(self) -> str:
        """ Length unit property of a line element"""
        return self._length_unit

    @length_unit.setter
    def length_unit(self, unit: str):
        """ Length setter method for a line element"""
        if unit not in VALID_LENGTH_UNITS:
            raise InvalidLengthUnitError(unit)
        self._length_unit = unit

    @property
    def num_phase(self) -> NumPhase:
        """ Number of phase property of the line element """
        return self._num_phase
    
    @num_phase.setter
    def num_phase(self, num_phase: NumPhase) -> None:
        """ Number of phase setter method for the line element """
        self._num_phase = num_phase

    @property
    def fromnode_phase(self) -> Phase:
        """ Phase property of the line element """
        return self._fromnode_phase
    
    @fromnode_phase.setter
    def fromnode_phase(self, phase: Phase) -> None:
        """ Phase setter method for the line element """
        self._fromnode_phase = phase

    @property
    def tonode_phase(self) -> Phase:
        """ Phase property of the line element """
        return self._tonode_phase
    
    @tonode_phase.setter
    def tonode_phase(self, phase: Phase) -> None:
        """ Phase setter method for the line element """
        self._tonode_phase = phase


class GeometryBasedLine(Line):

    @property
    def geometry(self) -> LineGeometry:
        """ Geometry of the line element """
        return self._geometry
    
    @geometry.setter
    def geometry(self, geometry: LineGeometry) -> None:
        """ Geometry setter method for the line element """
        self._geometry = geometry

    def __repr__(self):
        return f"{self.__class__.__name__}(Name = {self._name}, FromNode = {self._fromnode}, ToNode = {self._tonode}, Length = {self._length} " + \
             f"NumPhase = {self._num_phase}, Length unit = {self._length_unit}, Geometry = {self._geometry})"

