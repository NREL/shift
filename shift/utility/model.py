
# third-party imports
from pydantic import BaseModel, confloat
from enum import IntEnum

from shift.constants import (
    MIN_LATITUDE,
    MAX_LATITUDE,
    MIN_LONGITUDE,
    MAX_LONGITUDE,
)

class Location(BaseModel):
    latitude: confloat(ge=MIN_LATITUDE, le=MAX_LATITUDE)
    longitude: confloat(ge=MIN_LONGITUDE, le=MAX_LONGITUDE)

class NumPhase(IntEnum):
    single = 1
    three = 3