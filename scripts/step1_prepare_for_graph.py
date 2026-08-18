
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, LineString
import ast

from utils.utils_gpd import to_empty_file
from utils.utils_exec import add_error, errors_to_file
from utils.utils_data import convert_int

## SETTINGS
import config
COUNTRY_CODE = config.COUNTRY_CODE
DATA_PATH = config.DATA_PATH
BUFFER_DISTANCE = config.BUFFER_DISTANCE
LOG_LEVEL = config.LOG_LEVEL

errors = []

FILENAME_INPUT_COUNTRY_SHAPE = "osm_brut_country_shape.gpkg"
if config.SOURCE == "overpass":
    FILENAME_INPUT_POWER_NODES = "osm_brut_power_tower_transition.gpkg"
    FILENAME_INPUT_POWER_LINES = "osm_brut_power_line.gpkg"
    FILENAME_INPUT_POWER_SUBSTATIONS = "osm_clean_power_substation.gpkg"
elif config.SOURCE == "podoma":
    FILENAME_INPUT_POWER_NODES = "osm_pdm_power_nodes.gpkg"
    FILENAME_INPUT_POWER_LINES = "osm_pdm_power_lines.gpkg"
    FILENAME_INPUT_POWER_SUBSTATIONS = "osm_pdm_power_substations.gpkg"
else:
    raise ValueError(f"Unknown source : {config.SOURCE}")


