import geopandas as gpd
import pandas as pd
from pathlib import Path
import requests
import osm2geojson
from geopandas import GeoDataFrame

from utils.utils_ovp import overpass_query, overpass_response_to_gdf
from utils.utils_shape import shape_to_polygon


## SETTINGS
import config
COUNTRY_CODE = config.COUNTRY_CODE
DATA_PATH = config.DATA_PATH
OSM_POWER_TAGS = config.OSM_POWER_TAGS

LOG_LEVEL = "ERROR"

# :todo: if Substation relation include an other substation, then the bigger substation has to be removed. (Currently = no specific process)
# cf : query_substation_in_substation

def main(countrycode):
    print("  -- Checking duplicate substation through relation")
    overpass_response = query_substation_in_substation(countrycode)
    gdf_subsub: GeoDataFrame = overpass_response_to_gdf(overpass_response, tags=OSM_POWER_TAGS)
    if len(gdf_subsub)>0:
        print("WARNING : They are substation in substation relation. It might break data analysis. Have a deeper look !")

    print("  -- Downloading substations")
    overpass_response = query_substation_way_and_rel(countrycode)
    gdf_sub : GeoDataFrame= overpass_response_to_gdf(overpass_response, tags=OSM_POWER_TAGS)
    gdf_sub.to_file(DATA_PATH / countrycode / "osm_brut_power_substation.gpkg")

    print("  -- Downloading substations way component and merge with relation")
    overpass_response = query_substation_way_in_rel(countrycode)
    gdf_comp : GeoDataFrame = overpass_response_to_gdf(overpass_response, tags=OSM_POWER_TAGS)
    #gdf_comp.to_file(DATA_PATH / countrycode / "osm_brut_power_substation_rel_component.gpkg")

    if len(gdf_comp)>0:
        overpass_response = query_connection_way_in_rel(countrycode)
        df = pd.DataFrame([{"component_way_id": int(d["tags"]["component_way_id"]),
                            "component_rel_id": int(d["tags"]["component_rel_id"])}
                           for d in overpass_response['elements']])

        df_sub_rel = pd.DataFrame(gdf_sub[gdf_sub["object_type"]=="relation"].copy())
        del df_sub_rel["geometry"]
        gdf_comp = gdf_comp.merge(df, how='left', left_on='id', right_on='component_way_id').reset_index()
        gdf_comp = gdf_comp.merge(df_sub_rel, how='left', left_on='component_rel_id', right_on='id', suffixes=("_way", None)).reset_index()
        del gdf_comp["component_rel_id"]
        del gdf_comp["component_way_id"]
        gdf_comp.to_file(DATA_PATH / countrycode / "osm_brut_power_substation_rel_component.gpkg")

        # Gathering multipart substation
        tdf = gdf_comp.groupby("osmid", as_index=False).agg({'osmid_way':lambda x: list(x)})
        tdf["related_osmid"] = tdf["osmid_way"].astype(str)
        del tdf["osmid_way"]

        gdf_comp = gdf_comp.dissolve("osmid")
        gdf_comp = gdf_comp.merge(tdf, left_on="osmid", right_on="osmid")
        #gdf_comp.to_file(DATA_PATH / countrycode / "osm_clean_power_substation.gpkg")

    gdf_sub_way = gdf_sub[gdf_sub["object_type"] != "relation"].copy()
    if len(gdf_comp) > 0:
        final_sub_gdf = gpd.GeoDataFrame(pd.concat([gdf_comp, gdf_sub_way]), geometry="geometry", crs=4326)
    else:
        final_sub_gdf = gdf_sub_way
    final_sub_gdf["geometry"] = final_sub_gdf["geometry"].apply(lambda x: shape_to_polygon(x))
    for key in ["level_0", "index"]:
        if key in final_sub_gdf.columns:
            del final_sub_gdf[key]
    delcol = [col for col in final_sub_gdf.columns if col.endswith("_way")]
    for col in delcol:
        del final_sub_gdf[col]
    final_sub_gdf.to_file(DATA_PATH / countrycode / "osm_clean_power_substation.gpkg")


def query_substation_way_and_rel(countrycode:str):
    """
    Get substation (of types way and relation)
    """
    query = f"""
[out:json][timeout:1000];
area["ISO3166-1:alpha2"={countrycode}]->.searchArea;
nwr["power"="substation"](area.searchArea);
out meta geom;"""
    return overpass_query(query, log_level=LOG_LEVEL)


def query_substation_way_in_rel(countrycode:str):
    """
    Get ways in substation relation
    """
    query = f"""
[out:json][timeout:1000];
area["ISO3166-1:alpha2"={countrycode}]->.searchArea;
relation["power"="substation"](area.searchArea)->.subRel;
way(r.subRel);
out meta geom;"""
    return overpass_query(query, log_level=LOG_LEVEL)


def query_substation_in_substation(countrycode:str):
    query = f"""
[out:json][timeout:1000];
area["ISO3166-1:alpha2"={countrycode}]->.searchArea;
relation["power"="substation"](area.searchArea)->.subRel;
(rel(r.subRel)["power"="substation"];);
out meta geom; """
    return overpass_query(query, log_level=LOG_LEVEL)


def query_connection_way_in_rel(countrycode:str):
    query = f"""
[out:json][timeout:1000];
area["ISO3166-1:alpha2"={countrycode}]->.searchArea;
relation["power"="substation"](area.searchArea)->.subRel;
foreach.subRel -> .oneRel (
    way(r.oneRel);
    foreach (
        convert Feature
        component_way_id = _.u(id()),
        component_rel_id = oneRel.u(id());
        (._;.returnSet;)->.returnSet;
    );
);
.returnSet;
out meta geom;"""

    return overpass_query(query, log_level=LOG_LEVEL)



if __name__ == '__main__':
    main(COUNTRY_CODE)