# coding=utf-8
from ladybug_geojson.convert.geojson import from_geojson
from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.line import LineSegment3D
from ladybug_geometry.geometry3d.polyline import Polyline3D
from ladybug_geometry.geometry3d.face import Face3D
from ladybug_geometry.geometry3d.polyface import Polyface3D
from ladybug.color import Color
from ladybug_display.geometry3d.point import DisplayPoint3D
from ladybug_display.geometry3d.line import DisplayLineSegment3D
from ladybug_display.geometry3d.polyline import DisplayPolyline3D
from ladybug_display.geometry3d.face import DisplayFace3D
from ladybug_display.geometry3d.polyface import DisplayPolyface3D

def to_dis_geometry(geometry, color):
    if isinstance(geometry, Point3D):
        return DisplayPoint3D(geometry, color)
    elif isinstance(geometry, LineSegment3D):
        return DisplayLineSegment3D(geometry, color)
    elif isinstance(geometry, Polyline3D):
        return DisplayPolyline3D(geometry, color)
    elif isinstance(geometry, Face3D):
        return DisplayFace3D(geometry, color)
    elif isinstance(geometry, Polyface3D):
        return DisplayPolyface3D(geometry, [color])
    else:
        return geometry

def get_geometry(data, color):
    objs = from_geojson(data)
    col = Color(*color)

    dis_geometries = []
    for obj in objs:
        geo = obj.geometry
        
        h = obj.properties.get('height')
        if h and isinstance(geo, Face3D):
            geo = Polyface3D.from_offset_face(geo, h)
            dis_geo = DisplayPolyface3D(geo, col)
            dis_geometries.append(dis_geo.to_dict())
            continue
        
        if isinstance(geo, list):
            for g in geo:
                dis_geo = to_dis_geometry(g, col)
                dis_geometries.append(dis_geo.to_dict())
        else:
            dis_geo = to_dis_geometry(geo, col)
            dis_geometries.append(dis_geo.to_dict())
    
    return dis_geometries