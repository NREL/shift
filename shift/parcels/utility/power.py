
# standard imports 
from typing import List, Dict

# third-party imports 
from shift.parcels.model import Building
import pydantic


def allocate_kw_based_on_area(
    buildings: List[Building],
    peak_kw: Dict[str, float],
):

    for building_type, kw in peak_kw.items():

        buildings_subset = [b for b in buildings if b.building_type == building_type]
        building_areas = [b.area for b in buildings_subset]

        for b in buildings_subset:
            b.kw = round((b.area* kw)/sum(building_areas),3)
