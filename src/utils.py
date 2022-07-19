import numpy as np
import networkx as nx
import geopy.distance
from cerberus import Validator
from exceptions import ValidationError
from graph import RoadNetworkFromPolygon
import shapefile
import shapely.geometry
import shapely
from networkx.algorithms import approximation as ax


def df_validator(scehma, df):

    errors = []
    csv_validator = Validator()
    csv_validator.schema = scehma
    csv_validator.require_all = True

    for idx, record in enumerate(df.to_dict(orient="records")):
        if not csv_validator.validate(record):
            errors.append(
                f"Item {idx}: {csv_validator.errors}, Record: {record}"
            )
    if errors:
        raise ValidationError(errors)
    return True


def get_point_from_curve(curve, x):

    x_ = np.array([el[0] for el in curve])
    y_ = np.array([el[1] for el in curve])

    index = sum(x_ <= x)
    if index == len(x_):
        y = (y_[index - 1] - y_[index - 2]) * (x - x_[index - 2]) / (
            x_[index - 1] - x_[index - 2]
        ) + y_[index - 2]
    elif index == 0:
        y = (y_[index + 1] - y_[index]) * (x - x_[index]) / (
            x_[index + 1] - x_[index]
        ) + y_[index]
    else:
        y = (y_[index] - y_[index - 1]) * (x - x_[index - 1]) / (
            x_[index] - x_[index - 1]
        ) + y_[index - 1]

    return y


def get_distance(point1, point2, latlon=False):

    """Returns distance between two geopoints in meter assuming eliposoidal earth model"""

    # Assuming point1 and point2 are tuples with first element representing longitude and
    # second element representing latitude

    # Geopy however requires (lat, lon) pair
    if not latlon:
        return (
            geopy.distance.distance(
                (point1[1], point1[0]), (point2[1], point2[0])
            ).km
            * 1000
        )
    else:
        return geopy.distance.distance(point1, point2).km * 1000


def get_nearest_points_in_the_network(graph, points):

    nearest_points = {}
    graph_node_data = {
        key: val["pos"] for key, val in dict(graph.nodes(data=True)).items()
    }
    for point in points:

        min_distance, nearest_node = None, None
        for node, coords in graph_node_data.items():
            distance = get_distance(point, coords)
            if min_distance is None:
                min_distance = distance
                nearest_node = node
            else:
                if distance < min_distance:
                    min_distance = distance
                    nearest_node = node

        nearest_points[nearest_node] = {
            "centre": point,
            "longitude": graph_node_data[nearest_node][0],
            "latitude": graph_node_data[nearest_node][1],
        }

    return nearest_points


def slice_up_network_edges(graph: nx.Graph, slice_in_meter: float) -> nx.Graph:

    # Creates a new graph with edges sliced by given distance in meter

    sliced_graph = nx.Graph()
    graph_nodes = {
        x[0]: x[1]["pos"] if "pos" in x[1] else [x[1]["x"], x[1]["y"]]
        for x in graph.nodes.data()
    }

    for edge in graph.edges():

        edge_length = get_distance(
            (graph_nodes[edge[0]][0], graph_nodes[edge[0]][1]),
            (graph_nodes[edge[1]][0], graph_nodes[edge[1]][1]),
        )
        edge_slices = [
            x / edge_length for x in np.arange(0, edge_length, slice_in_meter)
        ] + [1]

        x1, y1 = (graph_nodes[edge[0]][0], graph_nodes[edge[0]][1])
        x2, y2 = (graph_nodes[edge[1]][0], graph_nodes[edge[1]][1])

        sliced_nodes = []
        for slice in edge_slices:
            new_x, new_y = x1 + (x2 - x1) * slice, y1 + (y2 - y1) * slice
            sliced_graph.add_node(
                f"{new_x}_{new_y}_node",
                pos=(new_x, new_y),
                type="node",
                data={},
            )
            sliced_nodes.append(f"{new_x}_{new_y}_node")

        for i in range(len(sliced_nodes) - 1):
            sliced_graph.add_edge(
                sliced_nodes[i], sliced_nodes[i + 1], type="edge"
            )

    return sliced_graph


