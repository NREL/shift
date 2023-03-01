# standard imports
from typing import Optional, List
from enum import Enum

# third-party imports

# internal imports
from shift.utility.model import Location, NumPhase
from shift.parcels.model import Building

class Transformer(Location):
    numphase: Optional[NumPhase]
    buildings: Optional[List[Building]]
