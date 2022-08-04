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

""" Tests for geometry module. """
import os

import pandas as pd
import pytest

from shift.geometry import (
    BuildingsFromPlace,
    BuildingsFromPoint,
    BuildingsFromPolygon,
)
from shift.geometry import BuildingGeometry
from shift.geometry import SimpleLoadGeometry
from shift.geometry import SimpleLoadGeometriesFromCSV
from shift.exceptions import LatitudeNotInRangeError, LongitudeNotInRangeError


@pytest.fixture
def simple_csv_setup():
    """Create a csv and remove it once test is complete."""
    mock_df = pd.DataFrame(
        {"latitude": [20, 30, 40], "longitude": [10, 15, 20], "kw": [2, 5, 10]}
    )
    csv_filename = "mock_simple_csv.csv"
    mock_df.to_csv(csv_filename, index=False)
    yield csv_filename
    os.remove(csv_filename)


def test_invalid_latitude():
    """Test invalid latitude."""
    bgeometry = BuildingGeometry()
    with pytest.raises(Exception) as e:
        bgeometry.latitude = -500

    assert e.type == LatitudeNotInRangeError


def test_invalid_longitude():
    """Test invalid longitude."""
    bgeometry = BuildingGeometry()
    with pytest.raises(Exception) as e:
        bgeometry.longitude = -500

    assert e.type == LongitudeNotInRangeError


def test_buildings_from_place():
    """Test for creation of building geometries from a place."""
    g = BuildingsFromPlace("Chennai, India", max_dist=100)
    geometries = g.get_geometries()
    assert isinstance(geometries[0], BuildingGeometry)


def test_buildings_from_point():
    """Test for creation of building geometries from a point."""
    g = BuildingsFromPoint((27.7172, 85.3240), max_dist=100)
    geometries = g.get_geometries()
    assert isinstance(geometries[0], BuildingGeometry)


def test_buildings_from_polygon():
    """Test for creation of building geometries from a polygon"""
    g = BuildingsFromPolygon(
        [
            [-122.29262, 37.83639],
            [-122.28095, 37.82972],
            [-122.29213, 37.82768],
            [-122.29262, 37.83639],
        ]
    )
    geometries = g.get_geometries()
    assert isinstance(geometries[0], BuildingGeometry)


def test_geometries_from_csv(simple_csv_setup):
    """Test geometries from csv."""
    csv_filename = simple_csv_setup
    g = SimpleLoadGeometriesFromCSV(csv_filename)
    geometries = g.get_geometries()
    assert isinstance(geometries[0], SimpleLoadGeometry)
