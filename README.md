# osm-power-grid-map-analysis
To build maps and graph analysis on OpenStreetMap (OSM) power grid data (power lines and substations).

This repository contains 2 elements :

* Three python scripts that 1) download data from OpenStreetMap (OSM) via Overpass ; 2) clean and prepare them for building a graph ; 3) Build and analyse a graph
* A QGIS project to render 1) A map showing recent contributions to OpenStreetMap, especially through the project #ohmygrid ; 2) A map showing basic grid consistency

## Configure python script

* Install the needed librairies (pandas, geopandas, networkx, requests, ...)
* Set the desired two-letters COUNTRY_CODE in each script
* Set the desired BUFFER_DISTANCE (in meters) in script 2. This buffer is drawn auround substation to catch all power lines ending around. BUFFER_DISTANCE should be ideally 0, but in practise, we may need some tolerance.
* Run the scripts in the order.


## Configure QGIS project

* Project / Properties / Variable : Set country name
* To build a new country map set :
** Import all produced files by the python script into QGIS. Duplicate countryshape.
** Copy/paste style from the existing layers.
