# coding=utf-8
from ladybug_geojson.convert.geojson import from_geojson

try:  # import the ladybug dependencies
    from ladybug_geometry.geometry3d.face import Face3D
    from ladybug_geometry.geometry3d.polyface import Polyface3D
except ImportError as e:
    raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))

def get_geometry(data):
    objs = from_geojson(data)

    geometries = []
    for obj in objs:
        geo = obj.geometry
        
        h = obj.properties.get('height')
        if h and isinstance(geo, Face3D):
            geo = Polyface3D.from_offset_face(geo, h)
        if isinstance(geo, list):
            for g in geo:
                geometries.append(g.to_dict())
        else:
            geometries.append(geo.to_dict())
    
    return geometries