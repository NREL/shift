
from enums import NumPhase, Phase
from constants import (
    MIN_LATITUDE,
    MAX_LATITUDE,
    MIN_LONGITUDE,
    MAX_LONGITUDE,
    MAX_POWER_FACTOR,
    MIN_POWER_FACTOR,
    MIN_ZOOM_LEVEL,
    MAX_ZOOM_LEVEL,
    MAP_STYLES,
    MIN_PERCENTAGE,
    MAX_PERCENTAGE,
    MIN_NUM_CLUSTER,
    MIN_ADJUSTMENT_FACTOR,
    MAX_ADJUSTMENT_FACTOR,
    MIN_YEAR_OPERATION,
    MAX_YEAR_OPERATION,
    MIN_POLE_TO_POLE_DISTANCE,
    MAX_POLE_TO_POLE_DISTANCE,
    VALID_LENGTH_UNITS,
    VALID_FREQUENCIES
)

class SeedBaseException(Exception):
    """ All exception should derive from this """


class LatitudeNotInRangeError(SeedBaseException):
    """Exception raised because latitude not in range"""

    def __init__(self, latitude:float):
        self.message = f"Latitude {latitude} not in ({MIN_LATITUDE}, {MAX_LATITUDE}) range!"
        super().__init__(self.message)

class LongitudeNotInRangeError(SeedBaseException):
    """Exception raised because longitude not in range"""

    def __init__(self, longitude:float):
        self.message = f"Longitude {longitude} not in ({MIN_LONGITUDE}, {MAX_LONGITUDE}) range!"
        super().__init__(self.message)

class NegativeKVError(SeedBaseException):
    
    """ Exception raised because kV is negative"""
    def __init__(self, kv:float):
        self.message = f"KV = {kv} can not be negative"
        super().__init__(self.message)

class ZeroKVError(SeedBaseException):
    """ Exception raused because the kV is zero"""

class NegativeAreaError(SeedBaseException):
    """ Exception raused because area of the geometry is negative"""
    def __init__(self, area:float):
        self.message = f"Area = {area} can not be negative"
        super().__init__(self.message)


class PowerFactorNotInRangeError(SeedBaseException):
    """Exception raised because power factor not in range"""

    def __init__(self, pf:float):
        self.message = f"Power factor {pf} not in ({MIN_POWER_FACTOR}, {MAX_POWER_FACTOR}) range!"
        super().__init__(self.message)

class PercentageSumNotHundred(SeedBaseException):
    """Exception raised because sum of pct values not equal to 100"""

    def __init__(self, total_pct:float):
        self.message = f"Total sum {total_pct} not equal to 100"
        super().__init__(self.message)

class FileNotFoundError(SeedBaseException):
    """Exception raised because file path does not exist"""

    def __init__(self, file_path: str):
        self.message = f"File {file_path} does not exist!"
        super().__init__(self.message)

class NotCompatibleFileError(SeedBaseException):
    """Exception raised because unexpected file type recieved"""

    def __init__(self, file_path: str, expected_type: str):
        self.message = f"Unexpected file type received, expected {expected_type} but got {file_path}"
        super().__init__(self.message)

class ValidationError(SeedBaseException):
    """Exception raised bbecause content can not be validated"""

    def __init__(self, errors: list):
        self.message = f"Could not validate the content: {errors}"
        super().__init__(self.message)

class ZoomLevelNotInRangeError(SeedBaseException):
    """Exception raised because zoom level defined is not in range"""

    def __init__(self, zoom:int):
        self.message = f"Zoom level {zoom} not in ({MIN_ZOOM_LEVEL}, {MAX_ZOOM_LEVEL}) range!"
        super().__init__(self.message)

class InvalidMapboxStyle(SeedBaseException):
    """Exception raised because specified style is not accepted"""
    def __init__(self, style:str):
        self.message = f"Style {style} is not a valid style. Please one of these styles {MAP_STYLES}"
        super().__init__(self.message)

class EmptyAssetStyleDict(SeedBaseException):
    """Exception raised for empty style dict"""
    def __init__(self):
        self.message = "Asset specific style can not be empty in PLotlyGISNetworkPlot object"
        super().__init__(self.message)

class MissingKeyDataForNetworkNode(SeedBaseException):
    """Exception because type property is missing for a network node"""
    def __init__(self, type: str):
        self.message = f"`{type}` field is missing in network node data"
        super().__init__(self.message)

class InvalidNodeType(SeedBaseException):
    """Exception because invalid node type is used """
    def __init__(self, node: str):
        self.message = f"Invalid node type: {node}, please make sure to use valid node types"
        super().__init__(self.message)

class FolderNotFoundError(SeedBaseException):
    """Exception raised because folder not found!"""

    def __init__(self, folder_path: str):
        self.message = f"Folder {folder_path} does not exist!"
        super().__init__(self.message)

class PercentageNotInRangeError(SeedBaseException):
    """ Exception raised because percentage set is not within range"""
    def __init__(self, pct: float):
        self.message = f"Percentage {pct} not in ({MIN_PERCENTAGE}, {MAX_PERCENTAGE}) range!"
        super().__init__(self.message)


class NegativekVAError(SeedBaseException):
    """ Exception raised because negative kva is used !"""
    def __init__(self, kva:float):
        self.message = f"kVA = {kva} can not be negative"
        super().__init__(self.message)

class MaxLoopReachedForKmeans(SeedBaseException):
    """ Exception raised because max number of iterations reached for computing optimal cluster number """

