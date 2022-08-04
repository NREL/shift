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

""" This module contains classes for managing network plots. """

from abc import ABC, abstractmethod
import os
from typing import Union, List

import networkx as nx
import plotly.graph_objects as go

from shift.exceptions import (
    ZoomLevelNotInRangeError,
    InvalidMapboxStyle,
    EmptyAssetStyleDict,
    MissingKeyDataForNetworkNode,
    InvalidNodeType,
    FolderNotFoundError,
)
from shift.constants import MIN_ZOOM_LEVEL, MAX_ZOOM_LEVEL, MAP_STYLES


class NetworkPlot(ABC):
    """Interface for plotting a network."""

    @abstractmethod
    def show(self) -> None:
        """Abstract method for showing the plot."""
        pass

    @abstractmethod
    def html_export(self, html_file_path: str):
        """Abstract method for exporting network plot in html format.

        Args:
           html_file_path (str): Valid html file path
        """
        pass


class PlotlyGISNetworkPlot(NetworkPlot):
    """ " Class for plotting network along with GIS layer using plotly.

    Attributes:
        network (nx.Graph): Graph to plot
        access_token (str): MapBox token
        style (str): Valid MapBox style
        zoom_level (int): Initial Zoom level for the plot
        asset_specific_style (Union[None, dict]): Asset specific style dict
        data (dict): Plot data managed internally
        fig (go.Figure): go.Figure instance managed internally
    """

    def __init__(
        self,
        network: nx.Graph,
        access_token: str,
        style: str = "satellite",
        zoom_level: int = 13,
        asset_specific_style: Union[None, dict] = None,
    ) -> None:
        """Constructor for `PlotlyGISNetworkPlot` class.

        Args:
            network (nx.Graph): Graph to plot
            access_token (str): MapBox token
            style (str): Valid MapBox style
            zoom_level (int): Initial Zoom level for the plot
            asset_specific_style (Union[None, dict]): Asset specific style dict

        Raises:
            InvalidMapboxStyle: If invalid mapbox style is passed
            ZoomLevelNotInRangeError: If invalid zoom level is passed
            EmptyAssetStyleDict: If `asset_specific_style` is empty
        """

        self.access_token = access_token
        self.network = network
        self.style = style
        if self.style not in MAP_STYLES:
            raise InvalidMapboxStyle(self.style)

        self.zoom_level = zoom_level
        if self.zoom_level < MIN_ZOOM_LEVEL or self.zoom_level > MAX_ZOOM_LEVEL:
            raise ZoomLevelNotInRangeError(self.zoom_level)

        self.asset_specific_style = (
            asset_specific_style if asset_specific_style is not None else {}
        )
        if not self.asset_specific_style:
            raise EmptyAssetStyleDict()

        self.data = []
        self._add_data()
        self._prepare_plot()

    def _add_data(self):
        """Private method to add data for generating plot."""

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

    def add_scatter_data(
        self,
        lons: List[float],
        lats: List[float],
        texts: List[str],
        color: str = "blue",
        size: int = 5,
    ) -> None:
        """Add scatter data to the map.

        Args:
            lons (List[float]): List of longitudes
            lats (List[float]): List of latitudes
            texts (List[str]): List of hover texts
            color (str): Color for scatter plot
            size (int): Size for scatter plot
        """

        self.data.append(
            go.Scattermapbox(
                mode="markers",
                lon=lons,
                lat=lats,
                text=texts,
                marker={"size": size, "color": color},
            )
        )

    def add_line_data(
        self,
        lats: List[float],
        lons: List[float],
        line_color: str = "red",
        size: int = 10,
    ) -> None:
        """Method for adding line data.

        Args:
            lats (List[float]): List of latitudes
            lons (List[float]): List of longitudes
            line_color (str): Color for line plot
            size (int): Size for line plot
        """
        del size
        self.data.append(
            go.Scattermapbox(
                mode="markers+lines",
                lon=lons,
                lat=lats,
                marker={"size": 2},
                line={"color": line_color},
            )
        )

    def _get_map_centre(self) -> dict:
        """Private method to get map center."""

        longitudes = [node[1]["pos"][0] for node in self.network.nodes.data()]
        latitudes = [node[1]["pos"][1] for node in self.network.nodes.data()]
        return {
            "lon": sum(longitudes) / len(longitudes),
            "lat": sum(latitudes) / len(latitudes),
        }

    def _prepare_plot(self) -> None:
        """Private method to prepare the plot"""

        self.fig = go.Figure(data=self.data)
        self.fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        self.fig.update_mapboxes(
            {
                "accesstoken": self.access_token,
                "style": self.style,
                "center": self._get_map_centre(),
                "zoom": self.zoom_level,
            }
        )

    def show(self) -> None:
        """Refer to base class for more details."""
        self.fig.show()

    def html_export(self, html_file_path: str) -> None:
        """Refer to base class for more details."""
        if not os.path.exists(os.path.dirname(html_file_path)):
            raise FolderNotFoundError(os.path.dirname(html_file_path))
        self.fig.write_html(html_file_path)
