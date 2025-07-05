"""
This script gather all grid_connectivity layers into a worldwide geofile
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, LineString

from config import DATA_PATH

# Config for this script
COUNTRY_LIST = {'TZ': 'Tanzania', 'KE': 'Kenya', 'UG': 'Uganda'}

dfs_lines = {}
dfs_nodes = {}
for countrycode in COUNTRY_LIST.keys():
    dfs_lines[countrycode] = pd.DataFrame(gpd.read_file(DATA_PATH / f"{countrycode}/post_graph_power_lines.gpkg"))
    dfs_lines[countrycode]["country"] = countrycode
    dfs_nodes[countrycode] = pd.DataFrame(gpd.read_file(DATA_PATH / f"{countrycode}/post_graph_power_nodes.gpkg"))
    dfs_nodes[countrycode]["country"] = countrycode

dflines = gpd.GeoDataFrame(pd.concat(list(dfs_lines.values())), geometry="geometry")
dfnodes = gpd.GeoDataFrame(pd.concat(list(dfs_nodes.values())), geometry="geometry")

counts_osmid = dflines["osmid"].value_counts()

for key, val in counts_osmid.items():
    if (val >= 3) and (key != ""):
        print(f"-- Info : {val} lines found for osmid = '{key}'")

list_multiple = [key for key, val in counts_osmid.items() if (val >= 2) and (key != "")]

df_m_lines = dflines[dflines["osmid"].isin(list_multiple)].copy()
dflines = dflines[~dflines["osmid"].isin(list_multiple)].copy()

def fusion_country(values):
    myvals = [val for val in values.unique().tolist() if val]
    if len(myvals)==1:
        return myvals[0]
    elif len(myvals)==0:
        return ""
    else:
        return ";".join(map(str, myvals))

def fusion_nodes(values):
    myset = set()
    for v in values:
        myset |= set([x for x in v if x])
    return list(myset)

def get_geom(idnode):
    return dfnodes[dfnodes["osmid"]==idnode].iloc[0]["geometry"]

"""for connector in list_multiple:
    myrows = df_m_lines[df_m_lines["osmid"]==connector]
    myrows_countrylist = myrows["country"].unique().tolist()"""

for i in range(2):
    df_m_lines[f"node{i}"] = np.where(df_m_lines[f"node{i}"] == df_m_lines["international"],
                                      "", df_m_lines[f"node{i}"])

df_m_lines[f"nodes"] = df_m_lines.apply(lambda r: [r["node0"], r["node1"]], axis=1 )
resultat = df_m_lines.groupby('osmid').agg({
        'nodes': fusion_nodes,
        'country': fusion_country,
    }).reset_index()

resultat["node0"] = resultat["nodes"].apply(lambda x: x[0])
resultat["node1"] = resultat["nodes"].apply(lambda x: x[1])
resultat["geometry"] = resultat.apply(lambda x: LineString([get_geom(x["node0"]), get_geom(x["node1"])]), axis=1)
print(resultat.iloc[0])
print(resultat)
print("--------------------")

composed_line = gpd.GeoDataFrame(pd.concat([dflines, resultat]), geometry="geometry", crs=3857)
composed_line.to_file("../export-world/graph_line.gpkg")
print(composed_line)

print(dflines.iloc[0])
print(dfnodes.iloc[0])