def main():
    statistics = {}

    # ------------ Prepare power tower transition
    gdf_all_tower = gpd.read_file(DATA_PATH / COUNTRY_CODE / FILENAME_INPUT_POWER_NODES).to_crs(epsg=3857)
    statistics["nb_power_tower"] = len(gdf_all_tower[gdf_all_tower["power"] == "tower"])
    print("  -- Info : Number of nodes / power towers=", len(gdf_all_tower), "/", statistics["nb_power_tower"])

    if len(gdf_all_tower) == 0:
        to_empty_file(DATA_PATH / COUNTRY_CODE / "pre_graph_power_nodes.gpkg")
        to_empty_file(DATA_PATH / COUNTRY_CODE / "pre_graph_power_lines.gpkg")
        return

    ## Keeping only transition node (line_management not null or power=connection)
    gdf_tower = gdf_all_tower[(gdf_all_tower["line_management"].notnull()) | (gdf_all_tower["power"] == "connection")]
    gdf_tower = gdf_tower[(gdf_tower["line_management"] != "transpose") & (gdf_tower["power"] != "connection")]
    gdf_tower["line_management"] = np.where(gdf_tower["power"] == "connection",
                                            gdf_tower["line_management"].apply(lambda x: x + ";" if x is not None else "") + "connection",
                                            gdf_tower["line_management"])
    gdf_tower["line_management"] = gdf_tower["line_management"].str.replace("None;", "")
    # crossing management
    set_crossing_node = set(gdf_tower[gdf_tower["line_management"] == "cross"]["id"].tolist())
    gdf_tower = gdf_tower[gdf_tower["line_management"] != "cross"]
    gdf_tower = gdf_tower[gdf_tower["line_management"] != "straight"]
    gdf_tower = gdf_tower[gdf_tower["line_management"] != "transpose"]

    set_transition_nodes = set(gdf_tower["id"].unique().tolist())
    statistics["nb_transition_node"] = len(set_transition_nodes)
    print("  -- Info : Number of transition power nodes =", statistics["nb_transition_node"])

    # ------------- Prepare power line dataset
    gdf_line = gpd.read_file(DATA_PATH / COUNTRY_CODE / FILENAME_INPUT_POWER_LINES).to_crs(epsg=3857)
    if len(gdf_line) == 0:
        to_empty_file(DATA_PATH / COUNTRY_CODE / "pre_graph_power_nodes.gpkg")
        to_empty_file(DATA_PATH / COUNTRY_CODE / "pre_graph_power_lines.gpkg")
        return

    gdf_line["geom_type"] = gdf_line["geometry"].apply(lambda x: x.geom_type)
    gdf_line["nodes"] = gdf_line["nodes"].apply(lambda x: ast.literal_eval(x))
    gdf_line["nodes_end"] = gdf_line["nodes"].apply(lambda x: [x[0], x[-1]])
    gdf_line["nodes_without_end"] = gdf_line["nodes"].apply(lambda x: x[1:-1])
    statistics["nb_power_line"] = len(gdf_line)
    print("  -- Info : Number of power lines =", statistics["nb_power_line"])

    ## Checking geom_type for lines
    print("  -- Info : Types of power line (only LineString should be there) =",
          gdf_line["geom_type"].unique().tolist())
    temp = gdf_line[gdf_line["geom_type"] != "LineString"]
    for row in temp.to_dict(orient="records"):
        add_error(errors, {"name":"IncorrectLineType",
                           "description":"Incorrect Object Type for Power Line (LineString expected)",
                           "details":str(type(row["geometry"])), "osmid":row["osmid"], "level":3})
    gdf_line = gdf_line[gdf_line["geom_type"] == "LineString"]
    # gdf_line = gdf_line[gdf_line["@numid"]<1_355_000_000] # keep only lines mapped before jan 2025

    # Giving default value to circuit and cables
    # --------- Manage and check "circuit" tag as int --------------------
    gdf_line["circuits_int"] = gdf_line["circuits"].apply(lambda x: convert_int(x, default=1))
    temp_circuits_problem = gdf_line[gdf_line["circuits"] == -1]
    for row in temp_circuits_problem.to_dict(orient='records'):
        add_error(errors, {"name": "CircuitsNumber",
                           "description": f"Incorrect circuit number [{row['circuits']}]",
                           "osmid": row["osmid"].split("*")[0]})
    gdf_line["circuits"] = np.where(gdf_line["circuits_int"] == -1,
                                     1, gdf_line["circuits_int"])
    del gdf_line["circuits_int"]

    # --------- Manage and check "cables" tag as int --------------------
    gdf_line["cables_int"] = gdf_line["cables"].apply(lambda x: convert_int(x, default=3))
    temp_cables_problem = gdf_line[gdf_line["cables_int"] == -1]
    for row in temp_cables_problem.to_dict(orient='records'):
        add_error(errors, {"name": "CablesNumber",
                           "description": f"Incorrect cables number [{row['cables']}]",
                           "osmid": row["osmid"].split("*")[0]})
    gdf_line["cables"] = np.where(gdf_line["cables_int"] == -1,
                                   3, gdf_line["cables_int"])
    del gdf_line["cables_int"]

    ## Remove node corresponding to crossing point to avoid connectivity
    gdf_line["crossing"] = gdf_line["nodes_without_end"].apply(lambda x: len(set(x) & set_crossing_node))
    gdf_cross = gdf_line[gdf_line["crossing"]>0]
    myrowlist = []
    for row in gdf_cross.to_dict(orient='records'):
        myrow = row.copy()
        for node in row["nodes"][1:-1]:
            if node in set_crossing_node:
                delcrossnode = myrow["nodes"].index(node)
                myrow = remove_point_on_linestring(row, delcrossnode)
        myrowlist.append(myrow)

    gdf_without_cross = pd.DataFrame(myrowlist)
    gdf_line = gdf_line[gdf_line["crossing"]==0]
    gdf_line = gpd.GeoDataFrame(pd.concat([gdf_without_cross, gdf_line]), geometry="geometry", crs=3857)
    # to process

    ## Check consistency of start and end points for power lines
    print("  -- Check consistency of start and end points for power lines")
    gdf_line["check_consistency"] = gdf_line["geometry"].map(check_line_consistency)
    tempdf = gdf_line[~gdf_line["check_consistency"]]
    for row in tempdf.to_dict(orient='records'):
        add_error(errors, {"name":"InconsistentGeometry",
                           "description":"Inconsistent Geometry (At least two point expected)",
                           "details":str(row["geometry"]), "osmid":row["osmid"], "level":3})
    gdf_line = gdf_line[gdf_line["check_consistency"]]

    # Identify self-looping lines
    print("  -- Identify self-looping lines")
    gdf_line["len_list_node"] = gdf_line["nodes"].map(len)
    gdf_line["len_set_node"] = gdf_line["nodes"].apply(lambda x: len(set(x)))
    tempdf = gdf_line[gdf_line["len_list_node"]!=gdf_line["len_set_node"]]
    for row in tempdf.to_dict(orient='records'):
        if (row["nodes"][0] == row["nodes"][-1]) and (row["len_list_node"]==row["len_set_node"]+1):
            # Case where looping from start to end
            pass
        else:
            pass
        add_error(errors, {"name": "SelfLoopingLine",
                           "description": "The line is looping to itself",
                           "osmid1": row["osmid"], "level":1})
    gdf_line = gdf_line[gdf_line["len_list_node"] == gdf_line["len_set_node"]]

    # Checking if 'line_management' is not an end node
    print("  -- Check if 'line_management' is not an end node")
    gdf_line["set_inbetween_transition_node"] = gdf_line["nodes_without_end"].apply(lambda x: set(x) & set_transition_nodes)
    tempdf = gdf_line[gdf_line["set_inbetween_transition_node"].apply(lambda x: len(x)) > 0]
    for row in tempdf.to_dict(orient='records'):
        for nid in row["set_inbetween_transition_node"]:
            add_error(errors, {"name": "LineManagementNotEndNode",
                           "description": "This 'line_management' node (1) should probably be an end node for power line (2)",
                           "osmid1": f"node/{nid}", "osmid2":row["osmid"], "level":1})

    # Checking branch connected line
    print("  -- Check branch connected line")
    all_nodes_end_set = set(sum(gdf_line["nodes_end"], []))
    gdf_line["error_branch_connected"] = gdf_line.apply(lambda line: list(set(line["nodes_without_end"]) & all_nodes_end_set), axis=1)
    temp = gdf_line[gdf_line["error_branch_connected"].apply(lambda x: x != [])]
    for row in temp.to_dict(orient='records'):
        for mynode in row["error_branch_connected"]:
            add_error(errors, {"name":"ConnectionInBetweenEnds",
                               "description": "Connection of a power line to (1) through the node (2)",
                               "osmid1": f"node/{row['osmid']}", "osmid2": f"node/{mynode}", "level":1})
    branch_nodes_error_set = set(sum(gdf_line["error_branch_connected"], []))

    # Cut line on node_transition
    myset_of_cut_nodes = (set_transition_nodes | branch_nodes_error_set)
    print(f"  -- Cut line on node_transition, {len(myset_of_cut_nodes)} items")

    gdf_line["set_inbetween_cut_node_id"] = gdf_line["nodes_without_end"].apply(
        lambda x: set(x) & myset_of_cut_nodes)
    gdf_line["list_inbetween_cut_node_index"] = gdf_line.apply(
        lambda r: [r["nodes"].index(n) for n in r["set_inbetween_cut_node_id"]], axis=1)
    gdf_line["list_inbetween_cut_node_index"] = gdf_line["list_inbetween_cut_node_index"].apply(lambda x: sorted(x))

    tempdf = gdf_line[gdf_line["list_inbetween_cut_node_index"].apply(lambda x: len(x))>0]

    compilerows = []
    for row in tempdf.to_dict(orient='records'):
        compilerows.extend(split_linestring_at_points(row, row["list_inbetween_cut_node_index"]))
    print(f"  -- Cutting {len(tempdf)} lines into {len(compilerows)} pieces")
    gdf_line = gdf_line[gdf_line["list_inbetween_cut_node_index"].apply(lambda x: len(x)) == 0].copy()
    extend_df_line = pd.DataFrame(compilerows)
    gdf_line = gpd.GeoDataFrame(pd.concat([pd.DataFrame(gdf_line), extend_df_line]), geometry="geometry").set_crs(
        epsg=3857)
    gdf_line = gdf_line.reset_index(drop=True)

    # Simplify geometry
    print("  -- Simplify geometry")
    gdf_line["geometry"] = gdf_line.apply(lambda x: simplify_line(x), axis=1)
    for i in range(2):
        gdf_line[f"p{i}"] = gdf_line["geometry"].apply(lambda x: Point(x.coords[i]))
        gdf_line[f"node{i}"] = gdf_line["nodes_end"].apply(lambda x: x[i])
        gdf_line[f"transition{i}"] = gdf_line[f"node{i}"].apply(lambda x: x in set_transition_nodes)

    ### Prepare substation dataset
    print("  -- Prepare substation dataset")
    gdf_sub = gpd.read_file(DATA_PATH / COUNTRY_CODE / FILENAME_INPUT_POWER_SUBSTATIONS).to_crs(epsg=3857)
    gdf_sub["centroid"] = gdf_sub["geometry"].centroid
    gdf_sub["geometry"] = gdf_sub["geometry"].buffer(distance=BUFFER_DISTANCE)

    ## dic_substation_geopoint : Ex: way/1234567 --> POINT(12.34 52.25)
    dic_substation_geopoint = {r["osmid"]: r["centroid"] for r in gdf_sub.to_dict(orient="records")}

    ## Spatial join ends of lines with substations
    print("  -- Spatial join ends of lines with substations")
    gdf_country_shape = gpd.read_file(DATA_PATH / COUNTRY_CODE / FILENAME_INPUT_COUNTRY_SHAPE).to_crs(epsg=3857)

    # Proximity analysis from end node line to substation
    print("  -- Proximity analysis from end node line to substation")
    gdf_all_end_nodes = [gdf_line.copy(), gdf_line.copy()]
    for i in [1, 0]:
        gdf_all_end_nodes[i]["geometry"] = gdf_all_end_nodes[i][f"p{i}"]
        gdf_all_end_nodes[i]["node"] = gdf_all_end_nodes[i][f"node{i}"]
    gdf_all_end_nodes = gpd.GeoDataFrame(pd.concat(gdf_all_end_nodes), geometry="geometry", crs=3857)
    lstcol = [col for col in gdf_all_end_nodes.columns if col not in ["geometry", "node"]]
    for col in lstcol:
        del gdf_all_end_nodes[col]
    gdf_all_end_nodes = gdf_all_end_nodes.sjoin_nearest(gdf_sub, how='left', distance_col='distance')
    del gdf_all_end_nodes["centroid"]

    gdfprox_select = gdf_all_end_nodes[gdf_all_end_nodes["distance"]<BUFFER_DISTANCE]
    dic_node_to_sub = {k["node"]: k["osmid"] for k in gdfprox_select.to_dict(orient='records')}

    for i in [1, 0]:
        gdf_line[f"substation{i}"] = gdf_line[f"node{i}"].apply(lambda x: dic_node_to_sub.get(x))

    # Identify International end node
    print("  -- Identify International end node")
    gdfprox_clip = gdf_all_end_nodes.clip(gdf_country_shape).copy()
    set_inside_country = set(gdfprox_clip[f"node"].tolist())
    gdf_spec_nodes_international = gdf_all_end_nodes[~(gdf_all_end_nodes[f"node"]).isin(set_inside_country)].copy()
    gdf_spec_nodes_international = gdf_spec_nodes_international[["node", "geometry"]]
    gdf_spec_nodes_international["grid_role"] = "international"
    gdf_spec_nodes_international["id"] = gdf_spec_nodes_international["node"]
    gdf_spec_nodes_international["osmid"] = "node/" + gdf_spec_nodes_international["id"].astype(str)

    set_international_nodes = set(gdf_spec_nodes_international["id"].tolist())
    #print("SET INTERNATIONAL NODES = ", set_international_nodes)

    ## Selection of lines that are not within the same substation
    gdf_line = gdf_line[(gdf_line["substation0"] == "") | (gdf_line["substation1"] == "")
                        | (gdf_line["substation0"] != gdf_line["substation1"])]
    ## Exclude international line (crossing country, but both end points at international)
    gdf_line = gdf_line[~(gdf_line["node0"].isin(set_international_nodes)&gdf_line["node1"].isin(set_international_nodes))]


    ## Make to_international for international line, but node end within country
    temp_int = gdf_line[gdf_line["node0"].isin(set_international_nodes) | gdf_line["node1"].isin(set_international_nodes)]
    set_all_int_node = set(temp_int["node0"].tolist() + temp_int["node1"].tolist())
    set_to_international_node = set_all_int_node.difference(set_international_nodes)

    mylist_of_to_international_node = []
    for i in [0, 1]:
        tdf = gdf_line[gdf_line[f"node{i}"].isin(set_to_international_node)]
        for row in tdf.to_dict(orient='records'):
            mylist_of_to_international_node.append(
                {"grid_role": "to_international", "id": row[f"node{i}"], "osmid": f"node/{row[f"node{i}"]}", "geometry":row[f"p{i}"]}
            )
    if mylist_of_to_international_node:
        gdf_spec_nodes_to_international = gpd.GeoDataFrame(mylist_of_to_international_node, geometry="geometry", crs=3857)
    else:
        gdf_spec_nodes_to_international = gpd.GeoDataFrame({"grid_role": [], "id":  [], "osmid":  [], "geometry": []}, geometry="geometry",
                                                           crs=3857)
    gdf_spec_nodes_to_international = gdf_spec_nodes_to_international.merge(gdf_all_tower, how='left', left_on='id', right_on='id', suffixes=(None, "_merged"))
    lstcol = [col for col in gdf_spec_nodes_to_international.columns if col.endswith("_merged")]
    for col in lstcol:
        del gdf_spec_nodes_to_international[col]

    ## List node linked to line_management
    gdf_spec_nodes_line_management = gdf_tower.copy()
    gdf_spec_nodes_line_management["grid_role"] = "line_management=" + gdf_spec_nodes_line_management["line_management"]

    ## List node made from substation
    gdf_spec_nodes_substation = gdf_sub.copy()
    gdf_spec_nodes_substation["grid_role"] = "substation"
    gdf_spec_nodes_substation["geometry"] = gdf_spec_nodes_substation["centroid"]
    del gdf_spec_nodes_substation["centroid"]

    # Manage lambda node
    print("  -- Manage lambda node")
    set_lambda_node = set()
    for i in [1, 0]:
        gdf_line[f"nodetype{i}"] = "lambda_node"
        gdf_line[f"osmid{i}"] = "node/" + gdf_line[f"node{i}"].astype(str)

        ## Process substation
        gdf_line[f"nodetype{i}"] = gdf_line.apply(
            lambda r: "substation" if r[f"substation{i}"] is not None else r[f"nodetype{i}"], axis=1)
        gdf_line[f"p{i}"] = gdf_line.apply(
            lambda r: dic_substation_geopoint.get(r[f"substation{i}"]) if (r[f"substation{i}"] is not None and not pd.isna(r[f"substation{i}"])) else r[f"p{i}"], axis=1)
        gdf_line[f"osmid{i}"] = gdf_line.apply(
            lambda r: r[f"substation{i}"] if (r[f"substation{i}"] is not None and not pd.isna(r[f"substation{i}"])) else r[f"osmid{i}"], axis=1)

        ## Process international
        gdf_line[f"nodetype{i}"] = gdf_line.apply(
            lambda r: "international" if r[f"node{i}"] in set_international_nodes else r[f"nodetype{i}"], axis=1)
        ## Process to_international
        gdf_line[f"nodetype{i}"] = gdf_line.apply(
            lambda r: "to_international" if r[f"node{i}"] in set_to_international_node else r[f"nodetype{i}"], axis=1)
        ## Process line_management
        gdf_line[f"nodetype{i}"] = gdf_line.apply(
            lambda r: "line_management" if r[f"node{i}"] in set_transition_nodes else r[f"nodetype{i}"], axis=1)

        tdf = gdf_line[gdf_line[f"nodetype{i}"]=="lambda_node"].copy()
        set_lambda_node |= set(tdf[f"node{i}"].tolist())

    gdf_line = gdf_line[gdf_line["osmid0"] != gdf_line["osmid1"]]
    gdf_line["international_osmid"] = np.where(
        gdf_line["osmid0"].apply(lambda x: int(x.replace("node/", "")) if x.startswith("node") else x).isin(set_all_int_node),
        gdf_line["osmid0"], None)
    gdf_line["international_osmid"] = np.where(
        gdf_line["osmid1"].apply(lambda x: int(x.replace("node/", "")) if x.startswith("node") else x).isin(set_all_int_node),
        gdf_line["osmid1"], gdf_line["international_osmid"])

    gdf_spec_nodes_lambda = gdf_all_end_nodes.copy()
    gdf_spec_nodes_lambda = gdf_spec_nodes_lambda[["node", "geometry"]]
    gdf_spec_nodes_lambda["grid_role"] = "lambda_node"
    gdf_spec_nodes_lambda["id"] = gdf_spec_nodes_lambda["node"]
    gdf_spec_nodes_lambda["osmid"] = "node/" + gdf_spec_nodes_lambda["id"].astype(str)
    gdf_spec_nodes_lambda = gdf_spec_nodes_lambda[gdf_spec_nodes_lambda["id"].isin(set_lambda_node)]
    del gdf_spec_nodes_lambda["node"]
    gdf_spec_nodes_lambda = gdf_spec_nodes_lambda.merge(gdf_all_tower, how='left', left_on='id', right_on='id', suffixes=(None, "_merged"))
    lstcol = [col for col in gdf_spec_nodes_lambda.columns if col.endswith("_merged")]
    for col in lstcol:
        del gdf_spec_nodes_lambda[col]

    df_graph_nodes = pd.concat([gdf_spec_nodes_lambda, gdf_spec_nodes_substation, gdf_spec_nodes_line_management,
                                gdf_spec_nodes_international, gdf_spec_nodes_to_international])


    for i in range(2):
        for key in [f"p{i}", f"substation{i}", f"node{i}", f"transition{i}"]:
            if key in df_graph_nodes.columns:
                del df_graph_nodes[key]

    for key in ["nodes", 'circuits', 'cables', 'distance', 'index_right']:
        if key in df_graph_nodes.columns:
            del df_graph_nodes[key]

    print("  -- Info : International nodes = ", set_international_nodes)

    if len(gdf_line):
        for row in gdf_line.to_dict(orient='records'):
            try:
                LineString([row["p0"], row["p1"]])
            except Exception:
                add_error(errors, {"name": "LineStringBuild",
                                   "description": "Error when building LineString",
                                   "osmid": row["osmid"], "level":3})
        gdf_line["geometry"] = gdf_line.apply(lambda r: LineString([r["p0"], r["p1"]]), axis=1)

    gdf_graph_nodes = gpd.GeoDataFrame(df_graph_nodes, geometry="geometry", crs=3857)
    gdf_graph_nodes.to_file(DATA_PATH / COUNTRY_CODE / "pre_graph_power_nodes.gpkg")

    ## This line remove errors, but theses errors should be seen and corrected
    if len(gdf_line) == 0:
        gdf_line = gpd.GeoDataFrame({key: [] for key in gdf_line.columns}, geometry="geometry", crs=3857)
        print("  /!\\ Lines-GeoDataFrame is empty")
    else:
        del gdf_line["p0"]
        del gdf_line["p1"]

    gdf_line.to_file(DATA_PATH / COUNTRY_CODE / "pre_graph_power_lines.gpkg")
    errors_to_file(errors, COUNTRY_CODE, "errors_step1_prepare_for_graph.json")


