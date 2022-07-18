from abc import ABC, abstractmethod
from exceptions import (
    LatitudeNotInRangeError,
    LongitudeNotInRangeError,
    NegativeAreaError,
    FileNotFoundError,
    NotCompatibleFileError,
    ValidationError,
)
from constants import (
    MIN_LATITUDE,
    MAX_LATITUDE,
    MIN_LONGITUDE,
    MAX_LONGITUDE,
    SIMPLELOADGEOMETRY_SCHEMA,
)
from typing import List
import osmnx as ox
import os
import pandas as pd
from utils import df_validator


""" Interface for OSMNX geometry """


class Geometry(ABC):
    @property
    def latitude(self) -> float:
        """Latitude property of a building"""
        return self._latitude

    @latitude.setter
    def latitude(self, latitude: float) -> None:
        """Setter method for latitude property of a building"""
        if latitude < MIN_LATITUDE or latitude > MAX_LATITUDE:
            raise LatitudeNotInRangeError(latitude)
        self._latitude = latitude

    @property
    def longitude(self) -> float:
        """Longitude property of a building"""
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


""" Base Implementation for OSMNX Building geometry """


class BuildingGeometry(Geometry):
    @property
    def area(self) -> float:
        """Area property of a building"""
        return self._area

    @area.setter
    def area(self, area: float) -> None:
        """Setter method for area property of a building"""
        if area < 0:
            raise NegativeAreaError(area)
        self._area = area

    def __repr__(self):
        return f"Building( Latitude = {self.latitude}, Longitude = {self.longitude}, Area = {self.area})"


""" Base Implementation for simple load point geometry """


class SimpleLoadGeometry(Geometry):
    @property
    def kw(self) -> float:
        """Area property of a building"""
        return self._kw

    @kw.setter
    def kw(self, kw: float) -> None:
        """Setter method for area property of a building"""
        self._kw = kw

    def __repr__(self):
        return f"Building( Latitude = {self.latitude}, Longitude = {self.longitude}, kW = {self.kw})"


""" Interface for getting geometries from CSV file """


class GeometriesFromCSV(ABC):
    def __init__(self, csv_file: str):

        self.csv_file = csv_file
        if not os.path.exists(csv_file):
            raise FileNotFoundError(csv_file)
        else:
            if not csv_file.endswith(".csv"):
                raise NotCompatibleFileError(csv_file, ".csv")

        self.df = pd.read_csv(csv_file)
        self.validate()

    @abstractmethod
    def validate(self):
        pass

    @abstractmethod
    def get_geometries(self) -> List[Geometry]:
        pass


""" Concrete implementations for getting simple load geometries from CSV file """


class SimpleLoadGeometriesFromCSV(GeometriesFromCSV):
    def get_geometries(self):

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
        return df_validator(SIMPLELOADGEOMETRY_SCHEMA, self.df)


""" Interface for getting geometries from OpenStreet data """


class OpenStreetGeometries(ABC):
    @abstractmethod
    def get_gdf(self):
        pass

    @abstractmethod
    def get_geometries(self) -> List[Geometry]:
        pass


""" Concrete implementations of open street building geometries """


class OpenStreetBuildingGeometries(OpenStreetGeometries):
    def get_geometries(self) -> List[Geometry]:

        """Create container for holding list of geometries"""
        concrete_geometries = []

        """ Get geo dataframe object implemented by child OpenStreet Geometries subclass"""
        gdf_data = self.get_gdf().to_dict(orient="records")

        """ Loop through all the rows in geo dataframe to create list of concrete geometries"""
        for row in gdf_data:

            """Looping through only either point or polygon geometries"""
            if row["geometry"].geom_type in ["Point", "Polygon"]:

                if row["geometry"].geom_type == "Point":

                    centre = list(row["geometry"].coords)[0]
                    area = 0

                else:
                    centre = list(row["geometry"].centroid.coords)[0]
                    # By default shapely gives area in square degrees
                    # By assuming the earth to be a perfect square of 6370 meter square
                    # area can be computed as below but it's not accurate however does the job for now
                    area = row["geometry"].area * 6370**2

                """ Create individual geometry """
                geometry = BuildingGeometry()
                geometry.latitude = centre[1]
                geometry.longitude = centre[0]
                geometry.area = round(area, 2)

                if geometry not in concrete_geometries:
                    concrete_geometries.append(geometry)

        return concrete_geometries


""" Getting building geometries from single point within bounding box"""


class BuildingsFromPoint(OpenStreetBuildingGeometries):
    def __init__(self, point: tuple, max_dist=1000):

        # e.g. (13.242134, 80.275948)
        self.point = point
        self.max_dist = max_dist

    def get_gdf(self):
        return ox.geometries_from_point(
            self.point, {"building": True}, dist=self.max_dist
        )


""" Getting building geometries from a place address within bounding box"""


class BuildingsFromPlace(OpenStreetBuildingGeometries):
    def __init__(self, place: str, max_dist=1000):

        # e.g. Chennai, India
        self.place = place
        self.max_dist = max_dist

    def get_gdf(self):
        return ox.geometries_from_address(
            self.place, {"building": True}, dist=self.max_dist
        )


""" Getting building geometries from a given polygon """


class BuildingsFromPolygon(OpenStreetBuildingGeometries):
    def __init__(self, polygon: List[list]):

        # e.g. [[13.242134, 80.275948]]
        self.polygon = polygon

    def get_gdf(self):
        return ox.geometries_from_polygon(self.polygon, {"building": True})


if __name__ == "__main__":

    # g = BuildingsFromPlace("Chennai, India")
    # geometries = g.get_geometries()
    # print(geometries[0])

    g = SimpleLoadGeometriesFromCSV(
        r"C:\Users\KDUWADI\Desktop\NREL_Projects\ciff_track_2\data\grp_customers_reduced.csv"
    )
    geometries = g.get_geometries()
    print(geometries[0])
