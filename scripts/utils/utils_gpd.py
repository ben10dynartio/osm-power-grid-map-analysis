import geopandas as gpd

def to_empty_file(filename, cols=[], crs=4326):
    gpd.GeoDataFrame({"geometry": []}, geometry="geometry").set_crs(epsg=3857).to_file(filename)