def get_forbidden_polygons(shp_file):

    """
    Get all the polygons for a forbidden area
    """
    shape = shapefile.Reader(shp_file)
    forbidden_polygons = []
    for feature in shape.shapeRecords():

        feature_object = feature.shape.__geo_interface__
        if feature_object["type"] == "Polygon":
            forbidden_polygons.append(
                shapely.geometry.Polygon(feature_object["coordinates"][0])
            )

    return forbidden_polygons


def get_slices(start, end, num_steps):

    return [
        start + i * (end - start) / (num_steps) for i in range(num_steps + 1)
    ]


def create_rectangular_mesh_network(
    lower_left: tuple,
    upper_right: tuple,
    vertical_space_meter: float = 32,
    horizontal_space_meter: float = 32,
    forbidden_areas=None,
    node_append_str=None,
):

    # Assuming tuples first element is longitude and second element is latitude
    # 50m is a common distance between low tension pole

    # First initialize the network
    graph = nx.Graph()

    # Find coordinates for four corners
    north_west = (lower_left[0], upper_right[1])
    north_east = upper_right
    south_west = lower_left
    south_east = (upper_right[0], lower_left[1])

    # Print some lengths
    horizontal_distance = get_distance(south_west, south_east)
    vertical_distance = get_distance(south_west, north_west)
    print(
        f"Vertical distance {vertical_distance}m, Horizontal distance {horizontal_distance}m"
    )

    # Compute number of sections required in horizontal (wet-east) and vertical (north-south) direction
    horizontal_sections = max(
        int(horizontal_distance / horizontal_space_meter), 1
    )
    vertical_sections = max(int(vertical_distance / vertical_space_meter), 1)
    print(
        f"Vertical sections: {vertical_sections}, horizontal sections: {horizontal_sections}"
    )

    # Let's create node and edges for the rectangular mesh
    vertical_edges, horizontal_edges = [], []
    for lon in get_slices(lower_left[0], upper_right[0], horizontal_sections):

        vertical_node_list = []
        for lat in get_slices(lower_left[1], upper_right[1], vertical_sections):
            node_name = f"{lon}_{lat}_{node_append_str}_node"
            graph.add_node(node_name, pos=(lon, lat))
            vertical_node_list.append(node_name)

        vertical_edges.append(vertical_node_list)

    for lat in get_slices(lower_left[1], upper_right[1], vertical_sections):
        horizontal_node_list = []
        for lon in get_slices(
            lower_left[0], upper_right[0], horizontal_sections
        ):
            node_name = f"{lon}_{lat}_{node_append_str}_node"
            horizontal_node_list.append(node_name)
        horizontal_edges.append(horizontal_node_list)

    # Let's create edges
    for vertical_points in vertical_edges:
        for i in range(len(vertical_points) - 1):
            graph.add_edge(vertical_points[i], vertical_points[i + 1])

    for horizontal_points in horizontal_edges:
        for i in range(len(horizontal_points) - 1):
            graph.add_edge(horizontal_points[i], horizontal_points[i + 1])

    # Let's plot the mesh
    points = {
        key: val["pos"] for key, val in dict(graph.nodes(data=True)).items()
    }

    # Let's see if the road_network exists

    try:
        road_ = RoadNetworkFromPolygon(
            [north_west, north_east, south_east, south_west, north_west]
        )
        road_.get_network(node_append_str)
        # Let's try to remove nodes that are near to the road network
        d_threshold = min(horizontal_space_meter, vertical_space_meter)

        # First we need to slice the road_edges to be no larger than d_threshold
        sliced_road = slice_up_network_edges(road_.updated_network, d_threshold)
        sliced_road = nx.relabel_nodes(
            sliced_road, {n: n + node_append_str for n in sliced_road.nodes()}
        )

        # Let's loop through sliced road nodes and remove closer nodes
        sliced_road_nodes = {
            key: val["pos"]
            for key, val in dict(sliced_road.nodes(data=True)).items()
        }
        for road_node, road_node_coords in sliced_road_nodes.items():
            for node, node_coords in points.items():
                if get_distance(node_coords, road_node_coords) < d_threshold:

                    try:
                        graph.remove_node(node)
                        # print(f"{node} node removed")
                    except nx.NetworkXError as e:
                        # print(e)
                        pass

        # Now let's connect the sliced road netowork to truncated mesh network
        # First step is to find the nearest node for each of the sliced road nodes to truncated mesh network

        # updated the node_coords
        points = {
            key: val["pos"] for key, val in dict(graph.nodes(data=True)).items()
        }
        nearest_nodes_meshed_network = {}
        for node, coords in sliced_road_nodes.items():
            min_distance, nearest_node = None, None
            for mesh_node, mesh_node_coords in points.items():
                distance = get_distance(coords, mesh_node_coords)
                if min_distance is None:
                    min_distance = distance
                    nearest_node = mesh_node
                else:
                    if distance < min_distance:
                        min_distance = distance
                        nearest_node = mesh_node

            if min_distance < (1.5 * d_threshold):
                nearest_nodes_meshed_network[node] = nearest_node

        # Second step is to add the sliced road edges to truncted mesh network
        for node, coords in sliced_road_nodes.items():
            graph.add_node(node, pos=coords)
        for edge in sliced_road.edges():
            graph.add_edge(edge[0], edge[1])

        # Add edges to connect the road to mesh network
        for node1, node2 in nearest_nodes_meshed_network.items():
            graph.add_edge(node1, node2)

        # updated the node_coords
        points = {
            key: val["pos"] for key, val in dict(graph.nodes(data=True)).items()
        }

    except (nx.NetworkXPointlessConcept, ValueError) as e:
        print(e)

    # Now let's try to fetch lakes and rives and try to a
    if forbidden_areas != None:

        # get all forbidden polygons
        forbidden_polygons = get_forbidden_polygons(forbidden_areas)

        # Let's create a polygon
        customer_polygon = shapely.geometry.Polygon(
            [north_west, north_east, south_east, south_west, north_west]
        )

        forbidden_polygon_subset = []
        for polygon in forbidden_polygons:
            if polygon.intersects(customer_polygon):
                forbidden_polygon_subset.append(polygon)

        if forbidden_polygon_subset:
            for polygon in forbidden_polygon_subset:
                for node, coords in points.items():
                    node_point = shapely.geometry.Point(coords)
                    if node_point.within(polygon):
                        try:
                            graph.remove_node(node)
                        except nx.NetworkXError as e:
                            # print(e)
                            pass

    if not nx.is_connected(graph):
        largest_component = max(nx.connected_components(graph), key=len)
        graph = graph.subgraph(largest_component)

    points = {
        key: val["pos"] for key, val in dict(graph.nodes(data=True)).items()
    }
    return graph, points


