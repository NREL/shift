
# standard imports
from typing import List 

# third-party imports
import polars 
import pydantic 

# internal imports 
from shift.parcels.model import Building


def get_buildings_from_csv(csv_path: str):
    df = polars.read_csv(csv_path)
    return pydantic.parse_obj_as(List[Building], df.to_dicts())
