import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import geopandas as gpd
import pandas as pd
from pathlib import Path

from utils.utils_ovp import overpass_query, overpass_response_to_gdf
## SETTINGS
import config
COUNTRY_CODE = config.COUNTRY_CODE
DATA_PATH = config.DATA_PATH

OSM_TAGS_WAY = ["name", "type", "route", "power", "voltage", "circuits", "cables", "wires", "operator", "operator:wikidata", "location", "note", "wikidata"]

FILENAME_COUNTRYSHAPE = "osm_brut_country_shape.gpkg"

def main(countrycode):
    Path(DATA_PATH / countrycode).mkdir(parents=True, exist_ok=True)

    print("  -- Downloading country shape of", countrycode)
    if countrycode != "PY":
        # There is a osm2geojson.json2geojson error for Paraguay ... it need to be investigated
        # Request shape manually instead for this country

        try:
            overpass_response = query_country_shape(countrycode)
            gdf = overpass_response_to_gdf(overpass_response, tags=["name", "name:en"])
            gdf.to_file(DATA_PATH / countrycode / "osm_brut_country_shape.gpkg")
        except Exception as e:
            print("Exception raised for querying country shape = ", e)
            if Path(DATA_PATH / countrycode / "osm_brut_country_shape.gpkg").is_file():
                print("Country shape file already exists. It will be used for computation.")
            else:
                print("NO Country shape file existing. Errors might be raised.")

    # Not necessary (and makes problems for some countries)
    """print("-- Downloading country cities")
    overpass_response = query_country_cities(countrycode)
    gdf = overpass_response_to_gdf(overpass_response, tags=["name", "name:en", "capital", "place", "population", "wikidata"])
    gdf.to_file(DATA_PATH + countrycode + "/osm_brut_country_cities.gpkg")"""


def query_country_shape(countrycode:str, querydate=None) -> str:
    # Add date if it is precised
    strdate = f"[date:\"{querydate}T00:00:00Z\"]" if querydate is not None else ""
    # Build query
    query = f"""[out:json][timeout:1000]{strdate};
                rel["ISO3166-1:alpha2"="{countrycode}"];
                out geom;"""
    return overpass_query(query, retry=1)


def query_country_cities(countrycode:str, querydate=None) -> str:
    # Add date if it is precised
    strdate = f"[date:\"{querydate}T00:00:00Z\"]" if querydate is not None else ""
    # Build query
    query = f"""[out:json][timeout:1000]{strdate};
                area["ISO3166-1:alpha2"={countrycode}]->.searchArea;
                node["capital"~"^(1|2|3|4|5|6)$"](area.searchArea);
                out meta geom;"""
    return overpass_query(query, retry=1)


if __name__ == '__main__':
    main(COUNTRY_CODE)
