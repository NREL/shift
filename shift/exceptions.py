# -*- coding: utf-8 -*-
# Copyright (c) 2022, Alliance for Sustainable Energy, LLC

# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

""" This module all the exceptions raised by this package. """

from typing import List
from shift.constants import (
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
    VALID_FREQUENCIES,
)
from shift.enums import NumPhase, Phase


class SeedBaseException(Exception):
    """All exception should derive from this."""


class LatitudeNotInRangeError(SeedBaseException):
    """Exception raised because latitude not in range.

    Args:
        latitude (float): Latitude property
    """

    def __init__(self, latitude: float):
        self.message = (
            f"Latitude {latitude} not in "
            + f"({MIN_LATITUDE}, {MAX_LATITUDE}) range!"
        )
        super().__init__(self.message)


class LongitudeNotInRangeError(SeedBaseException):
    """Exception raised because longitude not in range.

    Args:
        longitude (float): Longitude property
    """

    def __init__(self, longitude: float):
        self.message = (
            f"Longitude {longitude} not in "
            + f"({MIN_LONGITUDE}, {MAX_LONGITUDE}) range!"
        )
        super().__init__(self.message)


class NegativeKVError(SeedBaseException):
    """Exception raised because kV is negative.

    Args:
        kv (float): Voltage in KV property
    """

    def __init__(self, kv: float):
        self.message = f"KV = {kv} can not be negative"
        super().__init__(self.message)


class ZeroKVError(SeedBaseException):
    """Exception raused because the kV is zero."""


class NegativeAreaError(SeedBaseException):
    """Exception raused because area of the geometry is negative.

    Args:
        area (float): Area property
    """

    def __init__(self, area: float):
        self.message = f"Area = {area} can not be negative"
        super().__init__(self.message)


class PowerFactorNotInRangeError(SeedBaseException):
    """Exception raised because power factor not in range.

    Args:
        pf (float): Power factor property
    """

    def __init__(self, pf: float):
        self.message = (
            f"Power factor {pf} not in "
            + f"({MIN_POWER_FACTOR}, {MAX_POWER_FACTOR}) range!"
        )
        super().__init__(self.message)


class PercentageSumNotHundred(SeedBaseException):
    """Exception raised because sum of pct values not equal to 100.

    Args:
        total_pct (float): Percentage property
    """

    def __init__(self, total_pct: float):
        self.message = f"Total sum {total_pct} not equal to 100"
        super().__init__(self.message)


# pylint: disable=redefined-builtin
class FileNotFoundError(SeedBaseException):
    """Exception raised because file path does not exist.

    Args:
        file_path (str): File path property
    """

    def __init__(self, file_path: str):
        self.message = f"File {file_path} does not exist!"
        super().__init__(self.message)


class NotCompatibleFileError(SeedBaseException):
    """Exception raised because unexpected file type recieved.

    Args:
        file_path (str): File path property
        expected_type (str): Expected file type property
    """

    def __init__(self, file_path: str, expected_type: str):
        self.message = (
            "Unexpected file type received, "
            + f"expected {expected_type} but got {file_path}"
        )
        super().__init__(self.message)


class ValidationError(SeedBaseException):
    """Exception raised bbecause content can not be validated.

    Args:
        errors (list): List of error messages.
    """

    def __init__(self, errors: list):
        self.message = f"Could not validate the content: {errors}"
        super().__init__(self.message)


class ZoomLevelNotInRangeError(SeedBaseException):
    """Exception raised because zoom level defined is not in range.

    Args:
        zoom (int): Zoom level property
    """

    def __init__(self, zoom: int):
        self.message = (
            f"Zoom level {zoom} not in"
            + f"({MIN_ZOOM_LEVEL}, {MAX_ZOOM_LEVEL}) range!"
        )
        super().__init__(self.message)


class InvalidMapboxStyle(SeedBaseException):
    """Exception raised because specified style is not accepted.

    Args:
        style (str): Style property used for mapbox
    """

    def __init__(self, style: str):
        self.message = (
            f"Style {style} is not a valid style. "
            + f"Please one of these styles {MAP_STYLES}"
        )
        super().__init__(self.message)


class EmptyAssetStyleDict(SeedBaseException):
    """Exception raised for empty style dict."""

    def __init__(self):
        self.message = (
            "Asset specific style can not be"
            + "empty in PLotlyGISNetworkPlot object"
        )
        super().__init__(self.message)


