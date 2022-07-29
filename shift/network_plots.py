from abc import ABC, abstractmethod
import networkx as nx
import plotly.graph_objects as go
from exceptions import (
    ZoomLevelNotInRangeError,
    InvalidMapboxStyle,
    EmptyAssetStyleDict,
    MissingKeyDataForNetworkNode,
    InvalidNodeType,
    FolderNotFoundError,
)
from constants import MIN_ZOOM_LEVEL, MAX_ZOOM_LEVEL, MAP_STYLES
import os


class NetworkPlot(ABC):
    @abstractmethod
    def show(self):
        pass

    @abstractmethod
    def html_export(self, html_file_path: str):
        pass


class PlotlyGISNetworkPlot(NetworkPlot):
    def __init__(
        self,
        network: nx.Graph,
        access_token: str,
        style: str = "satellite",
        zoom_level: int = 13,
        asset_specific_style: dict = {},
    ):

        self.access_token = access_token
        self.network = network
        self.style = style
        if self.style not in MAP_STYLES:
            raise InvalidMapboxStyle(self.style)

        self.zoom_level = zoom_level
        if self.zoom_level < MIN_ZOOM_LEVEL or self.zoom_level > MAX_ZOOM_LEVEL:
            raise ZoomLevelNotInRangeError(self.zoom_level)

        self.asset_specific_style = asset_specific_style
        if not self.asset_specific_style:
            raise EmptyAssetStyleDict()

        self.data = []
        self.add_data()
        self.prepare_plot()

    def add_data(self):

        scatter_data = {}
        for node in self.network.nodes.data():

            if "type" not in node[1]:
                raise MissingKeyDataForNetworkNode("type")

            if "data" not in node[1]:
                node[1]["data"] = {}

            if node[1]["type"] not in scatter_data:
                scatter_data[node[1]["type"]] = {
                    "longitudes": [],
                    "latitudes": [],
                    "texts": [],
                }

            scatter_data[node[1]["type"]]["latitudes"].append(node[1]["pos"][1])
            scatter_data[node[1]["type"]]["longitudes"].append(
                node[1]["pos"][0]
            )
            text = "<br>".join([f"{k}:{v}" for k, v in node[1]["data"].items()])
            scatter_data[node[1]["type"]]["texts"].append(text)

        for key, style_dict in self.asset_specific_style.get(
            "nodes", {}
        ).items():

            if key in scatter_data:
                self.add_scatter_data(
                    scatter_data[key]["longitudes"],
                    scatter_data[key]["latitudes"],
                    scatter_data[key]["texts"],
                    color=style_dict.get("color", "blue"),
                    size=style_dict.get("size", 5),
                )
            else:
                raise InvalidNodeType(key)

        line_data = {}
        node_data = {node[0]: node[1] for node in self.network.nodes.data()}
        for edge in self.network.edges():

            edge_data = self.network.get_edge_data(*edge)
            if "type" not in edge_data:
                raise MissingKeyDataForNetworkNode("type")

            if edge_data["type"] not in line_data:
                line_data[edge_data["type"]] = {
                    "longitudes": [],
                    "latitudes": [],
                }

            line_data[edge_data["type"]]["latitudes"].extend(
                [
                    node_data[edge[0]]["pos"][1],
                    node_data[edge[1]]["pos"][1],
                    None,
                ]
            )
            line_data[edge_data["type"]]["longitudes"].extend(
                [
                    node_data[edge[0]]["pos"][0],
                    node_data[edge[1]]["pos"][0],
                    None,
                ]
            )

        for key, style_dict in self.asset_specific_style.get(
            "edges", {}
        ).items():

            if key in line_data:
                self.add_line_data(
                    line_data[key]["latitudes"],
                    line_data[key]["longitudes"],
                    line_color=style_dict.get("color", "red"),
                    size=style_dict.get("size", 10),
                )
            else:
                raise InvalidNodeType(key)

    def add_scatter_data(self, lons, lats, texts, color="blue", size=5):

        self.data.append(
            go.Scattermapbox(
                mode="markers",
                lon=lons,
                lat=lats,
                text=texts,
                marker={"size": size, "color": color},
            )
        )

    def add_line_data(self, lats, lons, line_color="red", size=10):

        self.data.append(
            go.Scattermapbox(
                mode="markers+lines",
                lon=lons,
                lat=lats,
                marker={"size": 2},
                line={"color": line_color},
            )
        )

    def get_map_centre(self):

        longitudes = [node[1]["pos"][0] for node in self.network.nodes.data()]
        latitudes = [node[1]["pos"][1] for node in self.network.nodes.data()]
        return {
            "lon": sum(longitudes) / len(longitudes),
            "lat": sum(latitudes) / len(latitudes),
        }

    def prepare_plot(self):

        self.fig = go.Figure(data=self.data)
        self.fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        self.fig.update_mapboxes(
            {
                "accesstoken": self.access_token,
                "style": self.style,
                "center": self.get_map_centre(),
                "zoom": self.zoom_level,
            }
        )

    def show(self):
        self.fig.show()

    def html_export(self, html_file_path: str):

        if not os.path.exists(os.path.dirname(html_file_path)):
            raise FolderNotFoundError(os.path.dirname(html_file_path))
        self.fig.write_html(html_file_path)
