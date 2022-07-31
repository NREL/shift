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

""" This module contains builder for building load models
for distribution system.

Examples

    >>> from shift.load_builder import (
        ConstantPowerFactorBuildingGeometryLoadBuilder)
    >>> from shift.geometry import BuildingGeometry
    >>> g1 = BuildingGeometry()
    >>> g1.latitude = 56.567
    >>> g1.longitude = 67.8889
    >>> g1.area = 2
    >>> g2 = BuildingGeometry()
    >>> g2.latitude = 56.567
    >>> g2.longitude = 67.8889
    >>> g2.area = 2
    >>> builder = ConstantPowerFactorBuildingGeometryLoadBuilder(g1,
        RandomPhaseAllocator(50, 0, 50, [g1,g2]),
        ProportionalBuildingAreaToConsumptionConverter(2,5,0,10),
        SimpleVoltageSetter(13.2),DefaultConnSetter(),
        1.0)
    >>> b = LoadBuilderEngineer(builder)
    >>> print(b.get_load())
"""

from abc import ABC, abstractmethod
import random
from typing import List
import math

from shift.geometry import Geometry
from shift.load import ConstantPowerFactorLoad, Load
from shift.utils import get_point_from_curve
from shift.exceptions import (
    PercentageSumNotHundred,
    NegativeKVError,
    ZeroKVError,
    InvalidInputError,
)
from shift.enums import Phase, NumPhase, LoadConnection


class BuildingAreaToConsumptionConverter(ABC):
    """Interface for computing power consumption from building area."""

    @abstractmethod
    def convert(self, area: float) -> float:
        """Abstract method for computing the power consumption.

        Args:
            area (float): Building area

        Returns:
            float: Power consumption in kW
        """
        pass


class PiecewiseBuildingAreaToConsumptionConverter(
    BuildingAreaToConsumptionConverter
):
    """Class for handling computation of power consumption
    using piecewide linear function.

    Attributes:
        curve (List[list]): Piecewise linear function e.g. [[1,2], [3,4]]
    """

    def __init__(self, area_to_kw_curve: List[list]) -> None:
        """Constructor for `PiecewiseBuildingAreaToConsumptionConverter` class.

        Args:
            area_to_kw_curve (List[list]): Piecewise linear
                function e.g. [[1,2], [3,4]]
        """
        self.curve = area_to_kw_curve

    def convert(self, area: float) -> float:
        """Refer to base class for more details."""
        return get_point_from_curve(self.curve, area)


class ProportionalBuildingAreaToConsumptionConverter(
    BuildingAreaToConsumptionConverter
):
    """Class for handling computation of power consumption
    using proportional allocation method.

    Attributes:
        min_kw (float): Minimum kw to be assigned
        max_kw (float): Maximum kw to be assigned
        max_area (float): Maximum area of all the buildings
        min_area (float): Minimum area of all the buildings
    """

    def __init__(
        self, min_kw: float, max_kw: float, max_area: float, min_area: float
    ) -> None:
        """Constructor for
        `ProportionalBuildingAreaToConsumptionConverter` class.

        Args:
            min_kw (float): Minimum kw to be assigned
            max_kw (float): Maximum kw to be assigned
            max_area (float): Maximum area of all the buildings
            min_area (float): Minimum area of all the buildings

        Raises:
            InvalidInputError: If min_kw is greater than or equal to max_kw
        """
        self.min_kw = min_kw
        self.max_kw = max_kw
        self.max_area = max_area
        self.min_area = min_area

        if self.min_kw >= self.max_kw:
            raise InvalidInputError(
                f"Min kW  {min_kw} is greater than or equal to Max kW {max_kw}"
            )

    def convert(self, area: float) -> float:
        """Refer to base class for more details."""
        if self.max_area != 0:
            kw = self.min_kw + (self.max_kw - self.min_kw) * (
                area - self.min_area
            ) / (self.max_area - self.min_area)
        else:
            kw = self.min_kw

        return kw


class PhaseAllocator(ABC):
    """Interface for allocating phase."""

    @abstractmethod
    def get_phase(self, geometry: Geometry) -> Phase:
        """Abstract method for getting a phase.

        Args:
            geometry (Geometry): Geometry instance for
                which phase is to be determined

        Returns:
            Phase: Phase instance for the geometry
        """
        pass

    @abstractmethod
    def get_num_phase(self, geometry: Geometry) -> NumPhase:
        """Abstract method for getting number of phase.

        Args:
            geometry (Geometry): Geometry instance for
                which num_phase is to be determined

        Returns:
            NumPhase: NumPhase instance for the geometry
        """
        pass


