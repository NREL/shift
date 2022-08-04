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

""" This module contains classes for representing
different type of power system loads.

Examples:

    >>> from shift.load import ConstantPowerLoad
    >>> load = ConstantPowerLoad()
    >>> load.name = "Load1"
    >>> load.latitude = 60.233
    >>> load.longitude = 23.455
    >>> load.phase = Phase.A
    >>> load.num_phase = NumPhase.SINGLE
    >>> load.conn_type = LoadConnection.STAR
    >>> load.kv = 12.7
    >>> load.kw = 4.8
    >>> load.kvar = 3.4
    >>> print(load)
"""

from abc import ABC

from shift.enums import Phase, NumPhase, LoadConnection
from shift.exceptions import (
    LatitudeNotInRangeError,
    LongitudeNotInRangeError,
    NegativeKVError,
    ZeroKVError,
    PowerFactorNotInRangeError,
)
from shift.constants import (
    MIN_LATITUDE,
    MAX_LATITUDE,
    MIN_LONGITUDE,
    MAX_LONGITUDE,
    MIN_POWER_FACTOR,
    MAX_POWER_FACTOR,
)


class Load(ABC):
    """Interface for single load point."""

    @property
    def name(self) -> str:
        """Name property of load"""
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        """Name setter method for a load"""
        self._name = name

    @property
    def latitude(self) -> float:
        """Latitude property where load is located"""
        return self._latitude

    @latitude.setter
    def latitude(self, latitude: float) -> None:
        """Latitude setter method for the load"""
        if latitude < MIN_LATITUDE or latitude > MAX_LATITUDE:
            raise LatitudeNotInRangeError(latitude)
        self._latitude = latitude

    @property
    def longitude(self) -> float:
        """Longitude property where load is located"""
        return self._longitude

    @longitude.setter
    def longitude(self, longitude: float) -> None:
        """Longitude setter method for the load"""
        if longitude < MIN_LONGITUDE or longitude > MAX_LONGITUDE:
            raise LongitudeNotInRangeError(longitude)
        self._longitude = longitude

    @property
    def phase(self) -> Phase:
        """Phase property where load is connected"""
        return self._phase

    @phase.setter
    def phase(self, phase: Phase) -> None:
        """Phase setter method for the load"""
        self._phase = phase

    @property
    def num_phase(self) -> NumPhase:
        """Number of phase property of the load"""
        return self._num_phase

    @num_phase.setter
    def num_phase(self, num_phase: NumPhase) -> None:
        """Number of phase setter method for the load"""
        self._num_phase = num_phase

    @property
    def conn_type(self) -> LoadConnection:
        """Connection type property of the load"""
        return self._conn_type

    @conn_type.setter
    def conn_type(self, connection: LoadConnection) -> None:
        """Abstract connection type setter method for the load"""
        self._conn_type = connection

    @property
    def kv(self) -> float:
        """kv property of the load"""
        return self._kv

    @kv.setter
    def kv(self, kv: float) -> None:
        """kv setter method for the load"""
        if kv < 0:
            raise NegativeKVError(kv)
        if kv == 0:
            raise ZeroKVError()
        self._kv = kv


class ConstantPowerLoad(Load):
    """Implementation for constant power load."""

    @property
    def kw(self) -> float:
        """kw property of the load"""
        return self._kw

    @kw.setter
    def kw(self, kw: float) -> None:
        """kw setter method for the load"""
        self._kw = kw

    @property
    def kvar(self) -> float:
        """kvar property of the load"""
        return self._kvar

    @kvar.setter
    def kvar(self, kvar: float) -> None:
        """kvar setter method for the load"""
        self._kvar = kvar

    def __repr__(self):
        return (
            f"ConstantPowerLoad(Name = {self._name}, Latitude ="
            + f" {self._latitude}, Longitude = {self._longitude},"
            + f" Phase = {self._phase} NumPhase = {self._num_phase},"
            + f" Connection Type = {self._conn_type}, kw = {self._kw},"
            + f" kvar = {self._kvar}, kv = {self._kv})"
        )


class ConstantPowerFactorLoad(Load):
    """Implementation for constant power factor load."""

    @property
    def kw(self) -> float:
        """kw property of the load"""
        return self._kw

    @kw.setter
    def kw(self, kw: float) -> None:
        """kw setter method for the load"""
        self._kw = kw

    @property
    def pf(self) -> float:
        """power factor setter method for the load"""
        return self._pf

    @pf.setter
    def pf(self, pf: float) -> None:
        """power factor setter method for the load"""
        if pf < MIN_POWER_FACTOR or pf > MAX_POWER_FACTOR:
            raise PowerFactorNotInRangeError(pf)
        self._pf = pf

    def __repr__(self):
        return (
            f"ConstantPowerFactorLoad(Name = {self._name},"
            + f" Latitude = {self._latitude}, Longitude = "
            + f"{self._longitude}, Phase = {self._phase} "
            + f"NumPhase = {self._num_phase}, Connection Type ="
            + f" {self._conn_type}, kw = {self._kw},"
            + f" pf = {self._pf}, kv = {self._kv})"
        )
