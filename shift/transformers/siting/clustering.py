# standard imports
from typing import List, Dict, Tuple

# third-party imports
from sklearn.cluster import KMeans
import plotly.express as px
import pandas as pd
from pydantic import BaseModel, conint
import pydantic
import numpy as np

# internal imports
from shift.parcels.model import Building
from shift.transformers.model import Transformer


class ClusterOutputModel(BaseModel):
    labels: List[int]
    centers: List[List[float]]
    data: List[List[float]]


class KmeansClusteringModel(BaseModel):
    n_clusters: conint(gt=0)
    X: List[List[float]]
    random_state: int = 0
    n_init: str = "auto"


def kmeans_clustering(
    config: KmeansClusteringModel
) -> ClusterOutputModel:
    
    kmeans = KMeans(
        n_clusters=config.n_clusters, 
        random_state=config.random_state, 
        n_init=config.n_init
    ).fit(config.X)

    return pydantic.parse_obj_as(ClusterOutputModel, {
        'labels': list(kmeans.labels_),
        'centers': list([list(x) for x in kmeans.cluster_centers_]),
        'data': config.X
    })


class XFMRBuildingMappingInputModel(BaseModel):
    buildings: List[Building]
    typical_customers_per_xfmr: Dict[str, conint(gt=0)]


def get_xfmr_building_mapping(
    config: XFMRBuildingMappingInputModel
) -> List[Transformer]:
    
    transformers = []
    for cust_type, cust_per_xfmr in config.typical_customers_per_xfmr.items():
        
        filtered_buildings = [b for b in config.buildings \
                              if b.building_type == cust_type]
        
        n_clusters = int(len(filtered_buildings)/cust_per_xfmr)
        if n_clusters < 1:
            raise ValueError('Number of clusters is less than 1.')

        clusters = kmeans_clustering(KmeansClusteringModel(
                            n_clusters=n_clusters, 
                            X=[[b.longitude, b.latitude] for b in filtered_buildings]
                        ))
        
        for id, centre in enumerate(clusters.centers):
            indexes = np.array(clusters.labels) == id
            
            transformers.append(
                Transformer(
                    longitude=centre[0], 
                    latitude=centre[1], 
                    buildings=list(np.array(filtered_buildings)[indexes])
                )
            )
    
    return transformers
          

