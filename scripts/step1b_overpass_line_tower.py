import geopandas as gpd
import pandas as pd
from pathlib import Path

from utils_ovp import overpass_query, overpass_response_to_gdf
## SETTINGS
import config
COUNTRY_CODE = config.COUNTRY_CODE
DATA_PATH = config.DATA_PATH

OSM_TAGS_WAY = ["name", "type", "route", "power", "voltage", "circuits", "cables", "wires", "operator", "operator:wikidata", "location", "note", "wikidata"]

FILENAME_COUNTRYSHAPE = "osm_brut_country_shape.gpkg"

def main(countrycode):
    Path(DATA_PATH / countrycode).mkdir(parents=True, exist_ok=True)
    print("  -- Downloading power lines")
    overpass_response = query_powerline(countrycode)
    gdf = overpass_response_to_gdf(overpass_response, tags=["power", "circuits", "cables", "voltage", "wires"])
    gdf.to_file(DATA_PATH / countrycode / "osm_brut_power_line.gpkg")

    #print("  -- Downloading substations")
    #overpass_response = query_substation(countrycode)
    #gdf = overpass_response_to_gdf(overpass_response, tags=["power", "substation"])
    #gdf.to_file(DATA_PATH / countrycode / "osm_brut_power_substation.gpkg")

    print("  -- Downloading towers and transitions")
    overpass_response = query_node_tower_transition(countrycode)
    gdf = overpass_response_to_gdf(overpass_response, tags=["power", "line_management", "voltage"])
    gdf.to_file(DATA_PATH / countrycode / "osm_brut_power_tower_transition.gpkg")


def query_powerline(countrycode:str, querydate=None) -> str:
    # Add date if it is precised
    strdate = f"[date:\"{querydate}T00:00:00Z\"]" if querydate is not None else ""
    # Build query
    query = f"""[out:json][timeout:1000]{strdate};
                area["ISO3166-1:alpha2"={countrycode}]->.searchArea;
                (way["power"="line"](area.searchArea);way["power"="cable"](area.searchArea););
                out meta geom;"""
    return overpass_query(query)


def query_substation(countrycode:str, querydate=None) -> str:
    # Add date if it is precised
    strdate = f"[date:\"{querydate}T00:00:00Z\"]" if querydate is not None else ""
    # Build query
    query = f"""[out:json][timeout:1000]{strdate};
                area["ISO3166-1:alpha2"={countrycode}]->.searchArea;
                nwr["power"="substation"](area.searchArea);
                out meta geom;"""
    return overpass_query(query)


def query_node_tower_transition(countrycode:str, querydate=None, verbose=False) -> str:
    # Add date if it is precised
    strdate = f"[date:\"{querydate}T00:00:00Z\"]" if querydate is not None else ""
    # Build query
    query = f"""[out:json][timeout:1000]{strdate};
                area["ISO3166-1:alpha2"={countrycode}]->.searchArea;
                way[power=line](area.searchArea);>->.nodeway;
                way[power=cable](area.searchArea);>->.nodecable;
                (node["power"="tower"](area.searchArea);node["line_management"](area.searchArea);node["power"="connection"](area.searchArea);.nodeway;.nodecable;);
                out meta geom;"""
    if verbose: print(query)
    return overpass_query(query)



if __name__ == '__main__':
    main(COUNTRY_CODE)