class RandomPhaseAllocator(PhaseAllocator):
    """Allocates the phase to all geometries uniformly randomly.

    Attributes:
        pct_single_phases (float): Percentage of single phase geometries
        pct_two_phases (float): Percentage of two phase geometries
        pct_three_phases (float): Percentage of three phase geometries
        geometries (List[Geometry]): List of Geometry objects
        geometry_to_phase (dict): A dictionary holding the phase for geometries
    """

    def __init__(
        self,
        pct_single_phases: float,
        pct_two_phases: float,
        pct_three_phases: float,
        geometries: List[Geometry],
    ) -> None:
        """Constructor for `RandomPhaseAllocator` class.

        Args:
            pct_single_phases (float): Percentage of single phase geometries
            pct_two_phases (float): Percentage of two phase geometries
            pct_three_phases (float): Percentage of three phase geometries
            geometries (List[Geometry]): List of Geometry objects

        Raises:
            PercentageSumNotHundred: If the sume of percentages is not 100
        """

        self.pct_single_phases = pct_single_phases
        self.pct_two_phases = pct_two_phases
        self.pct_three_phases = pct_three_phases
        self.geometries = geometries

        if pct_single_phases + pct_two_phases + pct_three_phases != 100:
            raise PercentageSumNotHundred(
                pct_single_phases + pct_two_phases + pct_three_phases
            )

        random.shuffle(self.geometries)

        three_phase_geometries = self.geometries[
            : int(len(self.geometries) * self.pct_three_phases / 100)
        ]
        self.geometry_to_phase = {g: Phase.ABCN for g in three_phase_geometries}
        self.geometry_to_numphase = {
            g: NumPhase.THREE for g in three_phase_geometries
        }

        single_phases = [Phase.AN, Phase.BN, Phase.CN]
        two_phases = [Phase.AB, Phase.BC, Phase.CA]

        two_phase_geometries = self.geometries[
            int(len(self.geometries) * self.pct_three_phases / 100) : int(
                len(self.geometries) * self.pct_two_phases / 100
            )
        ]
        self.geometry_to_phase.update(
            {g: random.choice(two_phases) for g in two_phase_geometries}
        )
        self.geometry_to_numphase.update(
            {g: NumPhase.TWO for g in two_phase_geometries}
        )

        single_phase_geometries = [
            g for g in self.geometries if g not in self.geometry_to_phase
        ]
        self.geometry_to_phase.update(
            {g: random.choice(single_phases) for g in single_phase_geometries}
        )
        self.geometry_to_numphase.update(
            {g: NumPhase.SINGLE for g in single_phase_geometries}
        )

    def get_phase(self, geometry: Geometry) -> Phase:
        """Refer to the base class for more details."""
        return self.geometry_to_phase[geometry]

    def get_num_phase(self, geometry: Geometry) -> NumPhase:
        """Refer to the base class for more details."""
        return self.geometry_to_numphase[geometry]


class VoltageSetter(ABC):
    """Interface for setting voltage for loads."""

    @abstractmethod
    def get_kv(self, load: Load) -> float:
        """Abstract method for getting voltage level for load object.

        Args:
            load (Load): Load instance

        Returns:
            float: Voltage in kV for load object
        """
        pass


class SimpleVoltageSetter:
    """Simple voltage setter for setting kv for loads.

    Attributes:
        line_to_line_voltage (float): Line to line voltage in kV
        voltage_dict (dict): NumPhase to voltage mapper
    """

    def __init__(self, line_to_line_voltage: float) -> None:
        """Constructor for `SimpleVoltageSetter` class.

        Args:
            line_to_line_voltage (float): Line to line voltage in kV

        Raises:
            NegativeKVError: If the `line_to_line_voltage` is negative
            ZeroKVError: if the `line_to_line_voltage` is 0
        """

        self.line_to_line_voltage = line_to_line_voltage
        if self.line_to_line_voltage < 0:
            raise NegativeKVError(self.line_to_line_voltage)

        if self.line_to_line_voltage == 0:
            raise ZeroKVError()

        self.voltage_dict = {
            NumPhase.SINGLE: round(self.line_to_line_voltage / math.sqrt(3), 3),
            NumPhase.TWO: self.line_to_line_voltage,
            NumPhase.THREE: self.line_to_line_voltage,
        }

    def get_kv(self, load: Load) -> float:
        """Refer to the base class for more details."""
        return self.voltage_dict[load.num_phase]


class ConnSetter(ABC):
    """Interface for setting the connection type for load object."""

    @abstractmethod
    def get_conn(self, load: Load) -> LoadConnection:
        """Abstract method for setting connection type for load object.

        Args:
            load (Load): Load instance

        Returns:
            LoadConnection: Connection type for the load
        """
        pass


class DefaultConnSetter(ConnSetter):
    """Class for handling default connection type."""

    def get_conn(self, load: Load) -> LoadConnection:
        """Refer to the base class for more details."""
        return (
            LoadConnection.DELTA
            if load.num_phase == NumPhase.TWO
            else LoadConnection.STAR
        )


class LoadBuilder(ABC):
    """Builder interface for converting geometries to power system loads."""

    @abstractmethod
    def set_name_and_location(self) -> None:
        """Abstract method for setting name and location."""
        pass

    @abstractmethod
    def set_power_data(self) -> None:
        """Abstract method for setting the power consumption for load."""
        pass

    @abstractmethod
    def set_phase_data(self) -> None:
        """Abstract method for setting phase to load."""
        pass

    @abstractmethod
    def set_kv_and_conn(self) -> None:
        """Abstract methid for setting kv and connection."""
        pass


