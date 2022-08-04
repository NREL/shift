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

""" Module for storing constants used through out the package. """

import os

from shift.enums import NetworkAsset


MIN_LATITUDE = -90
MAX_LATITUDE = 90
MIN_LONGITUDE = -180
MAX_LONGITUDE = 180
MAX_POWER_FACTOR = 1.0
MIN_POWER_FACTOR = -1.0
MIN_ZOOM_LEVEL = 0
MAX_ZOOM_LEVEL = 23
MIN_PERCENTAGE = 0
MAX_PERCENTAGE = 100
MAX_KMEANS_LOOP = 1000
MIN_NUM_CLUSTER = 2
MIN_ADJUSTMENT_FACTOR = 0.5
MAX_ADJUSTMENT_FACTOR = 2.0
KV_MIN = 0.1
KV_MAX = 1000
KVA_MIN = 0
KVA_MAX = 100000000
MIN_YEAR_OPERATION = 1
MAX_YEAR_OPERATION = 100
MIN_POLE_TO_POLE_DISTANCE = 10  # meter
MAX_POLE_TO_POLE_DISTANCE = 1000  # meter
VALID_LENGTH_UNITS = ["mi", "kft", "km", "m", "ft", "in", "cm"]
LENGTH_CONVERTER_TO_CM = {
    "mi": 160934,
    "kft": 30480,
    "km": 100000,
    "m": 100,
    "ft": 30.48,
    "in": 2.54,
    "cm": 1,
}
VALID_FREQUENCIES = [50, 60]

OVERHEAD_CONDUCTOR_CATALOG_FILE = os.path.join(
    os.path.dirname(__file__), "catalogs/overhead_conductors.xlsx"
)

UG_CONCENTRIC_CABLE_CATALOG_FILE = os.path.join(
    os.path.dirname(__file__), "catalogs/concentric_neutral_ug_cables.xlsx"
)

TRANSFORMER_CATALOG_FILE = os.path.join(
    os.path.dirname(__file__), "catalogs/transformer.xlsx"
)


MAP_STYLES = [
    "white-bg",
    "open-street-map",
    "carto-positron",
    "carto-darkmatter",
    "stamen-terrain",
    "stamen-toner",
    "stamen-watercolor",
    "basic",
    "streets",
    "outdoors",
    "light",
    "dark",
    "satellite",
    "satellite-streets",
]

SIMPLELOADGEOMETRY_SCHEMA = {
    "latitude": {"type": "float", "min": MIN_LATITUDE, "max": MAX_LATITUDE},
    "longitude": {"type": "float", "min": MIN_LONGITUDE, "max": MAX_LONGITUDE},
    "kw": {"type": "float"},
}

TRANSFORMER_CATALAOG_SCHEMA = {
    "kva": {"type": "float", "min": KVA_MIN, "max": KVA_MAX},
    "ht_kv": {"type": "float", "min": KV_MIN, "max": KV_MAX},
    "lt_kv": {"type": "float", "min": KV_MIN, "max": KV_MAX},
    "type": {"type": "string"},
    "percentage_resistance": {"type": "float", "min": 0, "max": 100},
    "percentage_reactance": {"type": "float", "min": 0, "max": 100},
    "percentage_no_load_loss": {"type": "float", "min": 0, "max": 100},
}


OVERHEAD_CONDUCTOR_CATALAOG_SCHEMA = {
    "name": {"type": "string"},
    "diameter": {"type": "float", "min": 0},
    "diameterunit": {"type": "string", "allowed": VALID_LENGTH_UNITS},
    "gmrac": {"type": "float", "min": 0},
    "gmrunit": {"type": "string", "allowed": VALID_LENGTH_UNITS},
    "ampacity": {"type": "float", "min": 0},
    "rac": {"type": "float", "min": 0},
    "runit": {"type": "string", "allowed": VALID_LENGTH_UNITS},
    "material": {"type": "string"},
}

UNDERGROUND_CONCENTRIC_CABLE_CATALOG_SCHEMA = {
    "name": {"type": "string"},
    "diastrand": {"type": "float", "min": 0},
    "inslayer": {"type": "float", "min": 0},
    "diam": {"type": "float", "min": 0},
    "diacable": {"type": "float", "min": 0},
    "k": {"type": "integer", "min": 1},
    "diains": {"type": "float", "min": 0},
    "gmrac": {"type": "float", "min": 0},
    "gmrunit": {"type": "string", "allowed": VALID_LENGTH_UNITS},
    "rstrand": {"type": "float", "min": 0},
    "ampacity": {"type": "float", "min": 0},
    "rac": {"type": "float", "min": 0},
    "runit": {"type": "string", "allowed": VALID_LENGTH_UNITS},
    "radunits": {"type": "string", "allowed": VALID_LENGTH_UNITS},
    "gmrstrand": {"type": "float", "min": 0},
    "material": {"type": "string"},
    "kV": {"type": "float", "min": 0},
    "neutral_type": {"type": "string"},
}

PLOTLY_FORMAT_CUSTOMERS_ONLY = {
    "nodes": {NetworkAsset.LOAD: {"color": "red", "size": 7}},
    "edges": {},
}

PLOTLY_FORMAT_CUSTOMERS_AND_DIST_TRANSFORMERS_ONLY = {
    "nodes": {
        NetworkAsset.LOAD: {"color": "red", "size": 7},
        NetworkAsset.DISTXFMR: {"color": "blue", "size": 20},
    },
    "edges": {},
}

PLOTLY_FORMAT_CUSTOMERS_DIST_TRANSFORMERS_HT_LINE = {
    "nodes": {
        NetworkAsset.LOAD: {"color": "red", "size": 2},
        NetworkAsset.DISTXFMR: {"color": "blue", "size": 10},
    },
    "edges": {NetworkAsset.HTLINE: {"color": "orange", "size": 10}},
}
PLOTLY_FORMAT_ALL_ASSETS = {
    "nodes": {
        NetworkAsset.LOAD: {"color": "red", "size": 2},
        NetworkAsset.DISTXFMR: {"color": "blue", "size": 10},
        NetworkAsset.HTNODE: {"color": "orange", "size": 3},
        NetworkAsset.LTNODE: {"color": "blue", "size": 3},
    },
    "edges": {
        NetworkAsset.HTLINE: {"color": "orange", "size": 10},
        NetworkAsset.LTLINE: {"color": "blue", "size": 7},
    },
}

PLOTLY_FORMAT_SIMPLE_NETWORK = {
    "nodes": {"node": {"color": "blue", "size": 7}},
    "edges": {"edge": {"color": "red", "size": 10}},
}
