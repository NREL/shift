from abc import ABC
from enums import Phase, NumPhase, LoadConnection
from exceptions import LatitudeNotInRangeError, LongitudeNotInRangeError, NegativeKVError, ZeroKVError, PowerFactorNotInRangeError
from constants import (MIN_LATITUDE, MAX_LATITUDE, MIN_LONGITUDE, MAX_LONGITUDE, MIN_POWER_FACTOR, MAX_POWER_FACTOR)



""" Interface for base load representation """
class Load(ABC):

    """ Interface for single load point """
    @property
    def name(self) -> str:
        """ Name property of load"""
        return self._name

    @name.setter
    def name(self, name:str) -> None:
        """ Name setter method for a load"""
        self._name = name

    @property
    def latitude(self) -> float:
        """ Latitude property where load is located """
        return self._latitude

    @latitude.setter
    def latitude(self, latitude: float) -> None:
        """ Latitude setter method for the load"""
        if latitude < MIN_LATITUDE or latitude > MAX_LATITUDE:
            raise LatitudeNotInRangeError(latitude)
        self._latitude = latitude


    @property
    def longitude(self) -> float:
        """ Longitude property where load is located """
        return self._longitude
    
    @longitude.setter
    def longitude(self, longitude: float) -> None:
        """ Longitude setter method for the load"""
        if longitude < MIN_LONGITUDE or longitude > MAX_LONGITUDE:
            raise LongitudeNotInRangeError(longitude)
        self._longitude = longitude

    
    @property
    def phase(self) -> Phase:
        """ Phase property where load is connected """
        return self._phase
    
    @phase.setter
    def phase(self, phase: Phase) -> None:
        """ Phase setter method for the load """
        self._phase = phase
    

    @property
    def num_phase(self) -> NumPhase:
        """ Number of phase property of the load """
        return self._num_phase
    
    @num_phase.setter
    def num_phase(self, num_phase: NumPhase) -> None:
        """ Number of phase setter method for the load """
        self._num_phase = num_phase


    @property
    def conn_type(self) -> LoadConnection:
        """ Connection type property of the load """
        return self._conn_type
    
    @conn_type.setter
    def conn_type(self, connection: LoadConnection) -> None:
        """ Abstract connection type setter method for the load """
        self._conn_type = connection

    @property
    def kv(self) -> float:
        """ kv property of the load """
        return self._kv

    @kv.setter
    def kv(self, kv:float) -> None:
        """ kv setter method for the load """
        if kv < 0:
            raise NegativeKVError(kv)
        if kv == 0:
            raise ZeroKVError()
        self._kv = kv


""" Implementation for constant power load """
class ConstantPowerLoad(Load):

    @property
    def kw(self) -> float:
        """ kw property of the load """
        return self._kw

    @kw.setter
    def kw(self, kw: float) -> None: 
        """ kw setter method for the load """
        self._kw = kw
    

    @property
    def kvar(self) -> float:
        """ kvar property of the load """
        return self._kvar

    @kvar.setter
    def kvar(self, kvar: float) -> None:
        """ kvar setter method for the load """
        self._kvar = kvar

    def __repr__(self):
        return f"ConstantPowerLoad(Name = {self._name}, Latitude = {self._latitude}, Longitude = {self._longitude}, Phase = {self._phase} " + \
             f"NumPhase = {self._num_phase}, Connection Type = {self._conn_type}, kw = {self._kw}, kvar = {self._kvar}, kv = {self._kv})"


""" Implementation for constant power factor load """
class ConstantPowerFactorLoad(Load):
    
    @property
    def kw(self) -> float:
        return self._kw

    @kw.setter
    def kw(self, kw: float) -> None: 
        self._kw = kw
    
    @property
    def pf(self) -> float:
        return self._pf

    @pf.setter
    def pf(self, pf: float) -> None:
        if pf < MIN_POWER_FACTOR or pf > MAX_POWER_FACTOR:
            raise PowerFactorNotInRangeError(pf)
        self._pf = pf

    def __repr__(self):
        return f"ConstantPowerFactorLoad(Name = {self._name}, Latitude = {self._latitude}, Longitude = {self._longitude}, Phase = {self._phase} " + \
             f"NumPhase = {self._num_phase}, Connection Type = {self._conn_type}, kw = {self._kw}, pf = {self._pf}, kv = {self._kv})"


if __name__ == '__main__':

    load = ConstantPowerLoad()
    load.name = "Load1"
    load.latitude = 60.233
    load.longitude = 23.455
    load.phase = Phase.A
    load.num_phase = NumPhase.SINGLE
    load.conn_type = LoadConnection.STAR
    load.kv = 12.7
    load.kw = 4.8
    load.kvar = 3.4
    print(load)
