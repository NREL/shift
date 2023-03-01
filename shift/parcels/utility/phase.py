
# standard imports
from typing import List, Dict, Callable

# third-party imports
from shift.parcels.model import Building, BuildingType


# Custom num phase 
def set_num_phase(
    buildings: List[Building],
    callback: Callable[[Building], None]
):
    
    for building in buildings:
        building.numphase = callback()


def _us_residential(b: Building):
    return (3 if b.area > 500 else 1) if b.area else 1

def _us_commercial(b: Building):
    return (3 if b.kw > 10 else 1) if b.kw else 3

def _us_industrial(b: Building):
    return 3

# US centric num phase 
def us_set_num_phase(
    buildings: List[Building],
    mapper: Dict[str, Callable[[Building], int]] = {
        'residential': _us_residential,
        'commercial': _us_commercial,
        'industrial': _us_industrial
    }
):
    for building in buildings:
        building.numphase = mapper[building.building_type](building)
    

        


