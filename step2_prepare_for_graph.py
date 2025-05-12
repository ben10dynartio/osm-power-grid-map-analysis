import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, LineString
import ast

## SETTINGS
COUNTRY_CODE = "NG"
DATA_PATH = "data/"
BUFFER_DISTANCE = 250


## Prepare power tower transition
gdf_tower = gpd.read_file(DATA_PATH + COUNTRY_CODE + "/osm_brut_power_tower_transition.gpkg").to_crs(epsg=3857)
gdf_tower = gdf_tower[gdf_tower["line_management"]=="transition"]
set_transition_nodes = set(gdf_tower["id"].unique().tolist())
print("-- Number of line_management=transition power nodes =", len(set_transition_nodes))

### Prepare power line dataset
gdf_line = gpd.read_file(DATA_PATH + COUNTRY_CODE + "/osm_brut_power_line.gpkg").to_crs(epsg=3857)
#gdf_line = gdf_line[gdf_line["@numid"]<1_355_000_000] # keep only lines mapped before jan 2025

gdf_line["geometry"] = gdf_line["geometry"].apply(lambda x: LineString([x.coords[0], x.coords[-1]]))
#gdf_line["nodes"] = gdf_line["nodes"].apply(lambda x: [ast.literal_eval(x)[0], ast.literal_eval(x)[-1]])
gdf_line["nodes"] = gdf_line["nodes"].apply(lambda x: [ast.literal_eval(x)[0], ast.literal_eval(x)[-1]])
for i in range(2):
    gdf_line[f"p{i}"] = gdf_line["geometry"].apply(lambda x: Point(x.coords[i]))
    gdf_line[f"node{i}"] = gdf_line["nodes"].apply(lambda x: x[i])
    gdf_line[f"transition{i}"] = gdf_line[f"node{i}"].apply(lambda x: x in set_transition_nodes)

# Ex: 1234567 --> POINT(12.34 52.25)
dic_line_geopoint ={}
for i in range(2):
    dic_line_geopoint = {**dic_line_geopoint,
                         **{r[f"node{i}"] : r[f"p{i}"] for r in gdf_line.to_dict(orient="records")}}

print(dic_line_geopoint)
print(gdf_line.iloc[45])

### Prepare substation dataset
gdf_sub = gpd.read_file(DATA_PATH + COUNTRY_CODE + "/osm_brut_power_substation.gpkg").to_crs(epsg=3857)
gdf_sub["centroid"] = np.where((gdf_sub["type"]=="way") | (gdf_sub["type"]=="relation"),
                               gdf_sub["geometry"].centroid, gdf_sub["geometry"])
gdf_sub["geometry"] = gdf_sub["geometry"].buffer(distance=BUFFER_DISTANCE)

# Ex: way/1234567 --> POINT(12.34 52.25)
dic_substation_geopoint = {r["osmid"] : r["centroid"] for r in gdf_sub.to_dict(orient="records")}

print(gdf_sub.iloc[45])


## Spatial join ends of lines with substations
gdf_country_shape = gpd.read_file(DATA_PATH + COUNTRY_CODE + "/osm_brut_country_shape.gpkg").to_crs(epsg=3857)
dic_res = []
dic_international_nodes = {}
for i in range(2):
    dftemp = gdf_line.copy()
    dftemp["geometry"] = dftemp[f"p{i}"]
    dftemp = dftemp.sjoin(gdf_sub, how='left').fillna("")
    print(dftemp.columns)
    dic_res = {k["osmid_left"] : k["osmid_right"] for k in dftemp.to_dict(orient='records') }
    gdf_line[f"substation{i}"] = gdf_line["osmid"].apply(lambda x: dic_res[x])

    # Identify International end
    dftempbis = dftemp.clip(gdf_country_shape).copy()
    set_inside_country = set(dftempbis[f"node{i}"].unique().tolist())
    dftemp = dftemp[~(dftemp[f"node{i}"]).isin(set_inside_country)]
    print(dftemp)
    print(gdf_country_shape)
    dic_international_nodes = {**dic_international_nodes,
                              **{"node/" + str(r[f"node{i}"]) : r["geometry"]
                                 for r in dftemp.to_dict(orient='records')}}


gdf_line = gdf_line[(gdf_line["substation0"] == "") | (gdf_line["substation1"] == "")
                    | (gdf_line["substation0"]!=gdf_line["substation1"])]


copy_gdf_transition = gdf_tower.copy()
copy_gdf_transition["grid_role"] = "transition"

copy_gdf_sub = gdf_sub.copy()
copy_gdf_sub["grid_role"] = "substation"
copy_gdf_sub["geometry"] = copy_gdf_sub["centroid"]
del copy_gdf_sub["centroid"]

copy_gdf_line = []
for i in range(2):
    dftemp = gdf_line.copy()
    # List of nodes that are neither substation nor trasnition
    dftemp = dftemp[dftemp[f"substation{i}"] == ""]
    dftemp = dftemp[~dftemp[f"transition{i}"]]
    dftemp["geometry"] = dftemp[f"p{i}"]
    dftemp["grid_role"] = "lambda_node"
    dftemp["osmid"] = "node/" + gdf_line[f"node{i}"].map(str)
    copy_gdf_line.append(dftemp)

dftemp = pd.DataFrame([{"osmid":key, "geometry":val, "grid_role":"international"} for key, val in dic_international_nodes.items()])
gdf_international = gpd.GeoDataFrame(dftemp, geometry="geometry", crs=3857)

df_graph_nodes = pd.concat(copy_gdf_line + [copy_gdf_transition, copy_gdf_sub, gdf_international])

for i in range(2):
    del df_graph_nodes[f"p{i}"]
    del df_graph_nodes[f"substation{i}"]
    del df_graph_nodes[f"node{i}"]
    del df_graph_nodes[f"transition{i}"]
for key in ["nodes", 'circuits', 'cables', 'voltage']:
    if key in df_graph_nodes.columns:
        del df_graph_nodes[key]

print(df_graph_nodes.columns)
gdf_graph_nodes = gpd.GeoDataFrame(df_graph_nodes, geometry="geometry")
gdf_graph_nodes.to_file(DATA_PATH + COUNTRY_CODE + "/pre_graph_power_nodes.gpkg")


for i in range(2):
    gdf_line[f"p{i}"] = np.where(gdf_line[f"substation{i}"] != "",
                                 gdf_line[f"substation{i}"].apply(lambda x: dic_substation_geopoint.get(x)),
                                 gdf_line[f"p{i}"])
    gdf_line[f"osmid_node{i}"] = np.where(gdf_line[f"substation{i}"] != "",
                                 gdf_line[f"substation{i}"],
                                 "node/" + gdf_line[f"node{i}"].map(str))
gdf_line["geometry"] = gdf_line.apply(lambda r: LineString([r["p0"], r["p1"]]), axis=1)

## This line remove errors, but theses errros should be seen and corrected
gdf_line = gdf_line[gdf_line["osmid_node0"]!=gdf_line["osmid_node1"]]

del gdf_line["p0"]
del gdf_line["p1"]
gdf_line.to_file(DATA_PATH + COUNTRY_CODE + "/pre_graph_power_lines.gpkg")



