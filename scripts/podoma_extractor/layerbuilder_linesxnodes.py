import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import config
from utils.utils_data import convert_dict

from pdmconf import connectpdm, OSM_POWER_TAGS, OUTPUT_FOLDER_NAME

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

args = parser.parse_args()
datebuild = args.date
countryosmcode = args.country
output_folder_name = args.folder

# ---------------------------------------------
# Connect to Podoma PostgreSQL/PostGIS database
# ---------------------------------------------
conn = connectpdm()

query = f"""
WITH lines AS (
    SELECT fc.osmid osmid, fc.version version, fc.tags wtags, fc.userid wuserid, fc.ts_start wtimestamp
    FROM pdm_features_lines_changes fc
    JOIN pdm_features_lines_boundary fb ON fc.osmid=fb.osmid AND fc.version=fb.version
    WHERE fb.boundary={countryosmcode}
    AND (({datebuild} >= fc.ts_start AND {datebuild} < fc.ts_end) OR ({datebuild} >= fc.ts_start AND fc.ts_end is null))
), nodesid AS (
    SELECT fm.memberid osmid, fm.osmid memberof, fm.pos pos, lines.wtags wtags, lines.wuserid wuserid, lines.wtimestamp wtimestamp
    FROM pdm_members_lines fm
    JOIN lines ON fm.osmid=lines.osmid AND fm.version=lines.version
), nodes AS (
    SELECT fc.osmid osmid, fc.geom geom, nid.memberof memberof, nid.pos pos, nid.wtags wtags, nid.wuserid wuserid, nid.wtimestamp wtimestamp, fc.ts_start ntimestamp
    FROM pdm_features_lines_changes fc
    JOIN nodesid nid ON fc.osmid=nid.osmid
    WHERE (({datebuild} >= fc.ts_start AND {datebuild} < fc.ts_end) OR ({datebuild} >= fc.ts_start AND fc.ts_end is null))
), supports AS (
    SELECT fc.osmid osmid, fc.tags tags, fc.userid nuserid
    FROM pdm_features_supports_changes fc
    JOIN pdm_features_supports_boundary fb ON fc.osmid=fb.osmid AND fc.version=fb.version
    WHERE fb.boundary={countryosmcode}
    AND (({datebuild} >= fc.ts_start AND {datebuild} < fc.ts_end) OR ({datebuild} >= fc.ts_start AND fc.ts_end is null))
), joined AS (
    SELECT nodes.osmid osmid, nodes.geom geometry, supports.tags ntags, nodes.memberof memberof, nodes.pos pos, nodes.wtags wtags, nodes.wuserid wuserid, supports.nuserid nuserid, nodes.wtimestamp wtimestamp, nodes.ntimestamp ntimestamp
    FROM nodes
    LEFT JOIN supports ON nodes.osmid=supports.osmid
)
SELECT * FROM joined;
"""

# ---------------------------------------------
# Load data into a GeoDataFrame
# ---------------------------------------------

output_path = config.DATA_PATH / output_folder_name
output_path.mkdir(exist_ok=True, parents=True)

gdf = gpd.GeoDataFrame.from_postgis(query, conn, geom_col='geometry')
#gdf = gpd.read_file("/home/ben/DevProjects/temp/databox/pgsql/pdm_extract_points.gpkg")

output_path_linesxnodes = output_path / FILENAME_LINESxNODES
gdf.to_file(output_path_linesxnodes)
print("Shapefile created:", output_path_linesxnodes, "\n")

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
print("Shapefile created:", output_path_lines, "\n")

# --------------------------------------
# Points Management
# --------------------------------------
def agg_group_to_points(g):
    first_row = g.iloc[0].copy()
    return first_row

gdf_points : gpd.GeoDataFrame = gdf.sort_values(["memberof", "pos"])
gdf_points = gdf_points.groupby("osmid").apply(agg_group_to_points).reset_index(drop=True)
gdf_points = gdf_points.set_crs(gdf.crs)
gdf_points["id"] = gdf_points["osmid"].apply(lambda x: int(x[5:]))
gdf_points["tags"] = gdf_points["ntags"].map(convert_dict)
gdf_points["userid"] = gdf_points["nuserid"]
for tag in OSM_POWER_TAGS:
    gdf_points[tag] = gdf_points["tags"].apply(lambda x: x.pop(tag, None))
for key in ["memberof", "ntags", "wtags", "nuserid", "wuserid", "ntimestamp", "wtimestamp"]:
    del gdf_points[key]
#print(gdf_points)

# Export to a shapefile
output_path_points = output_path / FILENAME_NODES
gdf_points.to_file(output_path_points)
print("Shapefile created:", output_path_points, "\n")