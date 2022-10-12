# coding=utf-8
import uuid
from honeybee.shade import Shade
from honeybee.model import Model
from ladybug_display.geometry3d.polyface import DisplayPolyface3D
from ladybug_display.geometry3d.face import DisplayFace3D

def get_model(geometry_dicts):
    ''' From geometries to model '''
    model = Model(identifier=str(uuid.uuid4()))

    for geo_d in geometry_dicts:
        if geo_d.get('type') == 'DisplayPolyface3D':
            geo = DisplayPolyface3D.from_dict(geo_d)
            for f in geo.geometry.faces:
                shd = Shade(identifier=str(uuid.uuid4()),
                    geometry=f)
                if shd:
                    model.add_shade(shd)
        elif geo_d.get('type') == 'DisplayFace3D':
            geo = DisplayFace3D.from_dict(geo_d)
            shd = Shade(identifier=str(uuid.uuid4()),
                geometry=geo.geometry)
            if shd: 
                model.add_shade(shd)

    if model.shades:
        return model.to_dict()
    
    return {}