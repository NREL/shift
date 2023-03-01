
# standard imports 
from typing import Optional
from enum import Enum, IntEnum

# third-party imports
from pydantic import BaseModel, confloat, validator
from shift.utility.model import Location, NumPhase

class BuildingType(str, Enum):
    residential = 'residential'
    commercial = 'commercial'
    industrial = 'industrial'


class Building(Location):
    area: Optional[confloat(ge=0)]
    building_type: BuildingType = BuildingType.residential
    kw: Optional[float]
    numphase: Optional[NumPhase]

    @validator('kw')
    def kw_or_area_should_be_present(cls, v, values, **kwargs):
        if v or values['area']:
            return v 
        raise ValueError('Building should have at least kw or area!')