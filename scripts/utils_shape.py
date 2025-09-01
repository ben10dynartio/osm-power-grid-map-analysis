import shapely

def shape_to_polygon(shape):
    if type(shape) == shapely.geometry.collection.GeometryCollection:
        mynewshape = shape.convex_hull
        #mynewshape = shapely.geometry.multipolygon.MultiPolygon(shape.geoms)
        #print(type(mynewshape))
    elif type(shape) == shapely.geometry.multilinestring.MultiLineString:
        mynewshape = shape.convex_hull
    elif type(shape) == shapely.geometry.point.Point:
        mynewshape = shape.buffer(0.00001) # warning : best for epsg 4326
    else:
        mynewshape = shape
    return mynewshape
