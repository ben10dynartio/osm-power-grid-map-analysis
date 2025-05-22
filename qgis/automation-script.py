import math
import os

COUNTRY_LIST = {'AE': 'United Arab Emirates', 'AF': 'Afghanistan', 'AM': 'Armenia', 'AZ': 'Azerbaijan', 'BD': 'Bangladesh', 'BH': 'Bahrain', 'BN': 'Brunei', 'BT': 'Bhutan', 'ID': 'Indonesia', 'IL': 'Israel', 'IQ': 'Iraq', 'IR': 'Iran', 'JO': 'Jordan', 'JP': 'Japan', 'KG': 'Kyrgyzstan', 'KH': 'Cambodia', 'KP': 'North Korea', 'KR': 'South Korea', 'KW': 'Kuwait', 'KZ': 'Kazakhstan', 'LA': 'Laos', 'LB': 'Lebanon', 'LK': 'Sri Lanka', 'MM': 'Myanmar', 'MN': 'Mongolia', 'MV': 'Maldives', 'MY': 'Malaysia', 'NP': 'Nepal', 'OM': 'Oman', 'PH': 'Philippines', 'PK': 'Pakistan', 'PS': 'State of Palestine', 'QA': 'Qatar', 'SA': 'Saudi Arabia', 'SG': 'Singapore', 'SY': 'Syria', 'TH': 'Thailand', 'TJ': 'Tajikistan', 'TL': 'Timor-Leste', 'TM': 'Turkmenistan', 'TR': 'Turkey', 'TW': 'Taiwan', 'UZ': 'Uzbekistan', 'VN': 'Vietnam', 'YE': 'Yemen'}

STYLE_REF_COUNTRY_CODE = "BO" # do not change
DATA_FOLDER = Path(__file__).parent.parent / "data"
EXPORT_FOLDER = Path(__file__).parent.parent / "export"
QGIS_FOLDER = Path(__file__).parent

DATA_LAYERS = ['osm_brut_country_shape', 'post_graph_power_lines', 
'osm_brut_power_line', 'osm_brut_power_tower_transition', 
'pre_graph_power_nodes', 'post_graph_power_nodes', ] # do not change

#### -----------------------
ProjectInstance = QgsProject.instance()
qgs_treeroot = ProjectInstance.layerTreeRoot()
ggs_layoutmanager = ProjectInstance.layoutManager()


def add_layer_group(groupe_name):
    root = ProjectInstance.layerTreeRoot()
    group = root.insertGroup(0, groupe_name)


def get_layer(name, countrycode):
    layers = ProjectInstance.mapLayersByName(name)
    for layer in layers:
        pathsource = layer.source()
        pathsource = pathsource.split("|")[0]
        pathsource = pathsource.replace(f"/{name}.gpkg", "")
        if countrycode == pathsource[-2:]:
            return layer


def move_layer(layer, group_name):
    myLayer = qgs_treeroot.findLayer(layer.id())
    myClone = myLayer.clone()
    parent = myLayer.parent()
    myGroup = qgs_treeroot.findGroup(group_name)
    # Insert in first position
    myGroup.insertChildNode(0, myClone)
    parent.removeChildNode(myLayer)


def duplicate_layer_style(from_layer, to_layer):
    iface.setActiveLayer(from_layer)
    iface.actionCopyLayerStyle().trigger()
    iface.setActiveLayer(to_layer)
    iface.actionPasteLayerStyle().trigger()


def create_country_group(country_code, country_name):
    GROUP_NAME = f"{country_code} - {country_name}" # do not change
    if qgs_treeroot.findGroup(GROUP_NAME) is None:
        print("-- Group creation and data import")
        add_layer_group(GROUP_NAME)
        
        for layer_name in DATA_LAYERS:
            path = DATA_FOLDER / f"{COUNTRY_CODE}/{layer_name}.gpkg"
            if not os.path.isfile(path):
                print(f"-- File '{path}' not found")
                raise FileNotFoundError
            layer = QgsVectorLayer(str(path), layer_name, "ogr")
            ProjectInstance.addMapLayer(layer)
            print(f"-- Import File '{path}'")

        for layer_name in DATA_LAYERS:
            layer = get_layer(layer_name, COUNTRY_CODE)
            move_layer(layer, GROUP_NAME)
            
        ### Begin - Duplicate style
        for layername in DATA_LAYERS:
            ref_layer = get_layer(layername, STYLE_REF_COUNTRY_CODE)
            dest_layer = get_layer(layername, COUNTRY_CODE)
            duplicate_layer_style(ref_layer, dest_layer)
        ### End - Duplicate style
        
    else:
        print("-- Group already exist, no import")
        
