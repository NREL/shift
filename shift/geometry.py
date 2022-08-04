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

""" Handles creation and management of geometries.

This module manages creation of geometries from csv file as well
as openstreet data. Contains abstract as well as concrete classes
for creating geometries.

Examples:
    Get the buildings from chennai and prints one of the building geometry.
    >>> from shift.geometry import BuildingsFromPlace
    >>> g = BuildingsFromPlace("Chennai, India")
    >>> geometries = g.get_geometries()
    >>> print(geometries[0])
"""

from abc import ABC, abstractmethod
from typing import List, Sequence
import os

import osmnx as ox
import pandas as pd
import shapely

# pylint: disable=redefined-builtin
from shift.exceptions import (
    LatitudeNotInRangeError,
    LongitudeNotInRangeError,
    NegativeAreaError,
    FileNotFoundError,
    NotCompatibleFileError,
)
from shift.constants import (
    MIN_LATITUDE,
    MAX_LATITUDE,
    MIN_LONGITUDE,
    MAX_LONGITUDE,
    SIMPLELOADGEOMETRY_SCHEMA,
)
from shift.utils import df_validator


class Geometry(ABC):
    """Interface for Geometry object."""

    @property
    def latitude(self) -> float:
        """float: Latitude property of a building"""
        return self._latitude

    @latitude.setter
    def latitude(self, latitude: float) -> None:
        """Setter method for latitude property of a building"""
        if latitude < MIN_LATITUDE or latitude > MAX_LATITUDE:
            raise LatitudeNotInRangeError(latitude)
        self._latitude = latitude

    @property
    def longitude(self) -> float:
        """float: Longitude property of a building"""
        return self._longitude

    @longitude.setter
    def longitude(self, longitude: float) -> None:
        """Setter method for longitude property of a building"""
        if longitude < MIN_LONGITUDE or longitude > MAX_LONGITUDE:
            raise LongitudeNotInRangeError(longitude)
        self._longitude = longitude

    def __eq__(self, other):
        return (
            self.latitude == other.latitude
            and self.longitude == other.longitude
        )

    def __hash__(self):
        return hash((self.latitude, self.longitude))


class BuildingGeometry(Geometry):
    """Implementation for Building geometry."""

    @property
    def area(self) -> float:
        """float: Area property of a building"""
        return self._area

    @area.setter
    def area(self, area: float) -> None:
        """Setter method for area property of a building"""
        if area < 0:
            raise NegativeAreaError(area)
        self._area = area

    def __repr__(self):
        return (
            f"Building( Latitude = {self.latitude}, "
            + f" Longitude = {self.longitude}, Area = {self.area})"
        )


class SimpleLoadGeometry(Geometry):
    """Implementation for simple load point geometry"""

    @property
    def kw(self) -> float:
        """float: Area property of a building"""
        return self._kw

    @kw.setter
    def kw(self, kw: float) -> None:
        """Setter method for area property of a building"""
        self._kw = kw

    def __repr__(self):
        return (
            f"Building( Latitude = {self.latitude}, "
            + f"Longitude = {self.longitude}, kW = {self.kw})"
        )


class GeometriesFromCSV(ABC):
    """Interface for getting geometries from CSV file

    Attributes:
        csv_file (str): Path to csv file
        df (pd.DataFrame): dataframe holding the content of csv file

    """

    def __init__(self, csv_file: str) -> None:
        """Method for instantiationg the class.

        Args:
            csv_file (str): Path to valid csv file

        Raises:
            FileNotFoundError: If csv file is not found
            NotCompatibleFileError: If the file pssed is not csv
        """

        self.csv_file = csv_file
        if not os.path.exists(csv_file):
            raise FileNotFoundError(csv_file)
        else:
            if not csv_file.endswith(".csv"):
                raise NotCompatibleFileError(csv_file, ".csv")

        self.df = pd.read_csv(csv_file)
        self.validate()

    @abstractmethod
    def validate(self) -> bool:
        """Child class must implement validate method."""
        pass

    @abstractmethod
    def get_geometries(self) -> List[Geometry]:
        """Child class must implement method to return list of geometries."""
        pass