def simplify_line(row):
    try:
        return LineString([row["geometry"].coords[0], row["geometry"].coords[-1]])
    except IndexError:
        add_error(errors, {"name": "SimplifyingLine",
                           "description": "Error when simplifying LineString",
                           "osmid": row["osmid"]})


def index_of_node(osmid_nodelist, osmid_node):
  try:
    return osmid_nodelist.index(osmid_node)
  except ValueError:
    return -1

def check_line_consistency(geom):
    try:
        LineString([geom.coords[0], geom.coords[-1]])
        return True
    except Exception:
        return False

def remove_point_on_linestring(row, i):
    geom = row["geometry"]

    if not isinstance(geom, LineString):
        raise ValueError("Geometry is not a LineString")

    coords = list(geom.coords)
    coords.pop(i)
    line = LineString(coords)

    nodes = row["nodes"]
    nodes.pop(i)

    node_without_ext = nodes[1:i-1] if len(nodes) > 2 else []

    row1 = row.copy()
    row1["geometry"] = line
    row1["nodes"] = nodes
    row1["nodes_without_end"] = node_without_ext
    row1["osmid"] = row1["osmid"]

    return row1

def split_linestring_at_point(row, i):
    #print("Cutting = ", row)
    geom = row["geometry"]

    if not isinstance(geom, LineString):
        raise ValueError("Geometry is not a LineString")

    coords = list(geom.coords)

    # Création des deux nouvelles lignes
    line1 = LineString(coords[:i + 1])
    line2 = LineString(coords[i:])

    nodes1 = row["nodes"][:i + 1]
    nodes2 = row["nodes"][i:]

    node_without_ext1 = nodes1[1:-1] if len(nodes1)>2 else []
    node_without_ext2 = nodes2[1:-1] if len(nodes2)>2 else []

    # On recrée une ligne avec les mêmes attributs (sauf geometry)

    row1 = row.copy()
    row1["geometry"] = line1
    row1["nodes"] = nodes1
    row1["nodes_without_end"] = node_without_ext1
    row1["osmid"] = row1["osmid"] + "*0"
    row2 = row.copy()
    row2["geometry"] = line2
    row2["nodes"] = nodes2
    row2["nodes_without_end"] = node_without_ext2
    row2["osmid"] = row2["osmid"] + "*1"

    return [row1, row2]

