import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import config

import os
import argparse
import psycopg2
from psycopg2.extras import register_hstore

import geopandas as gpd
from shapely import wkb

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--objecttype", type=str, help="Object Type", default="lines")
parser.add_argument("-c", "--country", type=str, help="Country OSM code", default="80500")

args = parser.parse_args()
countryosmcode = args.country
objecttype = args.objecttype
#80500

# ---------------------------------------------
# Connect to PostgreSQL/PostGIS database
# ---------------------------------------------
dbname=os.getenv("PODOMA_DBNAME", "podoma")
user=os.getenv("PODOMA_DBUSER", "podoma")
password=os.getenv("PODOMA_DBPASS", "podomapass")
host=os.getenv("PODOMA_DBHOST", "localhost")
port=os.getenv("PODOMA_DBPORT", "5432")

print("Querying on ", dbname, "on", host)

conn = psycopg2.connect(
    dbname=dbname,
    user=user,
    password=password,
    host=host,
    port=port,
)

register_hstore(conn)

query_dict = {}

query = """
    SELECT *, ST_AsBinary(geom) AS geom_wkb
    FROM pdm_boundary LIMIT 20;
"""

query_dict["countryshapes"] = """
    SELECT * AS geom_wkb
    FROM pdm_boundary WHERE admin_level = 2;
"""

query_dict["lines"]  = f"""
SELECT fc.osmid, fc.version, fc.tags, fl.label, fc.geom_len, fc.geom FROM pdm_features_lines_changes fc
JOIN pdm_features_lines_boundary fb ON fb.osmid=fc.osmid AND fb.version=fc.version
JOIN pdm_features_lines_labels fl ON fl.osmid=fc.osmid AND fl.version=fc.version
WHERE fb.boundary = {countryosmcode}
AND fc.geom_len <> 0 
AND fl.label='transmission'
AND (CURRENT_TIMESTAMP BETWEEN fc.ts_start AND fc.ts_end OR (CURRENT_TIMESTAMP >= fc.ts_start AND fc.ts_end is null));
        """


# The following query return all node of power line and corresponding ways tags
query_dict["points"]  = f"""
WITH lines AS (
    SELECT fc.osmid osmid, fc.version version, fc.tags wtags
    FROM pdm_features_lines_changes fc
    JOIN pdm_features_lines_boundary fb ON fc.osmid=fb.osmid AND fc.version=fb.version
    WHERE fb.boundary=80500
    AND (('2025-11-28' >= fc.ts_start AND '2025-11-28' < fc.ts_end) OR ('2025-11-28' >= fc.ts_start AND fc.ts_end is null))
), nodesid AS (
    SELECT fm.memberid osmid, fm.osmid memberof, fm.pos pos, lines.wtags wtags
    FROM pdm_members_lines fm
    JOIN lines ON fm.osmid=lines.osmid AND fm.version=lines.version
), nodes AS (
    SELECT fc.osmid osmid, fc.geom geom, nid.memberof memberof, nid.pos pos, nid.wtags wtags
    FROM pdm_features_lines_changes fc
    JOIN nodesid nid ON fc.osmid=nid.osmid
    WHERE (('2025-11-28' >= fc.ts_start AND '2025-11-28' < fc.ts_end) OR ('2025-11-28' >= fc.ts_start AND fc.ts_end is null))
), supports AS (
    SELECT fc.osmid osmid, fc.tags tags
    FROM pdm_features_supports_changes fc
    JOIN pdm_features_supports_boundary fb ON fc.osmid=fb.osmid AND fc.version=fb.version
    WHERE fb.boundary=80500
    AND (('2025-11-28' >= fc.ts_start AND '2025-11-28' < fc.ts_end) OR ('2025-11-28' >= fc.ts_start AND fc.ts_end is null))
), joined AS (
    SELECT nodes.osmid osmid, nodes.geom geom, supports.tags ntags, nodes.memberof memberof, nodes.pos pos, nodes.wtags wtags
    FROM nodes
    LEFT JOIN supports ON nodes.osmid=supports.osmid
)
SELECT * FROM joined;
"""

# The following query return all node of power line, but without their tags
query_dict["pointsx3"]  = f"""
WITH lines AS (
    SELECT fc.osmid osmid, fc.version version
    FROM pdm_features_lines_changes fc
    JOIN pdm_features_lines_boundary fb ON fc.osmid=fb.osmid AND fc.version=fb.version
    WHERE fb.boundary=80500
    AND (('2025-11-28' >= fc.ts_start AND '2025-11-28' < fc.ts_end) OR ('2025-11-28' >= fc.ts_start AND fc.ts_end is null))
), nodesid AS (
    SELECT fm.memberid osmid, fm.osmid memberof, fm.pos pos
    FROM pdm_members_lines fm
    JOIN lines ON fm.osmid=lines.osmid AND fm.version=lines.version
), nodes AS (
    SELECT fc.osmid osmid, fc.geom geom, fc.tags tags, nid.memberof memberof, nid.pos pos
    FROM pdm_features_lines_changes fc
    JOIN nodesid nid ON fc.osmid=nid.osmid
    WHERE (('2025-11-28' >= fc.ts_start AND '2025-11-28' < fc.ts_end) OR ('2025-11-28' >= fc.ts_start AND fc.ts_end is null))
)

SELECT * FROM nodes;
"""

