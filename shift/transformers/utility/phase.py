# standard imports
from typing import List

# third-party imports

# internal imports
from shift.transformers.model import Transformer

def set_num_phase(
    transformers: List[Transformer]
):

    for transformer in transformers:
        phases = [b.numphase for b in transformer.buildings if b.numphase]
        
        if phases:
            transformer.numphase = max(phases)
