import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, LineString
import ast

## SETTINGS
import config
COUNTRY_CODE = config.COUNTRY_CODE
DATA_PATH = config.DATA_PATH
BUFFER_DISTANCE = config.BUFFER_DISTANCE

def main():
    statistics = {}

    # ------------ Prepare power tower transition
    gdf_tower = gpd.read_file(DATA_PATH / COUNTRY_CODE / "osm_brut_power_tower_transition.gpkg").to_crs(epsg=3857)
    statistics["nb_power_tower"] = len(gdf_tower[gdf_tower["power"] == "tower"])
    print("  -- Info : Number of power towers =", statistics["nb_power_tower"])

    ## Keeping only transition node (line_management not null or power=connection)
    gdf_tower = gdf_tower[(gdf_tower["line_management"].notnull()) | (gdf_tower["power"] == "connection")]
    gdf_tower = gdf_tower[(gdf_tower["line_management"] != "transpose") & (gdf_tower["power"] != "connection")]
    gdf_tower["line_management"] = np.where(gdf_tower["power"].notnull(),
                                            gdf_tower["line_management"].astype(str) + ";connection",
                                            gdf_tower["line_management"])
    gdf_tower["line_management"] = gdf_tower["line_management"].str.replace("None;", "")
    set_transition_nodes = set(gdf_tower["id"].unique().tolist())
    statistics["nb_transition_node"] = len(set_transition_nodes)
    print("  -- Info : Number of transition power nodes =", statistics["nb_transition_node"])

    # ------------- Prepare power line dataset
    gdf_line = gpd.read_file(DATA_PATH / COUNTRY_CODE / "osm_brut_power_line.gpkg").to_crs(epsg=3857)
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
    if len(temp):
        print("  /!\\ Error of type for following objects : ", list(temp["osmid"]))
    gdf_line = gdf_line[gdf_line["geom_type"] == "LineString"]
    # gdf_line = gdf_line[gdf_line["@numid"]<1_355_000_000] # keep only lines mapped before jan 2025

    ## Check consistency of start and end points for power lines
    for row in gdf_line.to_dict(orient='records'):
        try:
            LineString([row["geometry"].coords[0], row["geometry"].coords[-1]])
        except NotImplementedError as e:
            print("* ERROR UNKNOWN > with item =", row)
            raise e

    # Checking if 'line_management' is not an end node
    all_nodes_without_end_set = set(sum(gdf_line["nodes_without_end"], []))
    for nid in list(set_transition_nodes & all_nodes_without_end_set):
        print(
            f"* ERROR TOPOLOGY > This 'line_management' node might be an end node (except if power=connection, or line_management=cross): https://openstreetmap.org/node/{nid}")

    # Checking branch connected line
    all_nodes_end_set = set(sum(gdf_line["nodes_end"], []))
    gdf_line["error_branch_connected"] = gdf_line.apply(lambda line: list(set(line["nodes_without_end"]) & all_nodes_end_set), axis=1)
    temp = gdf_line[gdf_line["error_branch_connected"].apply(lambda x: x != [])]
    for row in temp.to_dict(orient='records'):
        for mynode in row["error_branch_connected"]:
            print("* ERROR INTERMEDIATE CONNECTION > https://openstreetmap.org/" + str(row["osmid"]) +
                  " is connected in the middle through the node https://openstreetmap.org/node/" + str(mynode))
    branch_nodes_error_set = set(sum(gdf_line["error_branch_connected"], []))

    # Cut line on node_transition
    for mynode in (set_transition_nodes | branch_nodes_error_set):
        #print("  -- Info : Cut on ", mynode)
        temp = gdf_line[gdf_line["nodes_without_end"].apply(lambda x: mynode in x)]
        listremove_index = set()
        listadding_row = []
        for key, row in temp.to_dict(orient='index').items():
            #print("Need split on index=", key, " & row=", row)
            i = index_of_node(row["nodes"], mynode)
            #print(" > on index=", i)
            splitrows = split_linestring_at_point(row, i)
            listadding_row.extend(splitrows)
            listremove_index.add(key)

        # for key in listremove_index:
        gdf_line = gdf_line.drop(listremove_index)
        extend_df_line = pd.DataFrame(listadding_row)
        gdf_line = gpd.GeoDataFrame(pd.concat([pd.DataFrame(gdf_line), extend_df_line]), geometry="geometry").set_crs(
            epsg=3857)
        gdf_line = gdf_line.reset_index(drop=True)

    # Simplify geometry
    gdf_line["geometry"] = gdf_line.apply(lambda x: simplify_line(x), axis=1)
    for i in range(2):
        gdf_line[f"p{i}"] = gdf_line["geometry"].apply(lambda x: Point(x.coords[i]))
        gdf_line[f"node{i}"] = gdf_line["nodes_end"].apply(lambda x: x[i])
        gdf_line[f"transition{i}"] = gdf_line[f"node{i}"].apply(lambda x: x in set_transition_nodes)



    # Ex: 1234567 --> POINT(12.34 52.25)
    """dic_line_geopoint = {}
    for i in range(2):
        dic_line_geopoint = {**dic_line_geopoint,
                             **{r[f"node{i}"]: r[f"p{i}"] for r in gdf_line.to_dict(orient="records")}}"""

    ### Prepare substation dataset
    gdf_sub = gpd.read_file(DATA_PATH / COUNTRY_CODE / "osm_clean_power_substation.gpkg").to_crs(epsg=3857)
    gdf_sub["centroid"] = gdf_sub["geometry"].centroid
    gdf_sub["geometry"] = gdf_sub["geometry"].buffer(distance=BUFFER_DISTANCE)

    # Ex: way/1234567 --> POINT(12.34 52.25)
    dic_substation_geopoint = {r["osmid"]: r["centroid"] for r in gdf_sub.to_dict(orient="records")}

    ## Spatial join ends of lines with substations
    gdf_country_shape = gpd.read_file(DATA_PATH / COUNTRY_CODE / "osm_brut_country_shape.gpkg").to_crs(epsg=3857)

    # Proximity analysis from end node line to substation
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
    print("DICT LINERES = ", dic_node_to_sub)

    for i in [1, 0]:
        gdf_line[f"substation{i}"] = gdf_line[f"node{i}"].apply(lambda x: dic_node_to_sub.get(x))

    # Identify International end node
    gdfprox_clip = gdf_all_end_nodes.clip(gdf_country_shape).copy()
    set_inside_country = set(gdfprox_clip[f"node"].tolist())
    gdf_spec_nodes_international = gdf_all_end_nodes[~(gdf_all_end_nodes[f"node"]).isin(set_inside_country)].copy()
    gdf_spec_nodes_international["grid_role"] = "international"
    gdf_spec_nodes_international["id"] = gdf_spec_nodes_international["node"]
    gdf_spec_nodes_international["osmid"] = "node/" + gdf_spec_nodes_international["id"].astype(str)

    set_international_nodes = set(gdf_spec_nodes_international["id"].tolist())
    #print("SET INTERNATIONAL NODES = ", set_international_nodes)

    """for i in [1, 0]:
        dftemp = gdf_line.copy()

        dftemp["geometry"] = dftemp[f"p{i}"]
        #dftemp = dftemp.sjoin(gdf_sub, how='left').fillna("")
        dftemp =  dftemp.sjoin_nearest(gdf_sub, how='left', distance_col='distance')
        dftemp = dftemp[dftemp["distance"]<BUFFER_DISTANCE]
        print("DF ANALYSIS")
        print(dftemp.iloc[0])
        dic_lineres = {k["osmid_left"]: k["osmid_right"] for k in dftemp.to_dict(orient='records')}
        gdf_line[f"substation{i}"] = gdf_line["osmid"].apply(lambda x: dic_lineres[x])

        # Identify International end node
        dftempbis = dftemp.clip(gdf_country_shape).copy()
        set_inside_country = set(dftempbis[f"node{i}"].unique().tolist())
        dftemp = dftemp[~(dftemp[f"node{i}"]).isin(set_inside_country)]
        dic_international_nodes = {**dic_international_nodes,
                                   **{r[f"node{i}"]: r["geometry"]
                                      for r in dftemp.to_dict(orient='records')}}"""


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
    gdf_spec_nodes_to_international = gpd.GeoDataFrame(mylist_of_to_international_node, geometry="geometry", crs=3857)

    ## List node linked to line_management
    gdf_spec_nodes_line_management = gdf_tower.copy()
    gdf_spec_nodes_line_management["grid_role"] = "line_management=" + gdf_spec_nodes_line_management["line_management"]

    ## List node made from substation
    gdf_spec_nodes_substation = gdf_sub.copy()
    gdf_spec_nodes_substation["grid_role"] = "substation"
    gdf_spec_nodes_substation["geometry"] = gdf_spec_nodes_substation["centroid"]
    del gdf_spec_nodes_substation["centroid"]

    set_lambda_node = set()
    gdf_line = gdf_line.fillna("")
    print("GDF_LINE =")
    print(gdf_line)
    print(gdf_line.iloc[0])
    for i in [1, 0]:
        gdf_line[f"nodetype{i}"] = "lambda_node"
        gdf_line[f"osmid{i}"] = "node/" + gdf_line[f"node{i}"].astype(str)

        ## Process substation
        gdf_line[f"nodetype{i}"] = gdf_line.apply(
            lambda r: "substation" if r[f"substation{i}"] != "" else r[f"nodetype{i}"], axis=1)
        gdf_line[f"p{i}"] = gdf_line.apply(
            lambda r: dic_substation_geopoint.get(r[f"substation{i}"]) if r[f"substation{i}"] != "" else r[f"p{i}"], axis=1)
        gdf_line[f"osmid{i}"] = gdf_line.apply(
            lambda r: r[f"substation{i}"] if r[f"substation{i}"] != "" else r[f"osmid{i}"], axis=1)

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

    gdf_spec_nodes_lambda = gdf_all_end_nodes.copy()
    gdf_spec_nodes_lambda["grid_role"] = "lambda_node"
    gdf_spec_nodes_lambda["id"] = gdf_spec_nodes_lambda["node"]
    gdf_spec_nodes_lambda["osmid"] = "node/" + gdf_spec_nodes_lambda["id"].astype(str)
    gdf_spec_nodes_lambda = gdf_spec_nodes_lambda[gdf_spec_nodes_lambda["id"].isin(set_lambda_node)]
    del gdf_spec_nodes_lambda["node"]

    df_graph_nodes = pd.concat([gdf_spec_nodes_lambda, gdf_spec_nodes_substation, gdf_spec_nodes_line_management,
                                gdf_spec_nodes_international, gdf_spec_nodes_to_international])


    """copy_gdf_line = []

    for i in range(2):
        dftemp = gdf_line.copy()
        if len(dftemp):
            dftemp = dftemp[~dftemp[f"node{i}"].isin(dic_international_nodes)]
            # List of nodes that are neither substation nor trasnition
            dftemp = dftemp[dftemp[f"substation{i}"] == ""]
            dftemp = dftemp[~dftemp[f"transition{i}"]]
            dftemp["geometry"] = dftemp[f"p{i}"]
            dftemp["grid_role"] = "lambda_node"
            dftemp["osmid"] = "node/" + gdf_line[f"node{i}"].map(str)
            copy_gdf_line.append(dftemp)

    if len(dic_international_nodes) > 0:
        dftemp = pd.DataFrame(
            [{"osmid": "node/" + str(key), "geometry": val, "grid_role": "international"} for key, val in
             dic_international_nodes.items()])
        gdf_international = gpd.GeoDataFrame(dftemp, geometry="geometry", crs=3857)
        df_graph_nodes = pd.concat(copy_gdf_line + [copy_gdf_transition, gdf_spec_nodes_substation, gdf_international])
    else:
        df_graph_nodes = pd.concat(copy_gdf_line + [copy_gdf_transition, gdf_spec_nodes_substation])"""

    for i in range(2):
        for key in [f"p{i}", f"substation{i}", f"node{i}", f"transition{i}"]:
            if key in df_graph_nodes.columns:
                del df_graph_nodes[key]

    for key in ["nodes", 'circuits', 'cables', 'voltage', 'distance', 'index_right']:
        if key in df_graph_nodes.columns:
            del df_graph_nodes[key]

    print("  -- Info : International nodes = ", set_international_nodes)

    """gdf_line["international"] = ""
    set_international_inside_country_nodes = set()
    if len(gdf_line):
        for i in range(2):
            gdf_line[f"p{i}"] = np.where(gdf_line[f"substation{i}"] != "",
                                         gdf_line[f"substation{i}"].apply(lambda x: dic_substation_geopoint.get(x)),
                                         gdf_line[f"p{i}"])
            gdf_line[f"osmid_node{i}"] = np.where(gdf_line[f"substation{i}"] != "",
                                                  gdf_line[f"substation{i}"],
                                                  "node/" + gdf_line[f"node{i}"].map(str))
            gdf_line["international"] = np.where(gdf_line[f"node{i}"].isin(dic_international_nodes),
                                                 f"node{i}",
                                                 gdf_line["international"])
        for row in gdf_line.to_dict(orient='records'):
            try:
                LineString([row["p0"], row["p1"]])
            except Exception:
                print(" * ERROR LINESTRING-BUILD with", row)
        gdf_line["geometry"] = gdf_line.apply(lambda r: LineString([r["p0"], r["p1"]]), axis=1)

        gdf_line_international = gdf_line[gdf_line["international"] != ""].copy()
        set_international_inside_country_nodes = set(list(gdf_line_international["osmid_node0"])) | set(
            list(gdf_line_international["osmid_node1"]))

    # Set lambda_node connected to international line as international_in node
    df_graph_nodes["grid_role"] = np.where((df_graph_nodes["grid_role"] == "lambda_node") &
                                           df_graph_nodes["osmid"].isin(set_international_inside_country_nodes),
                                           "to_international",
                                           df_graph_nodes["grid_role"])"""
    if len(gdf_line):
        for row in gdf_line.to_dict(orient='records'):
            try:
                LineString([row["p0"], row["p1"]])
            except Exception:
                print(" * ERROR LINESTRING-BUILD with", row)
        gdf_line["geometry"] = gdf_line.apply(lambda r: LineString([r["p0"], r["p1"]]), axis=1)

    gdf_graph_nodes = gpd.GeoDataFrame(df_graph_nodes, geometry="geometry", crs=3857)
    print("GRAPH node =")
    print(gdf_graph_nodes)
    print(gdf_graph_nodes.iloc[0])
    gdf_graph_nodes.to_file(DATA_PATH / COUNTRY_CODE / "pre_graph_power_nodes.gpkg")

    ## This line remove errors, but theses errors should be seen and corrected
    if len(gdf_line) == 0:
        gdf_line = gpd.GeoDataFrame({key: [] for key in gdf_line.columns}, geometry="geometry", crs=3857)
        print("  /!\\ Lines-GeoDataFrame is empty")
    else:
        del gdf_line["p0"]
        del gdf_line["p1"]

    gdf_line.to_file(DATA_PATH / COUNTRY_CODE / "pre_graph_power_lines.gpkg")

"""def has_branch_connection(nodes_set, row):
    for i in range(2):
        if row["nodes_end"][i] in nodes_set:
            print("* ERROR INTERMEDIATE CONNECTION > https://openstreetmap.org/" + str(row["osmid"]) +
                  " is connected in the middle through the node https://openstreetmap.org/node/" + str(
                row["nodes_end"][i]))
            return True
    return False"""


def simplify_line(row):
    try:
        return LineString([row["geometry"].coords[0], row["geometry"].coords[-1]])
    except IndexError:
        print(" * ERROR SIMPLIFYING > with row =", row)

def index_of_node(osmid_nodelist, osmid_node):
  try:
    return osmid_nodelist.index(osmid_node)
  except ValueError:
    return -1


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

    # Remplacer la ligne par les deux nouvelles
    #new_gdf = gdf.drop(index)
    #new_gdf = gdf.iloc[:0].append(new_gdf, ignore_index=True)  # reset type
    #new_gdf = new_gdf.append(gdf.drop(index), ignore_index=True)

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

if __name__ == "__main__":
    main()