query_dict["pointsx2"]  = f"""
with nodes as (
    SELECT
    osmid,
    version,
    geom,
    tags,
    ts as ts_start,
    LEAD(ts) OVER (PARTITION BY osmid ORDER BY version) AS ts_end
    FROM pdm_features_supports
	WHERE osmid like 'n%' and action != 'delete'
), list as (
	SELECT f.osmid osmid, f.version version, f.tags wtags, n.osmid nid, n.geom geom, n.tags ntags
	FROM pdm_features_lines_changes f
	JOIN pdm_members_lines fm ON fm.osmid=f.osmid AND fm.version=f.version
	JOIN pdm_features_lines_boundary fb ON f.osmid=fb.osmid AND f.version=fb.version
	JOIN nodes n ON n.osmid=fm.memberid AND ((greatest(f.ts_start, '2024-01-01') >= n.ts_start AND greatest(f.ts_start, '2024-01-01') < n.ts_end) OR (greatest(f.ts_start, '2024-01-01') >= n.ts_start AND n.ts_end IS NULL))
	WHERE f.osmid like 'w%'
	AND fb.boundary=80500
	AND (('2025-11-28' >= f.ts_start AND '2025-11-28' < f.ts_end) OR ('2025-11-28' >= f.ts_start AND f.ts_end is null))
)
SELECT * FROM list;
"""

query_dict["pointsx1"]  = f"""
with nodes as (
    SELECT
    osmid,
    version,
    geom,
    tags,
    ts as ts_start,
    LEAD(ts) OVER (PARTITION BY osmid ORDER BY version) AS ts_end
    FROM pdm_features_supports
	WHERE osmid like 'n%' and action != 'delete'
), list as (
	SELECT f.osmid osmid, f.version version, f.tags wtags, n.osmid nid, n.geom geom, n.tags ntags
	FROM pdm_features_lines_changes f
	JOIN pdm_members_lines fm ON fm.osmid=f.osmid AND fm.version=f.version
	JOIN pdm_features_lines_boundary fb ON f.osmid=fb.osmid AND f.version=fb.version
	JOIN nodes n ON n.osmid=fm.memberid AND ((greatest(f.ts_start, '2024-01-01') >= n.ts_start AND greatest(f.ts_start, '2024-01-01') < n.ts_end) OR (greatest(f.ts_start, '2024-01-01') >= n.ts_start AND n.ts_end IS NULL))
	WHERE f.osmid like 'w%'
	AND fb.boundary=80500
	AND (('2025-11-28' >= f.ts_start AND '2025-11-28' < f.ts_end) OR ('2025-11-28' >= f.ts_start AND f.ts_end is null))
)
SELECT * FROM list;
"""

query_dict["pointsx0"]  = f"""
SELECT fm.memberid, fs.version, fs.tags, fs.geom FROM pdm_members_lines fm
JOIN pdm_features_lines_boundary fb ON fm.osmid=fb.osmid AND fm.version=fb.version
JOIN pdm_features_lines_changes fc ON fc.osmid=fm.osmid AND fc.version=fm.version
LEFT JOIN pdm_features_supports_changes fs ON fm.memberid=fs.osmid AND fc.version=fs.version
WHERE fb.boundary = {countryosmcode}
AND (CURRENT_TIMESTAMP BETWEEN fc.ts_start AND fc.ts_end OR (CURRENT_TIMESTAMP >= fc.ts_start AND fc.ts_end is null))
AND (CURRENT_TIMESTAMP BETWEEN fs.ts_start AND fs.ts_end OR (CURRENT_TIMESTAMP >= fs.ts_start AND fs.ts_end is null));
"""

query_dict["substations"]  = f"""
SELECT fc.osmid, fc.version, fc.tags, fc.geom  FROM pdm_features_substations_changes fc
JOIN pdm_features_substations_boundary fb ON fc.osmid=fb.osmid AND fc.version=fb.version
WHERE fb.boundary = {countryosmcode}
AND (CURRENT_TIMESTAMP BETWEEN fc.ts_start AND fc.ts_end OR (CURRENT_TIMESTAMP >= fc.ts_start AND fc.ts_end is null));
"""

# ---------------------------------------------
# Load data into a GeoDataFrame
# ---------------------------------------------
gdf = gpd.GeoDataFrame.from_postgis(query_dict[objecttype], conn, geom_col='geom')

if objecttype == "substations":
    gdf["geom"] = gdf["geom"].polygonize()

# ---------------------------------------------
# Export to a shapefile
# ---------------------------------------------
output_path = config.DATA_PATH / "pgsql"
output_path.mkdir(exist_ok=True, parents=True)
output_path = output_path / f"pdm_extract_{objecttype}.gpkg"
gdf.to_file(output_path)

print("Shapefile created:", output_path)
