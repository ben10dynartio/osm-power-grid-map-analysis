import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point, LineString

from utils.utils_gpd import to_empty_file
from utils.utils_exec import errors_to_file, add_error
from utils.utils_data import convert_int

## SETTINGS
import config
COUNTRY_CODE = config.COUNTRY_CODE
DATA_PATH = config.DATA_PATH
OSM_POWER_TAGS = config.OSM_POWER_TAGS
LOG_LEVEL = config.LOG_LEVEL

errors = []

# Cleaning data
if config.SOURCE == "overpass":
    FILENAME_INPUT_POWER_CIRCUITS = "osm_brut_power_circuit_members.csv"
elif config.SOURCE == "podoma":
    FILENAME_INPUT_POWER_CIRCUITS = "osm_pdm_power_circuits.csv"
else:
    raise ValueError(f"Unknown source : {config.SOURCE}")

def main():
    gdf_nodes = gpd.read_file(DATA_PATH / COUNTRY_CODE / "pre_graph_power_nodes.gpkg")
    nodes_geo_dict = {row["osmid"]:row["geometry"] for row in gdf_nodes.to_dict(orient='records')}
    gdf_lines = gpd.read_file(DATA_PATH / COUNTRY_CODE / "pre_graph_power_lines.gpkg")

    if len(gdf_lines) == 0 or len(gdf_nodes) == 0:
        to_empty_file(DATA_PATH / COUNTRY_CODE / "pre_graph_power_lines_circuit.gpkg")
        return

    print("  -- Files opened, CRS =", gdf_nodes.crs, gdf_lines.crs)

    # --------- Export --------------------
    df_circ = pd.read_csv(DATA_PATH / COUNTRY_CODE / FILENAME_INPUT_POWER_CIRCUITS)

    df_circ["member_role"] = np.where(df_circ["member_role"].isin(["substation", "endpoint"]),
                                 "substation", df_circ["member_role"])
    df_circ["member_role"] = np.where(df_circ["member_role"].isin(["line", "section"]),
                                 "section", df_circ["member_role"])
    df_circ["power"] = np.where((df_circ["type"]=="route") & (df_circ["route"]=="power"),
                                 "circuit", df_circ["power"])
    df_circ["type"] = np.where((df_circ["type"]=="route") & (df_circ["route"]=="power"),
                          "power", df_circ["type"])
    del df_circ["route"]

    # --------- Manage and check "circuit" tag as int --------------------
    df_circ["circuits_int"] = df_circ["circuits"].apply(lambda x: convert_int(x, default=1))
    temp_circuits_problem = df_circ[df_circ["circuits"] == -1]
    for row in temp_circuits_problem.to_dict(orient='records'):
        add_error(errors, {"name": "CircuitsNumber",
                           "description": f"Incorrect circuit number [{row['circuits']}]",
                           "osmid": row["osmid"]})
    df_circ["circuits"] = np.where(df_circ["circuits_int"] == -1,
                                    1, df_circ["circuits_int"])
    del df_circ["circuits_int"]

    # --------- Manage and check "cables" tag as int --------------------
    df_circ["cables_int"] = df_circ["cables"].apply(lambda x: convert_int(x, default=3))
    temp_cables_problem = df_circ[df_circ["cables_int"] == -1]
    for row in temp_cables_problem.to_dict(orient='records'):
        add_error(errors, {"name": "CablesNumber",
                           "description": f"Incorrect cables number [{row['cables']}]",
                           "osmid": row["osmid"]})
    df_circ["cables"] = np.where(df_circ["cables_int"] == -1,
                                   3, df_circ["cables_int"])
    del df_circ["cables_int"]

    """print(gdf_nodes)
    print(gdf_lines)
    print(gdf_lines.iloc[0])
    print(df_circ)
    print(df_circ.iloc[0])"""

    circuit_rel_ids = df_circ["id"].unique().tolist()

    print("  -- Circuit analysis ")
    all_new_lines = []
    for circuit in circuit_rel_ids:
        tdf = df_circ[df_circ["id"]==circuit]
        subs = tdf[tdf["member_role"]=="substation"]
        if len(subs)<=1:
            add_error(errors, {"name": "IncompleteCircuitRelation",
                               "description": f"Incorrect Circuit Relation",
                               "id": circuit, "objecttype": "relation"})
        elif len(subs)==2:
            newline = subs.iloc[0].copy()
            for i in [0, 1]:
                row = subs.iloc[i]
                newline[f"nodetype{i}"] = row["substation"]
                newline[f"osmid{i}"] = row["member_osmid"]
            try:
                newline["geometry"] = LineString([nodes_geo_dict[newline[f"osmid0"]], nodes_geo_dict[newline[f"osmid1"]]])
            except KeyError:
                keyerror = newline[f"osmid0"] if newline[f"osmid0"] not in nodes_geo_dict else newline[f"osmid1"]
                add_error(errors, {"name": "NotFoundSubstationKey",
                                   "description": f"Not found Substation Key in list",
                                   "osmid":keyerror,})
                continue
            except TypeError as e:
                add_error(errors, {"name": "SkippedCircuitForUnknownReason",
                                   "description": f"???? / row",
                                   "osmid": row["member_osmid"], })
                continue
            all_new_lines.append(newline)
        else: # (3 or more substation)
            add_error(errors, {"name": "TripleCircuitRelation",
                               "description": f"Not an error, but a test case - look at triple substations circuits | topology = {tdf["topology"].unique().tolist()}",
                               "osmid": f"relation/{circuit}"}) #, "details":str(tdf.columns)})
            print("WARNING : Triple circuit relation : ", circuit, " | Script not configured yet to manage triple substation circuit relation")

    print("  -- Differentiate Power line with power circuit")
    if len(all_new_lines) > 0:
        gdf_new_lines = gpd.GeoDataFrame(all_new_lines, geometry="geometry")
        list_circuit = gdf_new_lines["osmid"].unique().tolist()

        for circuit_osmid in list_circuit:
            tdf = df_circ[(df_circ["osmid"]==circuit_osmid)&(df_circ["member_role"]=="section")]
            if len(tdf)==0:
                add_error(errors, {"name": "CircuitWithoutSection",
                                   "description": f"Circuit without section",
                                   "osmid": circuit_osmid, "objecttype": "relation"})
                continue
            nb_circuits = int(tdf.iloc[0]["circuits"])
            nb_cables = int(tdf.iloc[0]["cables"])
            list_member_id = set(tdf["member_osmid"].unique().tolist())
            # :todo: check if member exist in circuit
            gdf_lines["circuits"] = np.where(gdf_lines["osmid"].isin(list_member_id),
                                             gdf_lines["circuits"]-nb_circuits, gdf_lines["circuits"])
            gdf_lines["cables"] = np.where(gdf_lines["osmid"].isin(list_member_id),
                                             gdf_lines["cables"]-nb_cables, gdf_lines["cables"])

        check_df = gdf_lines[(gdf_lines["circuits"]<0)|(gdf_lines["cables"]<0)]
        for row in check_df.to_dict(orient='records'):
            if LOG_LEVEL in ["DEBUG"]:
                add_error(errors, {"name": "MoreCircuitRelationThanAttribute",
                                   "description": f"Excessing number of circuits relation compared to circuits attribute",
                                   "osmid": row["osmid"]})

        gdf_old_lines = gdf_lines[gdf_lines["circuits"]>0].copy()

        gdf_final_power_lines = gpd.GeoDataFrame(pd.concat([pd.DataFrame(gdf_old_lines), pd.DataFrame(gdf_new_lines)]), geometry="geometry", crs=3857)
    else:
        gdf_final_power_lines = gdf_lines

    gdf_final_power_lines.to_file(DATA_PATH / COUNTRY_CODE / "pre_graph_power_lines_circuit.gpkg")
    errors_to_file(errors, COUNTRY_CODE, "errors_step2o_manage_circuit.json")


if __name__ == '__main__':
    main()


