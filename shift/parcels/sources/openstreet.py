# standard imports
from typing import List, Sequence

# third-party imports
import geopandas
import pydantic
import shapely
import osmnx as ox

# internal imports
from shift.parcels.model import Building


def _gdf_to_buildings(gdf: geopandas.geodataframe.GeoDataFrame):
    
    geometries = []
    for geometry in gdf.to_dict(orient="records"):
        
        if geometry["geometry"].geom_type == "Point": 
            centre = list(geometry["geometry"].coords)[0]
            geometries.append({
                'longitude': centre[0],
                'latitude': centre[1],
                'area': 0      
            })
        if  geometry["geometry"].geom_type == "Polygon":
            centre = list(geometry["geometry"].centroid.coords)[0]
            geometries.append({
                'longitude': centre[0],
                'latitude': centre[1],
                'area': geometry["geometry"].area * 6370**2      
            })
    return pydantic.parse_obj_as(List[Building], geometries)

def buildings_from_point(
        point: Sequence, max_dist: float = 1000
) -> List[Building]:
    
    return _gdf_to_buildings(
         ox.geometries_from_point(
            point, {"building": True}, dist=max_dist
        )
    )

def buildings_from_place(
    place: str, max_dist=1000
) -> List[Building]:
    
    return _gdf_to_buildings(
        ox.geometries_from_address(
            place, {"building": True}, dist=max_dist
        )
    )

def buildings_from_polygon(
    polygon: List[list]
) -> List[Building]:
    
    return _gdf_to_buildings(
       ox.geometries_from_polygon(
        shapely.geometry.Polygon(polygon),
        {"building": True})
    )
