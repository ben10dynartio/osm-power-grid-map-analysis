import geopandas as gpd
from pathlib import Path
import requests
import osm2geojson

## SETTINGS
COUNTRY_CODE = "NG"
DATA_PATH = "data/"

def overpass_query(query:str):
    """Send an overpass query to the API """
    url = "http://overpass-api.de/api/interpreter"
    response = requests.get(url, params={'data': query})

    if response.status_code == 200:
        return response.json()
    else:
        raise RuntimeError(f"Erreur with query {response.status_code}: {response.text}")


def query_country_shape(countrycode:str, querydate=None) -> str:
    # Add date if it is precised
    strdate = f"[date:\"{querydate}T00:00:00Z\"]" if querydate is not None else ""
    # Build query
    query = f"""[out:json][timeout:1000]{strdate};
                rel["ISO3166-1:alpha2"={countrycode}];
                out geom;"""
    return overpass_query(query)


def query_country_cities(countrycode:str, querydate=None) -> str:
    # Add date if it is precised
    strdate = f"[date:\"{querydate}T00:00:00Z\"]" if querydate is not None else ""
    # Build query
    query = f"""[out:json][timeout:1000]{strdate};
                area["ISO3166-1:alpha2"={countrycode}]->.searchArea;
                node["capital"~"^(1|2|3|4|5|6)$"](area.searchArea);
                out meta geom;"""
    return overpass_query(query)


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


def query_node_tower_transition(countrycode:str, querydate=None) -> str:
    # Add date if it is precised
    strdate = f"[date:\"{querydate}T00:00:00Z\"]" if querydate is not None else ""
    # Build query
    query = f"""[out:json][timeout:1000]{strdate};
                area["ISO3166-1:alpha2"={countrycode}]->.searchArea;
                (node["power"="tower"](area.searchArea);node["line_management"="transition"](area.searchArea););
                out meta geom;"""
    return overpass_query(query)


def overpass_response_to_gdf(response, tags=[]):
    geojson = osm2geojson.json2geojson(response)
    gdf = gpd.GeoDataFrame.from_features(geojson, crs=4326)
    gdf["osmid"] = gdf["type"] + "/" + gdf["id"].astype(str)
    for tag in tags:
        gdf[tag] = gdf["tags"].apply(lambda x: x.get(tag))
    return gdf


def download_data(countrycode):
    Path(DATA_PATH + countrycode).mkdir(parents=True, exist_ok=True)

    print("-- Downloading country shape")
    overpass_response = query_country_shape(countrycode)
    gdf = overpass_response_to_gdf(overpass_response, tags=["name", "name:en"])
    gdf.to_file(DATA_PATH + countrycode + "/osm_brut_country_shape.gpkg")

    print("-- Downloading country cities")
    overpass_response = query_country_cities(countrycode)
    gdf = overpass_response_to_gdf(overpass_response, tags=["name", "name:en", "capital", "place", "population", "wikidata"])
    gdf.to_file(DATA_PATH + countrycode + "/osm_brut_country_cities.gpkg")

    print("-- Downloading power lines")
    overpass_response = query_powerline(countrycode)
    gdf = overpass_response_to_gdf(overpass_response, tags=["power", "circuits", "cables", "voltage"])
    gdf.to_file(DATA_PATH + countrycode + "/osm_brut_power_line.gpkg")

    print("-- Downloading substations")
    overpass_response = query_substation(countrycode)
    gdf = overpass_response_to_gdf(overpass_response, tags=["power", "substation"])
    gdf.to_file(DATA_PATH + countrycode + "/osm_brut_power_substation.gpkg")

    print("-- Downloading towers and transitions")
    overpass_response = query_node_tower_transition(countrycode)
    gdf = overpass_response_to_gdf(overpass_response, tags=["power", "line_management"])
    gdf.to_file(DATA_PATH + countrycode + "/osm_brut_power_tower_transition.gpkg")


if __name__ == "__main__":
    download_data(COUNTRY_CODE)