class SimpleLoadGeometriesFromCSV(GeometriesFromCSV):
    """Concrete implementations for getting simple load
    geometries from CSV file.

    Refer to the base class for more deatils on how to construct the
    object.
    """

    def get_geometries(self):
        """Method to get all the gepmetries from csv."""

        # Let's loop through all records and create all the geometries
        concrete_geometries = []

        for record in self.df.to_dict(orient="records"):

            geometry = SimpleLoadGeometry()
            geometry.latitude = record["latitude"]
            geometry.longitude = record["longitude"]
            geometry.kw = record["kw"]

            concrete_geometries.append(geometry)

        return concrete_geometries

    def validate(self):
        """Method to validate the content of csv file."""
        return df_validator(SIMPLELOADGEOMETRY_SCHEMA, self.df)


class OpenStreetGeometries(ABC):
    """Interface for getting geometries from OpenStreet data."""

    @abstractmethod
    def get_gdf(self) -> pd.DataFrame:
        """Method to return the geo dataframe containing all the buildings.

        Returns:
            pd.DataFrame: Geo dataframe containing all the buildings.
        """
        pass

    @abstractmethod
    def get_geometries(self) -> List[Geometry]:
        """Method to return all the geometry objects.

        Returns:
            List[Geometry]: list of all the building geometry objects.
        """
        pass


class OpenStreetBuildingGeometries(OpenStreetGeometries):
    """Concrete implementations of open street building geometries"""

    def get_geometries(self) -> List[Geometry]:
        """Refer to base class for details."""
        # Create container for holding list of geometries
        concrete_geometries = []

        # Get geo dataframe object implemented by
        # child OpenStreet Geometries subclass
        gdf_data = self.get_gdf().to_dict(orient="records")

        # Loop through all the rows in geo dataframe to
        # create list of concrete geometries
        for row in gdf_data:

            # Looping through only either point or polygon geometries
            if row["geometry"].geom_type in ["Point", "Polygon"]:

                if row["geometry"].geom_type == "Point":

                    centre = list(row["geometry"].coords)[0]
                    area = 0

                else:
                    centre = list(row["geometry"].centroid.coords)[0]
                    # By default shapely gives area in square degrees
                    # By assuming the earth to be a perfect square of
                    # 6370 meter square area can be computed as below
                    # but it's not accurate however does the job for now
                    area = row["geometry"].area * 6370**2

                # Create individual geometry
                geometry = BuildingGeometry()
                geometry.latitude = centre[1]
                geometry.longitude = centre[0]
                geometry.area = round(area, 2)

                if geometry not in concrete_geometries:
                    concrete_geometries.append(geometry)

        return concrete_geometries


class BuildingsFromPoint(OpenStreetBuildingGeometries):
    """Getting building geometries from single point within bounding box.

    Attributes:
        point (Sequence): Point in (latitude, longitude) format
        max_dist (float): Distance in meter from the point to
            create a bounding box
    """

    def __init__(self, point: Sequence, max_dist: float = 1000) -> None:

        """Instantiating the class.

        Args:
            point (Sequence): Point in (latitude, longitude) format
            max_dist (float): Distance in meter from the point to
                create a bounding box
        """
        # e.g. (13.242134, 80.275948)
        self.point = point
        self.max_dist = max_dist

    def get_gdf(self) -> pd.DataFrame:
        """Refer to base class for details."""
        return ox.geometries_from_point(
            self.point, {"building": True}, dist=self.max_dist
        )


class BuildingsFromPlace(OpenStreetBuildingGeometries):
    """Getting building geometries from a place address within bounding box.

    Attributes:
        place (str): Any place in string format e.g. chennai, india
        max_dist (float): Distance in meter from the point
            to create a bounding box
    """

    def __init__(self, place: str, max_dist=1000) -> None:

        """Instantiating the class.

        Args:
            place (str): Any place in string format e.g. chennai, india
            max_dist (float): Distance in meter from the place
                to create a bounding box
        """

        # e.g. Chennai, India
        self.place = place
        self.max_dist = max_dist

    def get_gdf(self) -> pd.DataFrame:
        """Refer to base class for details."""
        return ox.geometries_from_address(
            self.place, {"building": True}, dist=self.max_dist
        )


class BuildingsFromPolygon(OpenStreetBuildingGeometries):
    """Getting building geometries from a given polygon.

    Attributes:
        polygon: List[list]: Polygon to be used e.g. [[13.242134, 80.275948]]
    """

    def __init__(self, polygon: List[list]) -> None:

        """Instantiating the class.

        Args:
            polygon: List[list]: Polygon to be used
                e.g. [[13.242134, 80.275948]]
        """
        self.polygon = shapely.geometry.Polygon(polygon)

    def get_gdf(self) -> pd.DataFrame:
        """Refer to base class for details."""
        return ox.geometries_from_polygon(self.polygon, {"building": True})