class MissingKeyDataForNetworkNode(SeedBaseException):
    """Exception because type property is missing for a network node.

    Args:
        type (str): type property for missing key
    """

    def __init__(self, type: str):
        self.message = f"`{type}` field is missing in network node data"
        super().__init__(self.message)


class InvalidNodeType(SeedBaseException):
    """Exception because invalid node type is used.

    Args:
        node (str): Node type property
    """

    def __init__(self, node: str):
        self.message = (
            f"Invalid node type: {node}, "
            + "please make sure to use valid node types"
        )
        super().__init__(self.message)


class FolderNotFoundError(SeedBaseException):
    """Exception raised because folder not found.

    Args:
        folder_path (str): Path to a invalid folder
    """

    def __init__(self, folder_path: str):
        self.message = f"Folder {folder_path} does not exist!"
        super().__init__(self.message)


class PercentageNotInRangeError(SeedBaseException):
    """Exception raised because percentage set is not within range.

    Args:
        pct (float): Percentage property
    """

    def __init__(self, pct: float):
        self.message = (
            f"Percentage {pct} not "
            + f"in ({MIN_PERCENTAGE}, {MAX_PERCENTAGE}) range!"
        )
        super().__init__(self.message)


class NegativekVAError(SeedBaseException):
    """Exception raised because negative kva is used.

    Args:
        kva (float): kva property
    """

    def __init__(self, kva: float):
        self.message = f"kVA = {kva} can not be negative"
        super().__init__(self.message)


class MaxLoopReachedForKmeans(SeedBaseException):
    """Exception raised because max number of iterations
    reached for computing optimal cluster number."""


class WrongInputUsed(SeedBaseException):
    """Exeption raised becaue wrong input is used."""


class NumberOfClusterNotInRangeError(SeedBaseException):
    """Exception raised because number of clusters used is not within range.

    Args:
        num_of_clus (int): Number of clusters property
    """

    def __init__(self, num_of_clus: int):
        self.message = (
            f"Number of clusters {num_of_clus}"
            + f"must be less than {MIN_NUM_CLUSTER}!"
        )
        super().__init__(self.message)


class EarlyMethodCallError(SeedBaseException):
    """Method is called to early."""


class AttributeDoesNotExistError(SeedBaseException):
    """Method is called to early."""


class AdjustmentFactorNotInRangeError(SeedBaseException):
    """Exception raised because adjustment factor not in range.

    Args:
        af (float): Adjustment factor property
    """

    def __init__(self, af: float):
        self.message = (
            f"Adjustement factor {af} not in "
            + f"({MIN_ADJUSTMENT_FACTOR}, {MAX_ADJUSTMENT_FACTOR}) range!"
        )
        super().__init__(self.message)


class HTkVlowerthanLTkVError(SeedBaseException):
    """Exceptions raised because HT kV used is lower than LT kv used.

    Args:
        ht_kv (float): High tension kv property
        lt_kv (float): Low tension kv property
    """

    def __init__(self, ht_kv: float, lt_kv: float):
        self.message = f"HT kV {ht_kv} must be higher than LT kV {lt_kv} !"
        super().__init__(self.message)


class EmptyCatalog(SeedBaseException):
    """Exceptions raised because no catalog found."""


class MultipleCatalogFoundError(SeedBaseException):
    """Exceptions raised because multiple records found in the catalog.

    Args:
        records (List[dict]): List of records
    """

    def __init__(self, records: List[dict]):
        self.message = f"Multiple records found {records}!"
        super().__init__(self.message)


class OperationYearNotInRange(SeedBaseException):
    """Exceptions raised because year in operation is not within range.

    Args:
        year (float): Year property
    """

    def __init__(self, year: float):
        self.message = (
            "Year in operation must be in range "
            + f"{(MIN_YEAR_OPERATION, MAX_YEAR_OPERATION)}, but found {year}"
        )
        super().__init__(self.message)


class PoleToPoleDistanceNotInRange(SeedBaseException):
    """Exceptions raised because pole to pole distance is not within range.

    Args:
        distance (float): Pole to pole distance property
    """

    def __init__(self, distance: float):
        self.message = (
            "Pole to pole distance must be in range "
            + f"{(MIN_POLE_TO_POLE_DISTANCE, MAX_POLE_TO_POLE_DISTANCE)}, "
            + f"but found {distance}"
        )
        super().__init__(self.message)


class NegativeLineLengthError(SeedBaseException):
    """Exceptions raised because line length is negative.

    Args:
        length (float): Line segment's length property
    """

    def __init__(self, length: float):
        self.message = f"Line length can not be negative but found {length}"
        super().__init__(self.message)


