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

""" This module contains classes for building transformers. """

from abc import ABC, abstractmethod
from typing import List, Callable
import math

import numpy as np
import pandas as pd

from shift.load import Load
from shift.clustering import Clustering
from shift.utils import df_validator
from shift.transformer import Transformer
from shift.constants import (
    MIN_POWER_FACTOR,
    MAX_POWER_FACTOR,
    MIN_ADJUSTMENT_FACTOR,
    MAX_ADJUSTMENT_FACTOR,
    TRANSFORMER_CATALAOG_SCHEMA,
    MIN_PERCENTAGE,
    MAX_PERCENTAGE,
    MIN_YEAR_OPERATION,
    MAX_YEAR_OPERATION,
    TRANSFORMER_CATALOG_FILE,
)
from shift.enums import NumPhase, TransformerConnection, Phase
from shift.exceptions import (
    PowerFactorNotInRangeError,
    AdjustmentFactorNotInRangeError,
    ZeroKVError,
    NegativeKVError,
    HTkVlowerthanLTkVError,
    EmptyCatalog,
    PercentageNotInRangeError,
    OperationYearNotInRange,
)


class TransformerLoadMapper(ABC):
    """Interface for getting transformer load mapping.

    Attributes:
        loads (List[Load]): List of loads
        diversity_factor_func (Callable): Callable to compute diversity factor
        adjustment_factor (float): Adjustment factor for adjusting kva
        planned_avg_annual_growth (float): Planned average annual load
            growth rate in percentage
        actual_avg_annual_growth (float): Actual average annual load
            growth rate in percentage
        actual_years_in_operation (float): Actual years in operation
        planned_years_in_operation (float): Planned years in operation
        power_factor (float): Power factor used to compute kva
        catalog_type (str): Catalog type used for choosing transformer
        trans_catalog (pd.DataFrame): Dataframe containing transformer catalogs
    """

    def __init__(
        self,
        loads: List[Load],
        diversity_factor_func: Callable[[float], float],
        adjustment_factor: float = 1.25,
        planned_avg_annual_growth: float = 2,
        actual_avg_annual_growth: float = 4,
        actual_years_in_operation: float = 15,
        planned_years_in_operation: float = 10,
        power_factor: float = 0.9,
        catalog_type: str = "all",
    ) -> None:
        """Constructor for `TransformerLoadMapper` class.

        Args:
            loads (List[Load]): List of loads
            diversity_factor_func (Callable[[float], float]): Callable to
                compute diversity factor
            adjustment_factor (float): Adjustment factor for adjusting kva
            planned_avg_annual_growth (float): Planned average annual load
                growth rate in percentage
            actual_avg_annual_growth (float): Actual average annual load
                growth rate in percentage
            actual_years_in_operation (float): Actual years in operation
            planned_years_in_operation (float): Planned years in operation
            power_factor (float): Power factor used to compute kva
            catalog_type (str): Catalog type used for choosing transformer

        Raises:
            PercentageNotInRangeError: If invalid percentage is used
            OperationYearNotInRange: If invalid operation year is used
            AdjustmentFactorNotInRangeError: If invalid adjustment
                factor is used
            PowerFactorNotInRangeError: If invalid power factor is used
            EmptyCatalog: If catalog is empty for given type
        """

        self.loads = loads
        self.diversity_factor_func = diversity_factor_func
        self.planned_avg_annual_growth = planned_avg_annual_growth
        self.actual_avg_annual_growth = actual_avg_annual_growth
        self.actual_years_in_operation = actual_years_in_operation
        self.planned_years_in_operation = planned_years_in_operation
        self.power_factor = power_factor

        if (
            self.planned_avg_annual_growth < MIN_PERCENTAGE
            or self.planned_avg_annual_growth > MAX_PERCENTAGE
        ):
            raise PercentageNotInRangeError(self.planned_avg_annual_growth)

        if (
            self.actual_avg_annual_growth < MIN_PERCENTAGE
            or self.actual_avg_annual_growth > MAX_PERCENTAGE
        ):
            raise PercentageNotInRangeError(self.actual_avg_annual_growth)

        if (
            self.actual_years_in_operation < MIN_YEAR_OPERATION
            or self.actual_years_in_operation > MAX_YEAR_OPERATION
        ):
            raise OperationYearNotInRange(self.actual_years_in_operation)

        if (
            self.planned_years_in_operation < MIN_YEAR_OPERATION
            or self.planned_years_in_operation > MAX_YEAR_OPERATION
        ):
            raise OperationYearNotInRange(self.planned_years_in_operation)

        self.adjustment_factor = adjustment_factor
        if (
            self.adjustment_factor < MIN_ADJUSTMENT_FACTOR
            or self.adjustment_factor > MAX_ADJUSTMENT_FACTOR
        ):
            raise AdjustmentFactorNotInRangeError(self.adjustment_factor)

        if (
            self.power_factor < MIN_POWER_FACTOR
            or self.power_factor > MAX_POWER_FACTOR
        ):
            raise PowerFactorNotInRangeError(self.power_factor)

        self.trans_catalog = pd.read_excel(TRANSFORMER_CATALOG_FILE)

        df_validator(TRANSFORMER_CATALAOG_SCHEMA, self.trans_catalog)
        if catalog_type != "all":
            self.trans_catalog = self.trans_catalog.loc[
                self.trans_catalog["type"] == type
            ]
            if self.trans_catalog.empty:
                raise EmptyCatalog(
                    f"Catalog of type {type} not found in transformer.xlsx file"
                )

    def compute_transformer_kva_capacity(
        self, non_coincident_peak: float, num_of_customers: int
    ) -> float:
        """Method for computing transformer capacity.

        Args:
            non_coincident_peak (float): Non coincident peak
            num_of_customers (int): Number of customers

        Returns:
            float: Transformer size
        """

        # Initial step is to compute maximum diversified demand
        div_factor = (
            self.diversity_factor_func(num_of_customers)
            if num_of_customers > 1
            else 1
        )
        max_diversified_demand = non_coincident_peak / div_factor
        max_diversified_kva = (
            max_diversified_demand * self.adjustment_factor / self.power_factor
        )

        original_max_diversified_kva = max_diversified_kva / math.pow(
            1 + self.actual_avg_annual_growth / 100,
            self.actual_years_in_operation,
        )
        trafo_size = original_max_diversified_kva * math.pow(
            1 + self.planned_avg_annual_growth / 100,
            self.planned_years_in_operation,
        )
        return trafo_size

    @abstractmethod
    def get_transformer_load_mapping(self) -> dict:
        """Abstract method for returning transformer to loads mapping."""
        pass

    def get_catalog_object(
        self, t_loads: List[Load], ht_kv: float, lt_kv: float
    ) -> dict:
        """Method for getting transformet catalog.

        Args:
            t_loads (List[Load]): List of `Load` instances
            ht_kv (float): High tension kV
            lt_kv (float): Low tension kv

        Raises:
            EmptyCatalog: If transformer catalog is not found

        Returns:
            dict: Transformer record
        """

        # Get maximum diversified demand (kW) and adjusted kW
        sum_of_noncoincident_peaks = sum(l.kw for l in t_loads)
        kva = self.compute_transformer_kva_capacity(
            sum_of_noncoincident_peaks, len(t_loads)
        )

        # Filter by capacity above kva capacity
        catalog = self.trans_catalog[self.trans_catalog["kva"] >= kva]
        if not catalog.empty:

            # Filter by high voltage
            catalog = catalog[catalog["ht_kv"] >= ht_kv]
            if not catalog.empty:

                # Filter by low voltage
                catalog = catalog[catalog["lt_kv"] >= lt_kv]

                if not catalog.empty:
                    catalog_used = catalog.loc[
                        catalog["kva"].idxmin()
                    ].to_dict()
                else:
                    raise EmptyCatalog(
                        "Catalog does not exist for transformer of"
                        + " capacity above or equal to"
                        + f"{kva} kVA with high tension voltage above or "
                        + f"equal to {ht_kv} and "
                        + f"above or equal to low tension voltage{lt_kv}"
                    )

            else:
                raise EmptyCatalog(
                    "Catalog does not exist for transformer of "
                    + "capacity greater than "
                    + f"{kva} kVA with high tension voltage greater "
                    + f"than or equal to {ht_kv}"
                )

        else:
            raise EmptyCatalog(
                "Catalog does not exist for transformer"
                + "of capacity above or equal to {kva} kVA"
            )

        return catalog_used


