import networkx as nx
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString

## SETTINGS
COUNTRY_CODE = "BO"
DATA_PATH = "data/"

def merge_two_lines_on_node(graph, node):
    edges = graph.edges(node)
    if len(edges) != 2:
        raise ValueError("Number of edges unexpected")
    new_nodes = []
    for e in edges:
        if e[0] != node:
            new_nodes.append(e[0])
        if e[1] != node:
            new_nodes.append(e[1])
    #new_nodes = [e for e in [edges[0][0], edges[0][1], edges[1][0], edges[1][1]] if e != node]

    #print(" ~~~~ ", edges, *new_nodes)
    graph.remove_node(node)
    graph.add_edge(*new_nodes, status="undefined")

def check_if_connected(graph, node):
    for e in graph.edges(node, keys=True):
        if graph.edges[e]["status"] != "disconnected":
            return graph.nodes[node]["status"]
    return "disconnected"

gdf_nodes = gpd.read_file(DATA_PATH + COUNTRY_CODE + "/pre_graph_power_nodes.gpkg").to_crs(epsg=3857)
gdf_lines = gpd.read_file(DATA_PATH + COUNTRY_CODE + "/pre_graph_power_lines.gpkg").to_crs(epsg=3857)
gdf_lines = gdf_lines[gdf_lines["id"]<1355000000]
#gdf_nodes = gdf_nodes[(gdf_nodes["id"]<1355000000) & (gdf_nodes["type"]=="way")]

G = nx.MultiGraph()

gdf_nodes.apply(lambda node: G.add_node(node["osmid"], grid_role=node["grid_role"],
                                        geometry=node["geometry"], status="undefined", connections=""), axis=1)
gdf_lines.apply(lambda line: G.add_edge(line["osmid_node0"], line["osmid_node1"], status="undefined",
                                        osmid=line["osmid"]), axis=1)


# Removing lambda node that connect exactly 2 edges
is_complete = False
while not is_complete:
    is_complete = True
    for node in G.nodes:
        #print(node, G.nodes[node])
        if (len(G.edges(node))==2) and (G.nodes[node]["grid_role"] == "lambda_node"):
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

keys = ["grid_role", "status", "connections", "geometry"]
data_nodes = [{**{"osmid":n}, **{key:G.nodes[n][key] for key in keys}} for n in G.nodes]
gdf_nodes = gpd.GeoDataFrame(data_nodes, geometry="geometry", crs=3857)
gdf_nodes.to_file(DATA_PATH + COUNTRY_CODE + "/post_graph_power_nodes.gpkg")

data_edges = [{"status":G.edges[n]["status"], "node0":n[0], "node1":n[1],
               "geometry":LineString([G.nodes[n[0]]["geometry"], G.nodes[n[1]]["geometry"]])} for n in G.edges]
gdf_edges = gpd.GeoDataFrame(data_edges, geometry="geometry", crs=3857)
gdf_edges.to_file(DATA_PATH + COUNTRY_CODE + "/post_graph_power_lines.gpkg")


## Graph analysis
print("Number of international connections", len([n for n in G.nodes if G.nodes[n]["grid_role"]=="international"]))
print("Number of substations", len(gdf_nodes[gdf_nodes["grid_role"]=="substation"]))
list_graph_subsets = list(nx.connected_components(G))
graph_stats = []
for l in list_graph_subsets:
    nbsub = len([n for n in l if (G.nodes[n]["grid_role"] == "substation") and (G.nodes[n]["status"] != "disconnected")])
    nbseg = len([e for e in G.subgraph(l).edges if G.edges[e]["status"] != "disconnected"])
    if nbsub:
        graph_stats.append({"nbsub":nbsub, "nbseg":nbseg})


df_stat = pd.DataFrame(graph_stats)
df_stat = df_stat.sort_values(["nbsub", "nbseg"], ascending=False)
print("Grid connectivity = ", end="")
for x in df_stat.to_dict(orient='records'):
    print(f"({x['nbsub']}x{x['nbseg']}) + ", end = "")
print("\n")
