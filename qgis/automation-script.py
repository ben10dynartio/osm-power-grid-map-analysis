COUNTRY_LIST = {
"NP":"Nepal",
"TZ":"Tanzania",
}

STYLE_REF_COUNTRY_CODE = "BO" # do not change

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
    myGroup = root.findGroup(group_name)
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
        QgsExpressionContextUtils.setProjectVariable(ProjectInstance, 'country_name', COUNTRY_NAME)

        for layer_name in DATA_LAYERS:
            path = f"data/{COUNTRY_CODE}/{layer_name}.gpkg"
            layer = QgsVectorLayer(path, layer_name, "ogr")
            ProjectInstance.addMapLayer(layer)

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
    sourcelayout = ggs_layoutmanager.layoutByName('Automation')
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
    exporter.exportToImage(f"export/{country_code}/{filename}", 
    export_settings)

for COUNTRY_CODE, COUNTRY_NAME in COUNTRY_LIST.items():
    create_country_group(COUNTRY_CODE, COUNTRY_NAME)
    set_map_bounding_box(COUNTRY_CODE)
    for my_map_style in ["graph", "map"]:
        visibility_and_export(COUNTRY_CODE, my_map_style)
