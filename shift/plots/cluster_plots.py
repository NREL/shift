import plotly.graph_objects as go
from shift.clustering import ClusterOutputModel
import numpy as np


def plot_cluster(cluster: ClusterOutputModel):

    fig = go.Figure()
    for id, _ in enumerate(cluster.centers):
        
        indexes = np.array(cluster.labels) == id
        builds = np.array(cluster.data)[indexes]
   
        fig.add_trace(
                    go.Scattermapbox(
                        mode="markers",
                        lon=[b[1] for b in builds],
                        lat=[b[0] for b in builds],
                        name=f"{id}",
                        marker={"size": 10},
                    )
                )
    fig.update_layout(
        margin={"l": 0, "t": 0, "b": 0, "r": 0},
        mapbox={
            "center": {"lon": -83.08126281, "lat": 42.39626405},
            "style": "stamen-terrain",
            "zoom": 13,
        },
    )
    fig.show()