class SingleTransformerBuilder(TransformerLoadMapper):
    """Class for managing building of single transformer
    used to build substation transformer.

    Refer to base class for attributes passed to base class.

    Attributes:
        ht_kv (float): High tension side kV
        lt_kv (float): Low tension side kV
        num_phase (NumPhase): NumPhase instance
        ht_conn (TransformerConnection): TransformerConnection
            instance for high tension side
        lt_conn (TransformerConnection): TransformerConnection
            instance for low tension side
        ht_phase (Phase): Phase instance for high tension side
        lt_phase (Phase): Phase instance for low tension side
        longitude (float): Longitude property of transformer
        latitude (float): Latitude property of transformer
    """

    def __init__(
        self,
        loads: List[Load],
        longitude: float,
        latitude: float,
        diversity_factor_func: Callable[[float], float],
        ht_kv: float,
        lt_kv: float,
        ht_conn: TransformerConnection,
        lt_conn: TransformerConnection,
        ht_phase: Phase,
        lt_phase: Phase,
        num_phase: NumPhase,
        catalog_type="all",
        power_factor: float = 1.0,
        adjustment_factor: float = 1.25,
        planned_avg_annual_growth: float = 2,
        actual_avg_annual_growth: float = 4,
        actual_years_in_operation: float = 15,
        planned_years_in_operation: float = 10,
    ) -> None:
        """Constructor for `SingleTransformerBuilder` class.

        Args:
            ht_kv (float): High tension side kV
            lt_kv (float): Low tension side kV
            num_phase (NumPhase): NumPhase instance
            ht_conn (TransformerConnection): TransformerConnection
                instance for high tension side
            lt_conn (TransformerConnection): TransformerConnection
                instance for low tension side
            ht_phase (Phase): Phase instance for high tension side
            lt_phase (Phase): Phase instance for low tension side
            longitude (float): Longitude property of transformer
            latitude (float): Latitude property of transformer

        Raises:
            ZeroKVError: If kv specified is zero
            NegativeKVError: If kv specified is negative
            HTkVlowerthanLTkVError: If high tension kv used
                is less than low tension kv
        """

        super().__init__(
            loads,
            diversity_factor_func,
            adjustment_factor,
            planned_avg_annual_growth,
            actual_avg_annual_growth,
            actual_years_in_operation,
            planned_years_in_operation,
            power_factor,
            catalog_type,
        )

        self.ht_kv = ht_kv
        self.lt_kv = lt_kv
        self.num_phase = num_phase
        self.ht_conn = ht_conn
        self.lt_conn = lt_conn
        self.ht_phase = ht_phase
        self.lt_phase = lt_phase
        self.longitude = longitude
        self.latitude = latitude

        for kv in [self.ht_kv, self.lt_kv]:
            if kv == 0:
                raise ZeroKVError
            if kv < 0:
                raise NegativeKVError

        if self.ht_kv < self.lt_kv:
            raise HTkVlowerthanLTkVError(self.ht_kv, self.lt_kv)

    def get_transformer_load_mapping(self) -> dict:
        """Refer to base class for more details."""

        self.transformers = {}
        catalog_used = self.get_catalog_object(
            self.loads, self.ht_kv, self.lt_kv
        )
        trans = Transformer()
        trans.latitude = self.latitude
        trans.longitude = self.longitude
        trans.name = f"{self.longitude}_{self.latitude}_transformer"
        trans.primary_kv = self.ht_kv
        trans.secondary_kv = self.lt_kv
        trans.pct_r = catalog_used["percentage_resistance"]
        trans.xhl = catalog_used["percentage_reactance"]
        trans.pct_noloadloss = catalog_used["percentage_no_load_loss"]
        trans.num_phase = self.num_phase
        trans.primary_con = self.ht_conn
        trans.kva = catalog_used["kva"]
        trans.secondary_con = self.lt_conn
        trans.primary_phase = self.ht_phase
        trans.secondary_phase = self.lt_phase
        self.transformers[trans] = self.loads

        return self.transformers


