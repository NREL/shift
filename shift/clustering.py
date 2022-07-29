from abc import ABC, abstractmethod
from constants import MAX_KMEANS_LOOP, MIN_NUM_CLUSTER
from exceptions import (MaxLoopReachedForKmeans, WrongInputUsed, 
    NumberOfClusterNotInRangeError, EarlyMethodCallError)
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import plotly.express as px
import pandas as pd
import numpy as np

""" Clustering abstract class """
class Clustering(ABC):

    @abstractmethod
    def get_clusters(self, x_array) -> dict:
        pass

    @abstractmethod
    def plot_clusters(self, x_array) -> dict:
        pass


class KmeansClustering(Clustering):

    def __init__(self, num_of_clusters='optimal'):
        self.num_of_clusters = num_of_clusters

        if isinstance(self.num_of_clusters, int):
            if self.num_of_clusters < MIN_NUM_CLUSTER:
                raise NumberOfClusterNotInRangeError(self.num_of_clusters)

    def plot_clusters(self):
        
        if hasattr(self, 'x_array') and hasattr(self, 'labels') and hasattr(self, 'clsuter_centers'):
            plot_data = {'x': [], 'y': [], 'label': []}
            for d, label in zip(self.x_array, self.labels):
                plot_data['x'].append(d[0])
                plot_data['y'].append(d[1])
                plot_data['label'].append(label)
            fig = px.scatter(pd.DataFrame(plot_data), x="x", y="y", color="label")
            fig.show()

        else:
            raise EarlyMethodCallError(f"Call get_clusters() method first before calling plot clusters method!")
    
    def plot_scores(self):
        if hasattr(self, 'sil_scores'):
            plot_data = {
                        'Number of clusters': [x[0] for x in self.sil_scores],
                        'Silhouette Value': [x[1] for x in self.sil_scores]
                    }
            fig = px.line(pd.DataFrame(plot_data), x="Number of clusters", y="Silhouette Value")
            fig.show()

        else:
            raise EarlyMethodCallError(f"Call get_clusters() method first before calling plot scores method!")
    


    def get_clusters(self, x_array) -> dict:

        self.x_array = x_array
        if isinstance(self.num_of_clusters, int):
            kmeans = KMeans(n_clusters=self.num_of_clusters, random_state=0).fit(x_array)

        else:
            if self.num_of_clusters== 'optimal':
                """ Let's try to find optimal number of clusters """
                self.sil_scores = []
                
                for k in range(2, MAX_KMEANS_LOOP):
                    kmeans = KMeans(n_clusters = k).fit(x_array)
                    labels = kmeans.labels_
                    self.sil_scores.append((k,silhouette_score(x_array, labels, metric = 'euclidean')))

                    # Break the loop if Silhouette score starts to decrease
                    if k>2:
                        if self.sil_scores[k-2][1] < self.sil_scores[k-3][1]:
                            break
                
                if k == MAX_KMEANS_LOOP-1:
                    raise MaxLoopReachedForKmeans()
                kmeans = KMeans(n_clusters=k-1, random_state=0).fit(x_array)
                self.optimal_clusters = k-1
            else:
                raise WrongInputUsed(f"For now  number of clusters can be either integer number or 'optimal' ! You provided {self.num_of_clusters}")
        self.labels = kmeans.labels_
        self.clsuter_centers = kmeans.cluster_centers_
        return {
                "labels" : self.labels,
                "centre": self.clsuter_centers
            }

if __name__ == '__main__':

    x_array = np.array([[1,2], [3,4], [5,6]])
    cluster = KmeansClustering('optimal')
    cluster.get_clusters(x_array)
    cluster.plot_scores()
    cluster.plot_clusters()