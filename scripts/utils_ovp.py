import requests
import osm2geojson
import geopandas as gpd

def overpass_query(query:str, log_level="INFO"):
    """Send an overpass query to the API """
    if log_level in ["DEBUG"]: print("------SEND OVERPASS------\n", query, "\n-------END OVERPASS------")
    url = "http://overpass-api.de/api/interpreter"
    response = requests.get(url, params={'data': query})

    if response.status_code == 200:
        return response.json()
    else:
        raise RuntimeError(f"Erreur with query {response.status_code}: {response.text}")

def overpass_response_to_gdf(response, tags=[]):
    geojson = osm2geojson.json2geojson(response)
    if len(geojson['features']):
        gdf = gpd.GeoDataFrame.from_features(geojson, crs=4326).fillna("")
        gdf["object_type"] = gdf["type"]
        del gdf["type"]
        gdf["osmid"] = gdf["object_type"] + "/" + gdf["id"].astype(str)
    else:
        print("  /!\\ no feature or error")
        gdf = gpd.GeoDataFrame({"geometry":[], "tags":[], "osmid":[], "object_type":[], "id":[], "nodes":[]}, geometry='geometry', crs=4326)
    gdf["tags"] = gdf["tags"].apply(lambda x: {} if not x else x)
    for tag in tags:
        gdf[tag] = gdf["tags"].apply(lambda x: x.get(tag))
    return gdf