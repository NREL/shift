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

""" This module contains classes for representing transformer. """

from abc import ABC

from shift.exceptions import (
    LatitudeNotInRangeError,
    LongitudeNotInRangeError,
    PercentageNotInRangeError,
    NegativekVAError,
    NegativeKVError,
    ZeroKVError,
)
from shift.constants import (
    MIN_LATITUDE,
    MAX_LATITUDE,
    MIN_LONGITUDE,
    MAX_LONGITUDE,
    MIN_PERCENTAGE,
    MAX_PERCENTAGE,
)
from shift.enums import Phase, NumPhase, TransformerConnection


class Transformer(ABC):
    """Interface for base transformer representation"""

    @property
    def name(self) -> str:
        """Name of the transformer"""
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

    @property
    def latitude(self) -> float:
        """Latitude property where transformer is located"""
        return self._latitude

    @latitude.setter
    def latitude(self, latitude: float) -> None:
        """Latitude setter method for the transformer"""
        if latitude < MIN_LATITUDE or latitude > MAX_LATITUDE:
            raise LatitudeNotInRangeError(latitude)
        self._latitude = latitude

    @property
    def longitude(self) -> float:
        """Longitude property where transformer is located"""
        return self._longitude

    @longitude.setter
    def longitude(self, longitude: float) -> None:
        """Longitude setter method for the transformer"""
        if longitude < MIN_LONGITUDE or longitude > MAX_LONGITUDE:
            raise LongitudeNotInRangeError(longitude)
        self._longitude = longitude

    @property
    def num_phase(self) -> NumPhase:
        """Number of phase property for the transformer"""
        return self._num_phase

    @num_phase.setter
    def num_phase(self, num_phase: NumPhase) -> None:
        """Number of phase setter method for the transformer"""
        self._num_phase = num_phase

    @property
    def xhl(self) -> float:
        """Percentage reactance property for the transformer"""
        return self._xhl

    @xhl.setter
    def xhl(self, xhl: float) -> None:
        """Percentage reactance setter method for the transformer"""
        if xhl < MIN_PERCENTAGE or xhl > MAX_PERCENTAGE:
            raise PercentageNotInRangeError(xhl)
        self._xhl = xhl

    @property
    def pct_r(self) -> float:
        """Percentage resistance property for the transformer"""
        return self._pct_r

    @pct_r.setter
    def pct_r(self, r: float) -> None:
        """Percentage resistance setter method for the transformer"""
        if r < MIN_PERCENTAGE or r > MAX_PERCENTAGE:
            raise PercentageNotInRangeError(r)
        self._pct_r = r

    @property
    def pct_noloadloss(self) -> float:
        """Percentage no load loss property for the transformer"""
        return self._pct_noloadloss

    @pct_noloadloss.setter
    def pct_noloadloss(self, pct_nl_loss: float) -> None:
        """Percentage no load loss setter for the transformer"""
        if pct_nl_loss < MIN_PERCENTAGE or pct_nl_loss > MAX_PERCENTAGE:
            raise PercentageNotInRangeError(pct_nl_loss)
        self._pct_noloadloss = pct_nl_loss

    @property
    def kva(self) -> float:
        """Transformer kVA property"""
        return self._kva

    @kva.setter
    def kva(self, kva: float) -> None:
        """kVA setter method for transformer"""
        if kva < 0:
            raise NegativekVAError(kva)
        self._kva = kva

    @property
    def primary_kv(self) -> float:
        """Primary kV of the transformer"""
        return self._primary_kv

    @primary_kv.setter
    def primary_kv(self, kv: float) -> None:
        """Primary kv setter for transformer"""
        if kv < 0:
            raise NegativeKVError(kv)
        if kv == 0:
            raise ZeroKVError
        self._primary_kv = kv

    @property
    def secondary_kv(self) -> float:
        """Secondary kV of the transformer"""
        return self._secondary_kv

    @secondary_kv.setter
    def secondary_kv(self, kv: float) -> None:
        """Secondary kv setter for transformer"""
        if kv < 0:
            raise NegativeKVError(kv)
        if kv == 0:
            raise ZeroKVError
        self._secondary_kv = kv

    @property
    def primary_con(self) -> TransformerConnection:
        """Primary connection type of the transformer"""
        return self._primary_con

    @primary_con.setter
    def primary_con(self, conn: TransformerConnection) -> None:
        """Primary connection setter for transformer"""
        self._primary_con = conn

    @property
    def secondary_con(self) -> TransformerConnection:
        """Secondary connection type of the transformer"""
        return self._secondary_con

    @secondary_con.setter
    def secondary_con(self, conn: TransformerConnection) -> None:
        """Primary connection setter for transformer"""
        self._secondary_con = conn

    @property
    def primary_phase(self) -> Phase:
        """Primary phase of the transformer"""
        return self._primary_phase

    @primary_phase.setter
    def primary_phase(self, phase: Phase) -> None:
        """Primary phase setter for transformer"""
        self._primary_phase = phase

    @property
    def secondary_phase(self) -> Phase:
        """Secondary phase of the transformer"""
        return self._secondary_phase

    @secondary_phase.setter
    def secondary_phase(self, phase: Phase) -> None:
        """Secondary phase setter for transformer"""
        self._secondary_phase = phase

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(Name = {self._name}, "
            + f"Latitude = {self._latitude}, Longitude = {self._longitude}, "
            + f"NumPhase = {self._num_phase}, XHL = {self._xhl}, "
            + f"%R = {self._pct_r}, "
            + f"%no_load_loss = {self._pct_noloadloss}, "
            + f"Primary Phase = {self._primary_phase}, Secondary Phase"
            + f" = {self._secondary_phase} "
            + f"kVA = {self._kva}, Primary kV = {self._primary_kv},"
            + f"Secondary kV = {self._secondary_kv}, Primary Conn ="
            + f" {self._primary_con}, Secondary Conn = {self._secondary_con}"
        )
