import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point, LineString

## SETTINGS
import config
COUNTRY_CODE = config.COUNTRY_CODE
DATA_PATH = config.DATA_PATH
OSM_POWER_TAGS = config.OSM_POWER_TAGS

gdf_nodes = gpd.read_file(DATA_PATH / COUNTRY_CODE / "pre_graph_power_nodes.gpkg")
nodes_geo_dict = {row["osmid"]:row["geometry"] for row in gdf_nodes.to_dict(orient='records')}
gdf_lines = gpd.read_file(DATA_PATH / COUNTRY_CODE / "pre_graph_power_lines.gpkg")
print(" --- Files opened, CRS =", gdf_nodes.crs, gdf_lines.crs)
gdf_lines["circuits"] = np.where(gdf_lines["circuits"].isna(),
                                 1, gdf_lines["circuits"]).astype(int)
gdf_lines["cables"] = np.where(gdf_lines["cables"].isna(),
                                 3, gdf_lines["cables"]).astype(int)

df_circ = pd.read_csv(DATA_PATH / COUNTRY_CODE / "osm_clean_power_circuit_members.csv")

"""print(gdf_nodes)
print(gdf_lines)
print(gdf_lines.iloc[0])
print(df_circ)
print(df_circ.iloc[0])"""

circuit_rel_ids = df_circ["id"].unique().tolist()

print("-------- Circuit analysis ")
all_new_lines = []
for circuit in circuit_rel_ids:
    tdf = df_circ[df_circ["id"]==circuit]
    subs = tdf[tdf["member_role"]=="substation"]
    if len(subs)==1:
        print(" * ERROR : Incomplete circuit relation : ", circuit)
    elif len(subs)==2:
        newline = subs.iloc[0].copy()
        for i in [0, 1]:
            row = subs.iloc[i]
            newline[f"nodetype{i}"] = row["substation"]
            newline[f"osmid{i}"] = row["member_osmid"]
        try:
            newline["geometry"] = LineString([nodes_geo_dict[newline[f"osmid0"]], nodes_geo_dict[newline[f"osmid1"]]])
        except KeyError:
            keyerror = newline[f"osmid0"] if newline[f"osmid0"] not in nodes_geo_dict else newline[f"osmid1"]
            print(f" * ERROR with substation https://openstreetmap.org/{keyerror} (not found in substation list)")
            continue
        all_new_lines.append(newline)
    else: # (3 or more substation)
        print("Triple circuit relation : ", circuit)
        raise ValueError("Script not configured yet to manage triple substation circuit relation")

print("-------- Differentiate Power line with power circuit")
gdf_new_lines = gpd.GeoDataFrame(all_new_lines, geometry="geometry")
list_circuit = gdf_new_lines["osmid"].unique().tolist()

for circuit_osmid in list_circuit:
    tdf = df_circ[(df_circ["osmid"]==circuit_osmid)&(df_circ["member_role"]=="section")]
    if len(tdf)==0:
        print(" * ERROR on circuit = ", circuit_osmid, "(no section)")
        continue
    nb_circuits = int(tdf.iloc[0]["circuits"])
    nb_cables = int(tdf.iloc[0]["cables"])
    list_member_id = set(tdf["member_osmid"].unique().tolist())
    # :todo: check if member exist in circuit
    gdf_lines["circuits"] = np.where(gdf_lines["osmid"].isin(list_member_id),
                                     gdf_lines["circuits"]-nb_circuits, gdf_lines["circuits"])
    gdf_lines["cables"] = np.where(gdf_lines["osmid"].isin(list_member_id),
                                     gdf_lines["cables"]-nb_cables, gdf_lines["cables"])

check_df = gdf_lines[(gdf_lines["circuits"]<0)|(gdf_lines["cables"]<0)]
for row in check_df.to_dict(orient='records'):
    print(" * ERROR Negative number of circuit or cables =", row)

gdf_old_lines = gdf_lines[gdf_lines["circuits"]>0].copy()

gdf_final_power_lines = gpd.GeoDataFrame(pd.concat([pd.DataFrame(gdf_old_lines), pd.DataFrame(gdf_new_lines)]), geometry="geometry", crs=3857)
gdf_final_power_lines.to_file(DATA_PATH / COUNTRY_CODE / "pre_graph_power_lines_circuit.gpkg")