def set_map_bounding_box(country_code):
    
    country_layer = get_layer('osm_brut_country_shape', country_code)
    country_layer.selectAll()
    feature = country_layer.selectedFeatures()[0]
    country_layer.removeSelection()

    source_crs = QgsCoordinateReferenceSystem(4326)
    dest_crs = QgsCoordinateReferenceSystem(3857)
    transform = QgsCoordinateTransform(source_crs, dest_crs, ProjectInstance)
    new_box = transform.transformBoundingBox(feature.geometry().boundingBox())

    xmax, xmin = new_box.xMaximum(), new_box.xMinimum()
    deltax = xmax-xmin
    xmax, xmin = xmax + 0.05*deltax, xmin - 0.05*deltax

    ymax, ymin = new_box.yMaximum(), new_box.yMinimum()
    deltay = ymax-ymin
    ymax, ymin = ymax + 0.05*deltay, ymin - 0.05*deltay

    QgsExpressionContextUtils.setProjectVariable(ProjectInstance, 'xMaximum', xmax)
    QgsExpressionContextUtils.setProjectVariable(ProjectInstance, 'xMinimum', xmin)
    QgsExpressionContextUtils.setProjectVariable(ProjectInstance, 'yMaximum', ymax)
    QgsExpressionContextUtils.setProjectVariable(ProjectInstance, 'yMinimum', ymin)
    
    # Compute scalebar Dimensions
    scalebar_size = max(deltay, deltax) * 65 / 180000 #nb of km available for scale bar
    scalebar_base = 10**math.trunc(math.log10(scalebar_size))
    scalebar_ratio = scalebar_size / scalebar_base
    if (1 <= scalebar_ratio) and (scalebar_ratio < 1.5):
        scalebar_unit_length = 25
        scalebar_nb_length = 4
    elif (1.5 <= scalebar_ratio) and (scalebar_ratio < 2):
        scalebar_unit_length = 50
        scalebar_nb_length = 3
    elif (2 <= scalebar_ratio) and (scalebar_ratio < 3):
        scalebar_unit_length = 50
        scalebar_nb_length = 4
    elif (3 <= scalebar_ratio) and (scalebar_ratio < 4):
        scalebar_unit_length = 100
        scalebar_nb_length = 3
    elif (4 <= scalebar_ratio) and (scalebar_ratio < 6):
        scalebar_unit_length = 100
        scalebar_nb_length = 4
    elif (6 <= scalebar_ratio) and (scalebar_ratio < 8):
        scalebar_unit_length = 200
        scalebar_nb_length = 3
    elif (8 <= scalebar_ratio) and (scalebar_ratio < 10):
        scalebar_unit_length = 200
        scalebar_nb_length = 4
        
    #print(f"{scalebar_size=}, {scalebar_base=}, {scalebar_ratio=}, {scalebar_nb_length=}")
    QgsExpressionContextUtils.setProjectVariable(ProjectInstance, 'scalebar_unit_length', scalebar_unit_length*scalebar_base/100)
    QgsExpressionContextUtils.setProjectVariable(ProjectInstance, 'scalebar_nb_length', str(scalebar_nb_length))


def show_layer(layer, is_shown):
    if layer == "all":
        layers = ProjectInstance.mapLayers().values()
        for layer in layers:
            node = ProjectInstance.layerTreeRoot().findLayer(layer)
            if node:
                node.setItemVisibilityChecked(is_shown)
    else:
        node = ProjectInstance.layerTreeRoot().findLayer(layer)
        if node:
            node.setItemVisibilityChecked(is_shown)


def show_grid_connectivity_layers():
    listlayers = ['osm_brut_country_shape', 'post_graph_power_nodes', 'post_graph_power_lines']
    for layername in listlayers:
        show_layer(get_layer(layername, COUNTRY_CODE), True)
        
def show_network_layers():
    listlayers = ['osm_brut_country_shape', 'pre_graph_power_nodes',
    'osm_brut_power_tower_transition', 'osm_brut_power_line']
    for layername in listlayers:
        show_layer(get_layer(layername, COUNTRY_CODE), True)
    layerosm = ProjectInstance.mapLayersByName("OpenStreetMap")[0]
    show_layer(layerosm, True)


def visibility_and_export(country_code, map_style):
    sourcelayout = ggs_layoutmanager.layoutByName('Automatized')
    graph_legend = sourcelayout.itemById('Legend:Grid connectivity')
    map_legend = sourcelayout.itemById('Legend:High-Voltage Network')
    show_layer("all", False)
    if map_style =="graph":
        show_grid_connectivity_layers()
        graph_legend.setVisibility(True)
        map_legend.setVisibility(False)
        filename = "grid-connectivity.png"
    elif map_style =="map":
        show_network_layers()
        graph_legend.setVisibility(False)
        map_legend.setVisibility(True)
        filename = "high-voltage-network.png"
    else:
        raise ValueError("Unknown map style = " + str(map_style))

    sourcelayout.refresh()

    exporter = QgsLayoutExporter(sourcelayout)
    export_settings = QgsLayoutExporter.ImageExportSettings()
    export_settings.dpi = 200
    exporter.exportToImage(str(EXPORT_FOLDER / f"{country_code}/{filename}"), 
    export_settings)

# Change working directory
os.chdir(QGIS_FOLDER)
print("Working directory =", os.getcwd(), " / data_path =", DATA_FOLDER)
for COUNTRY_CODE, COUNTRY_NAME in COUNTRY_LIST.items():
    print(f"> Starting execution for {COUNTRY_NAME} ({COUNTRY_CODE})")
    try:
        QgsExpressionContextUtils.setProjectVariable(ProjectInstance, 'country_name', COUNTRY_NAME)
        create_country_group(COUNTRY_CODE, COUNTRY_NAME)
        set_map_bounding_box(COUNTRY_CODE)
        for my_map_style in ["graph", "map"]:
            visibility_and_export(COUNTRY_CODE, my_map_style)
        print(f"> End {COUNTRY_CODE}\n")
    except FileNotFoundError as e:
        print(f"Error with {COUNTRY_NAME} ({COUNTRY_CODE}) =>", e)