class GeometryLoadBuilder(LoadBuilder):
    """Concrete implementation for converting geometry to load.

    Attributes:
        geometry (Geometry): Geometry instance
        phaseallocator (PhaseAllocator): PhaseAllocator instance
        kv_setter (VoltageSetter): VoltageSetter instance
        conn_setter (conn_setter): ConnSetter Instance
        load (Load): Load instance
    """

    def __init__(
        self,
        geometry: Geometry,
        phaseallocator: PhaseAllocator,
        kv_setter: VoltageSetter,
        conn_setter: ConnSetter,
        load: Load,
    ) -> None:
        """Constructor for GeometryLoadBuilder class.

        Args:
            geometry (Geometry): Geometry instance
            phaseallocator (PhaseAllocator): PhaseAllocator instance
            kv_setter (VoltageSetter): VoltageSetter instance
            conn_setter (conn_setter): ConnSetter Instance
            load (Load): Load instance
        """

        self.geometry = geometry
        self.load = load
        self.phase_allocator = phaseallocator
        self.kvsetter = kv_setter
        self.connsetter = conn_setter

    def set_name_and_location(self) -> None:
        """Refer to base class for more details."""
        self.load.name = (
            f"{self.geometry.longitude}_{self.geometry.latitude}_load"
        )
        self.load.latitude = self.geometry.latitude
        self.load.longitude = self.geometry.longitude

    def set_power_data(self) -> None:
        """Refer to base class for more details."""
        pass

    def set_phase_data(self) -> None:
        """Refer to base class for more details."""
        self.load.phase = self.phase_allocator.get_phase(self.geometry)
        self.load.num_phase = self.phase_allocator.get_num_phase(self.geometry)

    def set_kv_and_conn(self) -> None:
        """Refer to base class for more details."""
        self.load.kv = self.kvsetter.get_kv(self.load)
        self.load.conn_type = self.connsetter.get_conn(self.load)


class ConstantPowerFactorBuildingGeometryLoadBuilder(GeometryLoadBuilder):
    """Concerete implementation for building constant
    power factor type load from geometry object.

    Refer to the base class for base attributes.

    Attributes:
        power_factor (float): Power factor
        area_converter (BuildingAreaToConsumptionConverter):
            BuildingAreaToConsumptionConverter instance
    """

    def __init__(
        self,
        geometry: Geometry,
        phaseallocator: PhaseAllocator,
        area_converter: BuildingAreaToConsumptionConverter,
        kv_setter: VoltageSetter,
        conn_setter: ConnSetter,
        power_factor: float,
    ) -> None:
        """Constructor for
        `ConstantPowerFactorBuildingGeometryLoadBuilder` class.

        Refer to base class for base arguments.

        Args:
            area_converter (BuildingAreaToConsumptionConverter):
                BuildingAreaToConsumptionConverter instance
            power_factor (float): Power factor
        """

        super().__init__(
            geometry,
            phaseallocator,
            kv_setter,
            conn_setter,
            ConstantPowerFactorLoad(),
        )
        self.power_factor = power_factor
        self.area_converter = area_converter

    def set_power_data(self) -> None:
        """Refer to base class for more details."""
        self.load.pf = self.power_factor
        self.load.kw = self.area_converter.convert(self.geometry.area)


class ConstantPowerFactorSimpleLoadGeometryLoadBuilder(GeometryLoadBuilder):
    """Concerete implementation for building constant power
    factor type load from simple load point geometry object.

    Refer to base class for base attributes.

    Attributes:
        power_factor (float): Power factor
    """

    def __init__(
        self,
        geometry: Geometry,
        phaseallocator: PhaseAllocator,
        kv_setter: VoltageSetter,
        conn_setter: ConnSetter,
        power_factor: float,
    ) -> None:
        """Constructor for
        `ConstantPowerFactorSimpleLoadGeometryLoadBuilder` class.

        Refer to base class for base arguments.

        Args:
            power_factor (float): Power factor
        """

        super().__init__(
            geometry,
            phaseallocator,
            kv_setter,
            conn_setter,
            ConstantPowerFactorLoad(),
        )
        self.power_factor = power_factor

    def set_power_data(self) -> None:
        """Refer to base class for more details."""
        self.load.pf = self.power_factor
        self.load.kw = self.geometry.kw


class LoadBuilderEngineer:
    """Director for building loads.

    Attributes:
        builder (LoadBuilder): LoadBuilder instance
    """

    def __init__(self, builder: LoadBuilder) -> None:
        """Constructor for `LoadBuilderEngineer` class.

        Args:
            builder (LoadBuilder): LoadBuilder instance
        """
        self.builder = builder
        self.builder.set_name_and_location()
        self.builder.set_power_data()
        self.builder.set_phase_data()
        self.builder.set_kv_and_conn()

    def get_load(self) -> Load:
        """Returns a `Load` instance."""
        return self.builder.load
