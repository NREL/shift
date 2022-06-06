from enum import Enum


class Phase(Enum):
    A = '1'
    B = '2'
    C = '3'
    AN = '1.0'
    BN = '2.0'
    CN = '3.0'
    AB = '1.2'
    BA = '2.1'
    BC = '2.3'
    CB = '3.2'
    AC = '1.3'
    CA = '3.1'
    ABC = '1.2.3'
    ABCN = '1.2.3.0'

class NumPhase(Enum):
    SINGLE = 1
    TWO = 2
    THREE = 3

class LoadConnection(Enum):

    STAR = 'wye'
    DELTA = 'delta'

class TransformerConnection(Enum):

    STAR = 'Wye'
    DELTA = 'Delta'

class NetworkAsset(Enum):

    LOAD = 'load'
    LINE = 'line'
    DISTXFMR = 'distribution_transformer'
    HTNODE = 'ht_node'
    HTLINE = 'ht_line'
    LTNODE = 'lt_node'
    LTLINE = 'lt_line'

class ConductorType(Enum):
    OVERHEAD = 'overhead'
    UNDERGROUND_CONCENTRIC = 'underground'

class GeometryConfiguration(Enum):
    HORIZONTAL = 'horizontal'