def split_linestring_at_points(row, indexes):
    #print("Cutting = ", row)
    geom = row["geometry"]

    if not isinstance(geom, LineString):
        raise ValueError("Geometry is not a LineString")

    coords = list(geom.coords)

    # Création des deux nouvelles lignes
    lines = []
    nodes = []
    node_without_ext = []
    start = 0

    try:
        for j in indexes:
            lines.append(LineString(coords[start:j + 1]))
            nodes.append(row["nodes"][start:j + 1])
            if len(nodes[-1]) < 2:
                print("* ERROR -----------------> ", row)
            node_without_ext.append(nodes[-1][1:-1] if len(nodes[-1])>2 else [])
            start = j
        lines.append(LineString(coords[start:]))
        nodes.append(row["nodes"][start:])
        node_without_ext.append(nodes[-1][1:-1] if len(nodes[-1]) > 2 else [])
    except Exception as e:
        if LOG_LEVEL == "DEBUG":
            print("** ERROR when splitting row :")
            import pprint
            pprint.pp(row)
            print("Split indexes =", indexes)
            raise e

    allrows = []
    for j, (myline, mynodes, mynodesinbetween) in enumerate(zip(lines, nodes, node_without_ext)):
        myrow = row.copy()
        myrow["geometry"] = myline
        myrow["nodes"] = mynodes
        myrow["nodes_without_end"] = mynodesinbetween
        myrow["osmid"] = f"{myrow["osmid"]}*{j}"
        allrows.append(myrow)

    return allrows


if __name__ == "__main__":
    main()
