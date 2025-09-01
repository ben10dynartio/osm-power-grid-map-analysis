import geopandas as gpd
import pandas as pd
from pathlib import Path
import requests
import osm2geojson

from utils_ovp import overpass_query, overpass_response_to_gdf
from utils_shape import shape_to_polygon


## SETTINGS
import config
COUNTRY_CODE = config.COUNTRY_CODE
DATA_PATH = config.DATA_PATH
OSM_POWER_TAGS = config.OSM_POWER_TAGS


LOG_LEVEL = "DEBUG"

# :todo: if Substation relation include an other substation, then the bigger substation has to be removed. (Currently = no specific process)
# cf : query_substation_in_substation

def main(countrycode):
    print("  -- Downloading circuits")
    overpass_response = query_circuit_rel(countrycode)
    lst_element = []
    # Building table info, a row for each relation x member
    for rel in overpass_response['elements']:
        for member in rel["members"]:
            infobase = rel.copy()
            infobase["object_type"] = infobase["type"]
            del infobase["type"]
            del infobase["members"]
            del infobase["bounds"]
            infobase["member_osmid"] = member["type"] + "/" + str(member["ref"])
            infobase["member_role"] = member["role"]
            lst_element.append(infobase)
    df = pd.DataFrame(lst_element)
    df["osmid"] = df["object_type"] + "/" + df["id"].astype(str)
    for keyop in OSM_POWER_TAGS:
        df[keyop] = df["tags"].apply(lambda x: x.get(keyop))

    print(" -- Check member tags")
    df_check = df[~df["member_role"].isin(["substation", "line", "endpoint", "section", "tap"])]
    for row in df_check.to_dict(orient='records'):
        print("* ERROR WITH : ", row)

    df.to_csv(DATA_PATH / countrycode / "osm_brut_power_circuit_members.csv", index=False)


def query_circuit_rel(countrycode:str):
    """
    Get circuit relation
    """
    query = f"""
[out:json][timeout:1000];
area["ISO3166-1:alpha2"={countrycode}]->.searchArea;
(rel["power"="circuit"](area.searchArea);rel["route"="power"](area.searchArea););
out meta geom;"""
    return overpass_query(query, log_level=LOG_LEVEL)


def query_connection_in_rel(countrycode:str):
    """
    _
    """

    query = f"""
[out:json][timeout:1000];
area["ISO3166-1:alpha2"={countrycode}]->.searchArea;
(rel["power"="circuit"](area.searchArea);rel["route"="power"](area.searchArea);)->.subRel;
foreach.subRel -> .oneRel (
    way(r.oneRel);
    foreach (
        convert Feature
        component_way_id = _.u(id()),
        component_rel_id = "",
        constitute_rel_id = oneRel.u(id());
        (._;.returnSet;)->.returnSet;
    );
  	rel(r.oneRel);
    foreach (
        convert Feature
        component_way_id = "",
        component_rel_id = _.u(id()),
        constitute_rel_id = oneRel.u(id());
        (._;.returnSet;)->.returnSet;
    );
);
.returnSet;
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