import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import config
from utils.utils_data import convert_dict

from pdmconf import connectpdm, OSM_POWER_TAGS

import argparse
import ast

import geopandas as gpd
from shapely import wkb
from shapely.geometry import LineString

FILENAME_SUBSTATIONS = "osm_pdm_power_substations.gpkg"

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--country", type=str, help="Country OSM code", default="80500")
parser.add_argument("-d", "--date", type=str, help="Date of layer", default="CURRENT_TIMESTAMP")
parser.add_argument("-f", "--folder", type=str, help="Folder name", default="xx") # Country code expected

# ---------------------------------------------
# Initialisation
# ---------------------------------------------
args = parser.parse_args()
datebuild = args.date
countryosmcode = args.country
output_folder_name = args.folder

output_path = config.DATA_PATH / output_folder_name
output_path.mkdir(exist_ok=True, parents=True)

# ---------------------------------------------
# Connect to Podoma PostgreSQL/PostGIS database
# ---------------------------------------------
conn = connectpdm()

query = f"""
SELECT fc.osmid, fc.version, fc.tags, fc.geom geometry, fc.ts_start timestamp
FROM pdm_features_substations_changes fc
JOIN pdm_features_substations_boundary fb ON fc.osmid=fb.osmid AND fc.version=fb.version
WHERE fb.boundary = {countryosmcode}
AND (({datebuild} BETWEEN fc.ts_start AND fc.ts_end) OR ({datebuild} >= fc.ts_start AND fc.ts_end is null));
"""

gdf = gpd.GeoDataFrame.from_postgis(query, conn, geom_col='geometry')

# ---------------------------------------------
# Factoring and export GeoDataFrame
# ---------------------------------------------

gdf["id"] = gdf["osmid"].apply(lambda x: x.split("/")[1])
gdf["tags"] = gdf["tags"].map(convert_dict)
for tag in OSM_POWER_TAGS:
    gdf[tag] = gdf["tags"].apply(lambda x: x.pop(tag, None))

# Export to a shapefile
output_path_substations = output_path / FILENAME_SUBSTATIONS
gdf.to_file(output_path_substations)
print("Shapefile created:", output_path_substations, " | length =", len(gdf), "\n")