class InvalidLengthUnitError(SeedBaseException):
    """Exceptions raised because length unit is invalid.

    Args:
        unit (str): Line length unit used
    """

    def __init__(self, unit: str):
        self.message = (
            f"Invalid length unit used {unit} "
            + f"please choose one of these units {VALID_LENGTH_UNITS}"
        )
        super().__init__(self.message)


class NegativeDiameterError(SeedBaseException):
    """Exceptions raised because diameter is negative.

    Args:
        diameter (float): Conductor diameter property
    """

    def __init__(self, diameter: float):
        self.message = f"Diamater can not be negative but found {diameter}"
        super().__init__(self.message)


class NegativeGMRError(SeedBaseException):
    """Exceptions raised because GMR is negative.

    Args:
        gmr (float): Geometric mean radius property
    """

    def __init__(self, gmr: float):
        self.message = f"GMR can not be negative but found {gmr}"
        super().__init__(self.message)


class NegativeResistanceError(SeedBaseException):
    """Exceptions raised because AC resistance is negative.

    Args:
        r (float): AC resistance property
    """

    def __init__(self, r: float):
        self.message = f"AC resistance can not be negative but found {r}"
        super().__init__(self.message)


class NegativeAmpacityError(SeedBaseException):
    """Exceptions raised because Ampacity is negative.

    Args:
        ampacity (float): Ampacity property
    """

    def __init__(self, ampacity: float):
        self.message = f"Ampacity can not be negative but found {ampacity}"
        super().__init__(self.message)


class NegativeStrandsError(SeedBaseException):
    """Exceptions raised because Number of strands is negative.

    Args:
        num_of_strands (float): Number of strands property
    """

    def __init__(self, num_of_strands: float):
        self.message = (
            f"Number of strands can not be negative but found {num_of_strands}"
        )
        super().__init__(self.message)


class CustomerInvalidPhase(SeedBaseException):
    """Exceptions raised because number of phase for customer
    is greater than number of phase used in secondary.

    Args:
        customer_num_phase (NumPhase): Number of phase property for customer
        secondary_num_phase (NumPhase): Number of phase for secondary lateral
    """

    def __init__(
        self, customer_num_phase: NumPhase, secondary_num_phase: NumPhase
    ):
        self.message = (
            f"Number of phase used for load {customer_num_phase}"
            + f" is greater than that used for secondary {secondary_num_phase}"
        )
        super().__init__(self.message)


class UnsupportedFrequencyError(SeedBaseException):
    """Exceptions raised because unsupported frequency is in use.

    Args:
        freq (float): Frequency in hz
    """

    def __init__(self, freq: float):
        self.message = (
            f"Unsupported frequency is used {freq}"
            + f" please choose one of these frequency {VALID_FREQUENCIES}"
        )
        super().__init__(self.message)


class PhaseMismatchError(SeedBaseException):
    """Exceptions raised because phase misatch is encountered.

    Args:
        phase1 (Phase): Phase property for one end
        phase2 (Phase): Phase property for other end
    """

    def __init__(self, phase1: Phase, phase2: Phase):
        self.message = (
            f"Attempt to connect phase {phase1}"
            + f" to phase {phase2} is encountered!"
        )
        super().__init__(self.message)


class IncompleteGeometryConfigurationDict(SeedBaseException):
    """Exceptions raised because of incomplete geometry configuration dict.

    Args:
        num_phase (NumPhase): Number of phase property
        geometry_dict (dict): Geometry metadata
    """

    def __init__(self, num_phase: NumPhase, geometry_dict: dict):
        self.message = f"{num_phase} key does not exist in {geometry_dict}"
        super().__init__(self.message)


class ConductorNotFoundForKdrop(SeedBaseException):
    """Exceptions raised because no conductor is found that satisfies the kdrop.

    Args:
        kdrop (float): Voltage drop property
    """

    def __init__(self, kdrop: float):
        self.message = (
            f"No conductor is found that satisfies kdrop of value {kdrop}"
        )
        super().__init__(self.message)


class MissingConfigurationAttribute(SeedBaseException):
    """Exceptions raised because attribute is missing
    in configuration yaml file."""


class UnsupportedFeatureError(SeedBaseException):
    """Exceptions raised because feature being requested
    is not yet supported or invalid type is passed."""


class CatalogNotFoundError(SeedBaseException):
    """Exceptions raised because catalog requested is not found."""


class InvalidInputError(SeedBaseException):
    """Exceptions raised because the input provided is not valid."""


class NotImplementedError(SeedBaseException):
    """Feature not implmeneted error."""
