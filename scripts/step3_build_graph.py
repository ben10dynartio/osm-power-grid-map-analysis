import json
import networkx as nx
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, LineString

## SETTINGS
import config
COUNTRY_CODE = config.COUNTRY_CODE
DATA_PATH = config.DATA_PATH

INCLUDE_CIRCUIT = True


def main():
    txt_circuit = "_circuit" if INCLUDE_CIRCUIT else ""
    gdf_nodes = gpd.read_file(DATA_PATH / COUNTRY_CODE / "pre_graph_power_nodes.gpkg").to_crs(epsg=3857)
    gdf_lines = gpd.read_file(DATA_PATH / COUNTRY_CODE / f"pre_graph_power_lines{txt_circuit}.gpkg").to_crs(epsg=3857)
    # gdf_lines = gdf_lines[gdf_lines["id"]<1355000000]
    # gdf_nodes = gdf_nodes[(gdf_nodes["id"]<1355000000) & (gdf_nodes["type"]=="way")]

    G = nx.MultiGraph()

    gdf_nodes.apply(lambda node: G.add_node(node["osmid"], grid_role=node["grid_role"],
                                            geometry=node["geometry"], status="undefined", connections="",
                                            voltage=node["voltage"], power=node["power"]), axis=1)
    gdf_lines.apply(lambda line: G.add_edge(line["osmid0"], line["osmid1"], status="undefined",
                                            osmid=line["osmid"], international=line["international_osmid"],
                                            voltage=line["voltage"], circuits=line["circuits"], cables=line["cables"],
                                            wires=line["wires"], power=line["power"]), axis=1)

    # Removing lambda node that connect exactly 2 edges
    is_complete = False
    while not is_complete:
        is_complete = True
        for node in G.nodes:
            # print(node, G.nodes[node])
            if (len(G.edges(node)) == 2) and (G.nodes[node]["grid_role"] == "lambda_node"):
                # print("Merging on node:", node)
                merge_two_lines_on_node(G, node)
                is_complete = False
                break

    for node in G.nodes:
        edges = G.edges(node, keys=True)
        G.nodes[node]["connections"] = len(edges)
        if len(edges) == 0:
            G.nodes[node]["status"] = "disconnected"
        elif len(edges) == 1:
            if G.nodes[node]["grid_role"] == "lambda_node":
                for edge in edges:
                    G.edges[edge]["status"] = "disconnected"

    for node in G.nodes:
        G.nodes[node]["status"] = check_if_connected(G, node)

    keys = ["grid_role", "status", "connections", "voltage", "power", "geometry"]
    data_nodes = [{**{"osmid": n}, **{key: G.nodes[n][key] for key in keys}} for n in G.nodes]
    gdf_nodes = gpd.GeoDataFrame(data_nodes, geometry="geometry", crs=3857)
    gdf_nodes.to_file(DATA_PATH / COUNTRY_CODE / f"post_graph_power_nodes{txt_circuit}.gpkg")

    data_edges = []
    for n in G.edges:
        row = {"status": G.edges[n]["status"],
               "node0": n[0], "node1": n[1],
               "geometry": LineString([G.nodes[n[0]]["geometry"], G.nodes[n[1]]["geometry"]])}
        for key in ["osmid", "international", "power", "voltage", "circuits", "cables"]:
            row[key] = G.edges[n][key] if key in G.edges[n] else None
        data_edges.append(row)
    if not data_edges:
        data_edges = {"node0": [], "node1": [], "international": [], "osmid": [], "geometry": []}
    gdf_edges = gpd.GeoDataFrame(data_edges, geometry="geometry", crs=3857)
    gdf_edges["status"] = np.where(gdf_edges["status"] == "undefined",
                                   "connected", gdf_edges["status"])
    gdf_edges.to_file(DATA_PATH / COUNTRY_CODE / f"post_graph_power_lines{txt_circuit}.gpkg")


def merge_two_lines_on_node(graph, node):
    edges = graph.edges(node)
    stredges = str(edges)
    if len(edges) != 2:
        raise ValueError("Number of edges unexpected")
    merged_keys = ["voltage", "cables", "circuits", "wires"]
    merged_values = {}
    for key in merged_keys:
        temp = []
        for e in edges:
            temp.append(graph.edges[*e, 0][key])
        if temp[0] != temp[1]:
            print(f" * ERROR {key} difference on line node https://www.openstreetmap.org/{node} | {key} = {temp}, (first value kept)")
        merged_values[key] = temp[0]
    new_nodes = []
    osmid_list = []
    for e in edges:
        osmid_list.append(graph.edges[*e, 0]["osmid"]) #[*e, 0]
        if e[0] != node:
            new_nodes.append(e[0])
        if e[1] != node:
            new_nodes.append(e[1])
    #new_nodes = [e for e in [edges[0][0], edges[0][1], edges[1][0], edges[1][1]] if e != node]

    #print(" ~~~~ ", edges, *new_nodes)
    graph.remove_node(node)
    #print("Adding edge : ", new_nodes)
    if len(new_nodes) != 2:
        print(" * ERROR Topology Error on node(s) - 2 nodes expected :", new_nodes, " / You might need to split the way")
    elif new_nodes[0] != new_nodes[1]:
        graph.add_edge(*new_nodes, osmid = ";".join(osmid_list), status="undefined",
                       voltage=merged_values["voltage"], circuits=merged_values["circuits"],
                       wires=merged_values["wires"], cables=merged_values["circuits"])
    else:
        print("-- Possible Topology Error on node(s) - Same origin-destination :", new_nodes, " | edges = ", stredges, " | str = ", ";".join(osmid_list))
        graph.add_edge(*new_nodes, osmid = ";".join(osmid_list), status="undefined",
                       voltage=merged_values["voltage"], circuits=merged_values["circuits"],
                       wires=merged_values["wires"], cables=merged_values["circuits"])

def check_if_connected(graph, node):
    for e in graph.edges(node, keys=True):
        if graph.edges[e]["status"] != "disconnected":
            return graph.nodes[node]["status"]
    return "disconnected"


if __name__=="__main__":
    main()