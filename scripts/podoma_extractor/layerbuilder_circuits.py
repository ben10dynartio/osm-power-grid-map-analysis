import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import config
from utils.utils_data import convert_dict

from pdmconf import connectpdm, OSM_POWER_TAGS

import argparse
import ast

import pandas as pd

FILENAME_CIRCUITS = "osm_pdm_power_circuits.gpkg"

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

output_folder = config.DATA_PATH / args.folder
output_folder.mkdir(exist_ok=True, parents=True)

# ---------------------------------------------
# Connect to Podoma PostgreSQL/PostGIS database
# ---------------------------------------------
conn = connectpdm()

query = f"""
WITH circuits AS (
    SELECT fc.osmid osmid, fc.version version, fc.tags wtags, fc.userid wuserid, fc.ts_start wtimestamp
    FROM pdm_features_circuits_changes fc
    JOIN pdm_features_circuits_boundary fb ON fc.osmid=fb.osmid AND fc.version=fb.version
    WHERE fb.boundary={countryosmcode}
    AND (({datebuild} >= fc.ts_start AND {datebuild} < fc.ts_end) OR ({datebuild} >= fc.ts_start AND fc.ts_end is null))
), members AS (
    SELECT fm.memberid member_osmid, fm.role member_role, fm.osmid osmid, circuits.wtags wtags, circuits.wuserid wuserid, circuits.wtimestamp wtimestamp
    FROM pdm_members_circuits fm
    JOIN circuits ON fm.osmid=circuits.osmid AND fm.version=circuits.version
)
SELECT * FROM members;
"""

gdf = pd.read_sql_query(query, conn)

# ---------------------------------------------
# Factoring and export GeoDataFrame
# ---------------------------------------------

gdf["id"] = gdf["osmid"].apply(lambda x: x.split("/")[1])
gdf["tags"] = gdf["tags"].map(convert_dict)
for tag in OSM_POWER_TAGS:
    gdf[tag] = gdf["tags"].apply(lambda x: x.pop(tag, None))

gdf.to_csv(output_folder / "osm_pdm_circuits_members.csv", index=False)

# Export to a shapefile
this_output_path = output_folder / FILENAME_CIRCUITS
gdf.to_csv(this_output_path)
print("Shapefile created:", this_output_path, " | length =", len(gdf), "\n")


