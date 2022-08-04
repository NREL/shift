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

""" Module for handling all the enumerators through out the package. """

from enum import Enum


class Phase(Enum):
    """Enumeration class for representing power ssystem phase."""

    A = "1"
    B = "2"
    C = "3"
    AN = "1.0"
    BN = "2.0"
    CN = "3.0"
    AB = "1.2"
    BA = "2.1"
    BC = "2.3"
    CB = "3.2"
    AC = "1.3"
    CA = "3.1"
    ABC = "1.2.3"
    ABCN = "1.2.3.0"


class NumPhase(Enum):
    """Enumeration class for representing number of phases in power system."""

    SINGLE = 1
    TWO = 2
    THREE = 3


class LoadConnection(Enum):
    """Enumeration class for representing load
    connection type in power system."""

    STAR = "wye"
    DELTA = "delta"


class TransformerConnection(Enum):
    """Enumeration class for representing transformer
    connection type in power system."""

    STAR = "Wye"
    DELTA = "Delta"


class NetworkAsset(Enum):
    """Enumeration class for representing different
    network assets in power system."""

    LOAD = "load"
    LINE = "line"
    DISTXFMR = "distribution_transformer"
    HTNODE = "ht_node"
    HTLINE = "ht_line"
    LTNODE = "lt_node"
    LTLINE = "lt_line"


class ConductorType(Enum):
    """Enumeration class for representing conductor type in power system"""

    OVERHEAD = "overhead"
    UNDERGROUND_CONCENTRIC = "underground"


class GeometryConfiguration(Enum):
    HORIZONTAL = "horizontal"
