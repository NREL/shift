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

""" Contains abstract and concrete classes for implementing clustering.

This module contains classes for managing clustering of location pairs.
The cluster center is used as reference location to figure out
transformer siting. In the process mapping between
cluster center and locations is also created.

Examples:
    Get the clusters from given list of location pairs and plot it.

    >>> from shift.clustering import KmeansClustering
    >>> import numpy as np
    >>> x_array = np.array([[1,2], [3,4], [5,6]])
    >>> cluster = KmeansClustering(2)
    >>> cluster.get_clusters(x_array)
    >>> cluster.plot_clusters()
"""

from abc import ABC, abstractmethod
from typing import List, Union

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import plotly.express as px
import pandas as pd

from shift.constants import MAX_KMEANS_LOOP, MIN_NUM_CLUSTER
from shift.exceptions import (
    MaxLoopReachedForKmeans,
    WrongInputUsed,
    NumberOfClusterNotInRangeError,
    EarlyMethodCallError,
)


class Clustering(ABC):
    """Abstract interface for implementing clustering subclass"""

    @abstractmethod
    def get_clusters(self, x_array: List[list]) -> dict:
        """Method for creating and returning clusters.

        Subclass inhereting this class must implement this method and should
        return the clusters in the following format.
        ```json
        {"labels": [0,1,1], "centre": [(0,0), (2,2)]}
        ```

        Returns:
            dict: A dictionary containing cluster labels
                and cluster centers
        """
        pass

    @abstractmethod
    def plot_clusters(self) -> None:
        """Method to plot clusters

        Raises:
            EarlyMethodCallError: If this method is called before calling
                `get_clusters` method.
        """
        pass


class KmeansClustering(Clustering):
    """Class implementing Kmeans clustering.

    Attributes:
        num_of_clusters (Union[str, int]): Number of clusters to be used
        cluster_centers (List[Sequece]): List of cluster center
        labels (list): Integer label for each location indicating which
            cluster they belong to
        xarray (List[Sequece]): List of location pairs for which
            clustering is performed
        optimal_clusters (int): Optimal number of clusters created if
            `num_of_clusters` passed is `optimal`
    """

    def __init__(self, num_of_clusters: Union[str, int] = "optimal") -> None:
        """Constructor for `KmeansClustering` class.

        Args:
            num_of_clusters (Union[str, int]): Number of clusters to be used

        Raises:
            NumberOfClusterNotInRangeError: if `num_of_clusters` speecified is
                less than MIN_NUM_CLUSTER constants module.
        """
        self.num_of_clusters = num_of_clusters

        if isinstance(self.num_of_clusters, int):
            if self.num_of_clusters < MIN_NUM_CLUSTER:
                raise NumberOfClusterNotInRangeError(self.num_of_clusters)

    def plot_clusters(self):
        """Refer to the base class for details."""

        if (
            hasattr(self, "x_array")
            and hasattr(self, "labels")
            and hasattr(self, "cluster_centers")
        ):
            plot_data = {"x": [], "y": [], "label": []}
            for d, label in zip(self.x_array, self.labels):
                plot_data["x"].append(d[0])
                plot_data["y"].append(d[1])
                plot_data["label"].append(label)
            fig = px.scatter(
                pd.DataFrame(plot_data), x="x", y="y", color="label"
            )
            fig.show()

        else:
            raise EarlyMethodCallError(
                "Call get_clusters() method first before "
                + "calling plot clusters method!"
            )

    def plot_scores(self):
        """Method for plotting scores

        Note:
            Only use this method if `num_of_clusters` passed is `optimal`.

        Raises:
            EarlyMethodCallError: If called before calling
                `get_clusters` method.
        """

        if hasattr(self, "sil_scores"):
            plot_data = {
                "Number of clusters": [x[0] for x in self.sil_scores],
                "Silhouette Value": [x[1] for x in self.sil_scores],
            }
            fig = px.line(
                pd.DataFrame(plot_data),
                x="Number of clusters",
                y="Silhouette Value",
            )
            fig.show()

        else:
            raise EarlyMethodCallError(
                "Call get_clusters() method first before calling "
                + "plot scores method!"
            )

    def get_clusters(self, x_array: list) -> dict:
        """Refer to the base class for details.

        Raises:
            WrongInputUsed: If the number of clusters passed is invalid.
        """

        self.x_array = x_array
        if isinstance(self.num_of_clusters, int):
            kmeans = KMeans(
                n_clusters=self.num_of_clusters, random_state=0
            ).fit(x_array)

        else:
            if self.num_of_clusters == "optimal":
                # Let's try to find optimal number of clusters
                self.sil_scores = []

                for k in range(2, MAX_KMEANS_LOOP):
                    kmeans = KMeans(n_clusters=k).fit(x_array)
                    labels = kmeans.labels_
                    self.sil_scores.append(
                        (
                            k,
                            silhouette_score(
                                x_array, labels, metric="euclidean"
                            ),
                        )
                    )

                    # Break the loop if Silhouette score starts to decrease
                    if k > 2:
                        if (
                            self.sil_scores[k - 2][1]
                            < self.sil_scores[k - 3][1]
                        ):
                            break

                if k == MAX_KMEANS_LOOP - 1:
                    raise MaxLoopReachedForKmeans()
                kmeans = KMeans(n_clusters=k - 1, random_state=0).fit(x_array)
                self.optimal_clusters = k - 1
            else:
                raise WrongInputUsed(
                    "For now  number of clusters can be either integer "
                    + "number or 'optimal'!"
                    + f"You provided {self.num_of_clusters}"
                )
        self.labels = kmeans.labels_
        self.cluster_centers = kmeans.cluster_centers_
        return {"labels": self.labels, "centre": self.cluster_centers}
