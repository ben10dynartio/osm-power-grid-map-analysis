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

FILENAME_LINESxNODES = "osm_pdm_power_linesxnodes.gpkg"
FILENAME_LINES = "osm_pdm_power_lines.gpkg"
FILENAME_NODES = "osm_pdm_power_nodes.gpkg"

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
WITH linesnodes AS (
    SELECT fm.memberid osmid, nc.version, nc.geom ngeom, fc.osmid memberof, fm.pos pos, fc.tags wtags, fc.userid wuserid, nc.ts_start wtimestamp
    FROM pdm_features_lines_changes fc
    JOIN pdm_members_lines fm ON fm.osmid=fc.osmid AND fm.version=fc.version
    JOIN pdm_features_lines_changes nc ON nc.osmid=fm.memberid AND ((greatest(fc.ts_start, CURRENT_TIMESTAMP) >= nc.ts_start AND greatest(fc.ts_start, CURRENT_TIMESTAMP) < nc.ts_end) OR (greatest(fc.ts_start, CURRENT_TIMESTAMP) >= nc.ts_start AND nc.ts_end IS NULL))
    JOIN pdm_features_lines_boundary fb ON fb.osmid=fc.osmid AND fb.version=fc.version
    WHERE fb.boundary={countryosmcode}
    AND (({datebuild} >= fc.ts_start AND {datebuild} < fc.ts_end) OR ({datebuild} >= fc.ts_start AND fc.ts_end is null))
 )
 
SELECT ln.osmid osmid, ln.version, ln.ngeom geometry, fs.tags ntags, ln.memberof memberof, ln.pos pos, ln.wtags wtags, ln.wuserid wuserid, fs.userid nuserid, ln.wtimestamp wtimestamp, fs.ts_start ntimestamp
    FROM linesnodes ln
    LEFT JOIN pdm_features_supports_changes fs ON fs.osmid=ln.osmid AND fs.version=ln.version;
"""

gdf = gpd.GeoDataFrame.from_postgis(query, conn, geom_col='geometry')
#gdf = gpd.read_file("/home/ben/DevProjects/temp/databox/pgsql/pdm_extract_points.gpkg")

# ---------------------------------------------
# Factoring and export GeoDataFrame
# ---------------------------------------------

output_path_linesxnodes = output_path / FILENAME_LINESxNODES
gdf.to_file(output_path_linesxnodes)
print("Shapefile created:", output_path_linesxnodes, " | length =", len(gdf), "\n")

# --------------------------------------
# Line Management
# --------------------------------------
def agg_group_to_lines(g):
    first_row = g.iloc[0].copy()
    try:
        first_row["geometry"] = LineString(g["geometry"].apply(lambda p: (p.x, p.y)))
    except Exception:
        first_row["geometry"] = LineString()
    first_row["nodes"] = list(g["osmid"].apply(lambda x: int(x[5:])))
    return first_row

gdf_lines : gpd.GeoDataFrame = gdf.sort_values(["memberof", "pos"])
gdf_lines = gdf_lines.groupby("memberof").apply(agg_group_to_lines).reset_index(drop=True)
gdf_lines = gdf_lines.set_crs(gdf.crs)
gdf_lines["tags"] = gdf_lines["wtags"].map(convert_dict)
for tag in OSM_POWER_TAGS:
    gdf_lines[tag] = gdf_lines["tags"].apply(lambda x: x.pop(tag, None))
gdf_lines["osmid"] = gdf_lines["memberof"]
gdf_lines["userid"] = gdf_lines["wuserid"]
gdf_lines["id"] = gdf_lines["osmid"].apply(lambda x: int(x[5:]))
for key in ["memberof", "ntags", "wtags", "nuserid", "wuserid", "pos", "ntimestamp", "wtimestamp"]:
    del gdf_lines[key]
#print(gdf_lines)

# Export to a shapefile
output_path_lines = output_path / FILENAME_LINES
gdf_lines.to_file(output_path_lines)
print("Shapefile created:", output_path_lines, " | length =", len(gdf_lines), "\n")

# --------------------------------------
# Points Management
# --------------------------------------
def agg_group_to_points(g):
    first_row = g.iloc[0].copy()
    return first_row

gdf_nodes : gpd.GeoDataFrame = gdf.sort_values(["memberof", "pos"])
gdf_nodes = gdf_nodes.groupby("osmid").apply(agg_group_to_points).reset_index(drop=True)
gdf_nodes = gdf_nodes.set_crs(gdf.crs)
gdf_nodes["id"] = gdf_nodes["osmid"].apply(lambda x: int(x[5:]))
gdf_nodes["tags"] = gdf_nodes["ntags"].map(convert_dict)
gdf_nodes["userid"] = gdf_nodes["nuserid"]
for tag in OSM_POWER_TAGS:
    gdf_nodes[tag] = gdf_nodes["tags"].apply(lambda x: x.pop(tag, None))
for key in ["memberof", "ntags", "wtags", "nuserid", "wuserid", "ntimestamp", "wtimestamp"]:
    del gdf_nodes[key]
#print(gdf_points)

# Export to a shapefile
output_path_nodes = output_path / FILENAME_NODES
gdf_nodes.to_file(output_path_nodes)
print("Shapefile created:", output_path_nodes, " | length =", len(gdf_nodes), "\n")