class ClusteringBasedTransformerLoadMapper(TransformerLoadMapper):
    """Uses clustering algorithms to figure out transformer location.

    Refer to base class for attributes passed to base class.

    Attributes:
        ht_kv (float): High tension side kV
        lt_kv (float): Low tension side kV
        num_phase (NumPhase): NumPhase instance
        ht_conn (TransformerConnection): TransformerConnection
            instance for high tension side
        lt_conn (TransformerConnection): TransformerConnection
            instance for low tension side
        ht_phase (Phase): Phase instance for high tension side
        lt_phase (Phase): Phase instance for low tension side
        clustering_object (Clustering): Clustering instance
    """

    def __init__(
        self,
        loads: List[Load],
        clustering_object: Clustering,
        diversity_factor_func: Callable[[float], float],
        ht_kv: float,
        lt_kv: float,
        ht_conn: TransformerConnection,
        lt_conn: TransformerConnection,
        ht_phase: Phase,
        lt_phase: Phase,
        num_phase: NumPhase,
        catalog_type="all",
        power_factor: float = 1.0,
        adjustment_factor: float = 1.25,
        planned_avg_annual_growth: float = 2,
        actual_avg_annual_growth: float = 4,
        actual_years_in_operation: float = 15,
        planned_years_in_operation: float = 10,
    ):

        """Constructor for `ClusteringBasedTransformerLoadMapper` class.

        Args:
            ht_kv (float): High tension side kV
            lt_kv (float): Low tension side kV
            num_phase (NumPhase): NumPhase instance
            ht_conn (TransformerConnection): TransformerConnection
                instance for high tension side
            lt_conn (TransformerConnection): TransformerConnection
                instance for low tension side
            ht_phase (Phase): Phase instance for high tension side
            lt_phase (Phase): Phase instance for low tension side
            clustering_object (Clustering): Clustering instance

        Raises:
            ZeroKVError: If kv specified is zero
            NegativeKVError: If kv specified is negative
            HTkVlowerthanLTkVError: If high tension kv used
                is less than low tension kv
        """

        super().__init__(
            loads,
            diversity_factor_func,
            adjustment_factor,
            planned_avg_annual_growth,
            actual_avg_annual_growth,
            actual_years_in_operation,
            planned_years_in_operation,
            power_factor,
            catalog_type,
        )

        self.clustering_object = clustering_object
        self.ht_kv = ht_kv
        self.lt_kv = lt_kv
        self.num_phase = num_phase
        self.ht_conn = ht_conn
        self.lt_conn = lt_conn
        self.ht_phase = ht_phase
        self.lt_phase = lt_phase

        for kv in [self.ht_kv, self.lt_kv]:
            if kv == 0:
                raise ZeroKVError
            if kv < 0:
                raise NegativeKVError

        if self.ht_kv < self.lt_kv:
            raise HTkVlowerthanLTkVError(self.ht_kv, self.lt_kv)

    def get_transformer_load_mapping(self) -> dict:
        """Refer to base class for more details."""

        # Prepare the data for clustering
        x_array = np.array(
            [[load.longitude, load.latitude] for load in self.loads]
        )

        # Perform clustering operation based on x_data
        clusters = self.clustering_object.get_clusters(x_array)

        # Mapping cluster centre to loads """
        cluster_to_customers = {tuple(c): [] for c in clusters["centre"]}
        for label, load in zip(clusters["labels"], self.loads):
            centre = tuple(clusters["centre"][label])
            cluster_to_customers[centre].append(load)

        # Container to store all the transformers with all the mapping
        self.transformers = {}
        for xfmr, t_loads in cluster_to_customers.items():

            # Now let's initialize the transformer with it's proper values
            catalog_used = self.get_catalog_object(
                t_loads, self.ht_kv, self.lt_kv
            )
            trans = Transformer()
            trans.latitude = xfmr[1]
            trans.longitude = xfmr[0]
            trans.name = f"{xfmr[0]}_{xfmr[1]}_transformer"
            trans.primary_kv = self.ht_kv
            trans.secondary_kv = self.lt_kv
            trans.pct_r = catalog_used["percentage_resistance"]
            trans.xhl = catalog_used["percentage_reactance"]
            trans.pct_noloadloss = catalog_used["percentage_no_load_loss"]
            trans.num_phase = self.num_phase
            trans.primary_con = self.ht_conn
            trans.kva = catalog_used["kva"]
            trans.secondary_con = self.lt_conn
            trans.primary_phase = self.ht_phase
            trans.secondary_phase = self.lt_phase
            self.transformers[trans] = t_loads
        return self.transformers