def mesh_pruning(mesh_graph, customers):

    # Let's find the nodes we absolutey need to keep
    points = {
        key: val["pos"]
        for key, val in dict(mesh_graph.nodes(data=True)).items()
    }
    nodes_to_keep = []
    customer_to_node_mapper = {}

    for customer in customers:
        min_distance, nearest_node = None, None

        for point, coords in points.items():
            distance = get_distance(customer, coords)

            if min_distance is None:
                min_distance = distance
                nearest_node = point
            else:
                if distance < min_distance:
                    min_distance = distance
                    nearest_node = point

        if nearest_node not in nodes_to_keep:
            nodes_to_keep.append(nearest_node)
        customer_to_node_mapper[
            f"{customer[0]}_{customer[1]}_customer"
        ] = nearest_node

    # Let's start pruning the network
    graph_mst = ax.steinertree.steiner_tree(mesh_graph, nodes_to_keep)
    return graph_mst, customer_to_node_mapper


def triangulate_using_mesh(
    customers, forbidden_areas=None, node_append_str=None
):

    # find the edge coordinates

    lats = [x[1] for x in customers]
    lons = [x[0] for x in customers]

    graph, points = create_rectangular_mesh_network(
        (min(lons), min(lats)),
        (max(lons), max(lats)),
        forbidden_areas=forbidden_areas,
        node_append_str=node_append_str,
    )
    graph_mst, customer_to_node_mapper = mesh_pruning(graph, customers)
    # graph, points = add_customer_nodes_and_edges(graph_mst, customer_to_node_mapper)

    return graph_mst, points, customer_to_node_mapper


def set_node_edge_type(network):

    nx.set_node_attributes(network, "node", name="type")
    nx.set_node_attributes(network, {"type": "node"}, name="data")
    nx.set_edge_attributes(network, "edge", name="type")
    return network