class WrongInputUsed(SeedBaseException):
    """ Exeption raised becaue wrong input is used"""

class NumberOfClusterNotInRangeError(SeedBaseException):
    """ Exception raised because number of clusters used is not within range"""
    def __init__(self, num_of_clus: str):
        self.message = f"Number of clusters {num_of_clus} must be less than {MIN_NUM_CLUSTER}!"
        super().__init__(self.message)

class EarlyMethodCallError(SeedBaseException):
    """ Method is called to early """

class AttributeDoesNotExistError(SeedBaseException):
    """ Method is called to early """


class AdjustmentFactorNotInRangeError(SeedBaseException):
    """Exception raised because adjustment factor not in range"""

    def __init__(self, af:float):
        self.message = f"Adjustement factor {af} not in ({MIN_ADJUSTMENT_FACTOR}, {MAX_ADJUSTMENT_FACTOR}) range!"
        super().__init__(self.message)

class HTkVlowerthanLTkVError(SeedBaseException):
    """ Exceptions raised because HT kV used is lower than LT kv used"""
    def __init__(self, ht_kv: float, lt_kv:float):
        self.message = f"HT kV {ht_kv} must be higher than LT kV {lt_kv} !"
        super().__init__(self.message)

class EmptyCatalog(SeedBaseException):
    """ Exceptions raised because no catalog found"""

class MultipleCatalogFoundError(SeedBaseException):
    """ Exceptions raised because multiple records found in the catalog"""
    def __init__(self, records):
        self.message = f"Multiple records found {records}!"
        super().__init__(self.message)

class OperationYearNotInRange(SeedBaseException):
    """ Exceptions raised because year in operation is not within range"""
    def __init__(self, year: float):
        self.message = f"Year in operation must be in range {(MIN_YEAR_OPERATION, MAX_YEAR_OPERATION)}, but found {year}"
        super().__init__(self.message)


class PoleToPoleDistanceNotInRange(SeedBaseException):
    """ Exceptions raised because pole to pole distance is not within range"""
    def __init__(self, distance: float):
        self.message = f"Pole to pole distance must be in range {(MIN_POLE_TO_POLE_DISTANCE, MAX_POLE_TO_POLE_DISTANCE)}, but found {distance}"
        super().__init__(self.message)

class NegativeLineLengthError(SeedBaseException):
    """ Exceptions raised because line length is negative"""
    def __init__(self, length: float):
        self.message = f"Line length can not be negative but found {length}"
        super().__init__(self.message)

class InvalidLengthUnitError(SeedBaseException):
    """ Exceptions raised because length unit is invalid """
    def __init__(self, unit: str):
        self.message = f"Invalid length unit used {unit} please choose one of these units {VALID_LENGTH_UNITS}"
        super().__init__(self.message)


class NegativeDiameterError(SeedBaseException):
    """ Exceptions raised because diameter is negative"""
    def __init__(self, diameter: float):
        self.message = f"Diamater can not be negative but found {diameter}"
        super().__init__(self.message)


class NegativeGMRError(SeedBaseException):
    """ Exceptions raised because GMR is negative"""
    def __init__(self, gmr: float):
        self.message = f"GMR can not be negative but found {gmr}"
        super().__init__(self.message)

class NegativeResistanceError(SeedBaseException):
    """ Exceptions raised because AC resistance is negative"""
    def __init__(self, r: float):
        self.message = f"AC resistance can not be negative but found {r}"
        super().__init__(self.message)


class NegativeAmpacityError(SeedBaseException):
    """ Exceptions raised because Ampacity is negative"""
    def __init__(self, ampacity: float):
        self.message = f"Ampacity can not be negative but found {ampacity}"
        super().__init__(self.message)

class NegativeStrandsError(SeedBaseException):
    """ Exceptions raised because Number of strands is negative"""
    def __init__(self, num_of_strands: float):
        self.message = f"Number of strands can not be negative but found {num_of_strands}"
        super().__init__(self.message)


class CustomerInvalidPhase(SeedBaseException):
    """ Exceptions raised because number of phase for customer is greater than number of phase used in secondary"""
    def __init__(self, customer_num_phase: NumPhase, secondary_num_phase: NumPhase):
        self.message = f"Number of phase used for load {customer_num_phase} is greater than that used for secondary {secondary_num_phase}"
        super().__init__(self.message)

class UnsupportedFrequencyError(SeedBaseException):
    """ Exceptions raised because unsupported frequency is in use"""
    def __init__(self, freq: float):
        self.message = f"Unsupported frequency is used {float} please choose one of these frequency {VALID_FREQUENCIES}"
        super().__init__(self.message)

class PhaseMismatchError(SeedBaseException):
    """ Exceptions raised because phase misatch is encountered """
    def __init__(self, phase1: Phase, phase2: Phase):
        self.message = f"Attempt to connect phase {phase1} to phase {phase2} is encountered!"
        super().__init__(self.message)

class IncompleteGeometryConfigurationDict(SeedBaseException):
    """ Exceptions raised because of incomplete geometry configuration dict """
    def __init__(self, num_phase: NumPhase, geometry_dict: dict):
        self.message = f"{num_phase} key does not exist in {geometry_dict}"
        super().__init__(self.message)

class ConductorNotFoundForKdrop(SeedBaseException):
    """ Exceptions raised because no conductor is found that satisfies the kdrop """
    def __init__(self, kdrop: float):
        self.message = f"No conductor is found that satisfies kdrop of value {kdrop}"
        super().__init__(self.message)