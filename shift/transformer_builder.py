"""
Abstract class to get the transformers and mapping between transformers and loads
"""
from abc import ABC, abstractmethod
from typing import List
from load import Load
import numpy as np
from clustering import Clustering
from utils import df_validator
import pandas as pd
import math
from transformer import Transformer
from constants import (
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
from enums import NumPhase, TransformerConnection, Phase
from exceptions import (
    PowerFactorNotInRangeError,
    AdjustmentFactorNotInRangeError,
    ZeroKVError,
    NegativeKVError,
    HTkVlowerthanLTkVError,
    EmptyCatalog,
    MultipleCatalogFoundError,
    PercentageNotInRangeError,
    OperationYearNotInRange,
)


""" Interface for getting transformer load mapping """


class TransformerLoadMapper(ABC):
    def __init__(
        self,
        loads: List[Load],
        diversity_factor_func,
        adjustment_factor: float = 1.25,
        planned_avg_annual_growth: float = 2,
        actual_avg_annual_growth: float = 4,
        actual_years_in_operation: float = 15,
        planned_years_in_operation: float = 10,
        power_factor: float = 0.9,
        catalog_type: str = "all",
    ):

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
    ):

        """Initial step is to compute maximum diversified demand"""
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
        pass

    def get_catalog_object(self, t_loads: List[Load], ht_kv, lt_kv):

        # Get maximum diversified demand (kW) and adjusted kW
        sum_of_noncoincident_peaks = sum([l.kw for l in t_loads])
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
                        f"Catalog does not exist for transformer of capacity above or equal to \
                        {kva} kVA with high tension voltage above or equal to {ht_kv} and \
                        above or equal to low tension voltage{lt_kv}"
                    )

            else:
                raise EmptyCatalog(
                    f"Catalog does not exist for transformer of capacity greater than \
                    {kva} kVA with high tension voltage greater than or equal to {ht_kv}"
                )

        else:
            raise EmptyCatalog(
                "Catalog does not exist for transformer of capacity above or equal to {kva} kVA"
            )

        return catalog_used


class SingleTransformerBuilder(TransformerLoadMapper):
    def __init__(
        self,
        loads: List[Load],
        longitude: float,
        latitude: float,
        diversity_factor_func,
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


""" Uses clustering algorithms to figure out transformer location """


class ClusteringBasedTransformerLoadMapper(TransformerLoadMapper):
    def __init__(
        self,
        loads: List[Load],
        clustering_object: Clustering,
        diversity_factor_func,
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

        """Prepare the data for clustering"""
        x_array = np.array(
            [[load.longitude, load.latitude] for load in self.loads]
        )

        """ Perform clustering operation based on x_data"""
        clusters = self.clustering_object.get_clusters(x_array)

        """ Mapping cluster centre to loads """
        cluster_to_customers = {tuple(c): [] for c in clusters["centre"]}
        for label, load in zip(clusters["labels"], self.loads):
            centre = tuple(clusters["centre"][label])
            cluster_to_customers[centre].append(load)

        """ Container to store all the transformers with all the mapping """
        self.transformers = {}
        for xfmr, t_loads in cluster_to_customers.items():

            """Now let's initialize the transformer with it's proper values"""
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


if __name__ == "__main__":

    pass
