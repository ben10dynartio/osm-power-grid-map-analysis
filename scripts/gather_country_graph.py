import geopandas as gpd
import pandas as pd

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
dflines = dflines[dflines["international"]!=""]


dfnodes = gpd.GeoDataFrame(pd.concat(list(dfs_nodes.values())), geometry="geometry")

print(dflines.iloc[0])
print(dfnodes.iloc[0])