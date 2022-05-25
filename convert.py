# coding=utf-8
from ladybug_geojson.convert.geojson import from_geojson
import uuid
try:  # import the ladybug dependencies
    from honeybee.shade import Shade
    from honeybee.model import Model
    from ladybug_geometry.geometry3d.face import Face3D
    from ladybug_geometry.geometry3d.polyface import Polyface3D
except ImportError as e:
    raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))

def get_model(geometry_dicts):
    ''' From geometries to model '''
    model = Model(identifier=str(uuid.uuid4()))

    for geo_d in geometry_dicts:
        if geo_d.get('type') == 'Polyface3D':
            geo = Polyface3D.from_dict(geo_d)
            for f in geo.faces:
                shd = Shade(identifier=str(uuid.uuid4()),
                    geometry=f)
                if shd:
                    model.add_shade(shd)
        elif geo_d.get('type') == 'Face3D':
            geo = Face3D.from_dict(geo_d)
            shd = Shade(identifier=str(uuid.uuid4()),
                geometry=geo)
            if shd: 
                model.add_shade(shd)

    if model.shades:
        return model.to_dict()
    
    return {}