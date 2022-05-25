#!/usr/bin/env python
import json
from typing import Optional
import osmnx as ox
import geopandas as gpd
from origin import Origin
from shapely.geometry.point import Point
# docs
# https://geopandas.org/en/stable/docs/reference.html
# https://osmnx.readthedocs.io/en/stable/index.html

DEFAULT_HEIGHT = 3.0

def try_parse(x):
    ''' Convert str to float '''
    try:
        return float(x)
    except:
        return DEFAULT_HEIGHT


def set_height(group,
    column=None):
    if 'height' in group:
        # try to clean 'm'
        group['height'].replace(to_replace=r'[m]', value='',
                        regex=True, inplace=True)

        # try fill NaN with building:levels (building only)
        if column:
            group['height'] = group['height'] \
                        .fillna(group[column].apply(try_parse)\
                        .apply(lambda x: x * DEFAULT_HEIGHT))

        # try to fill with default height
        group['height'] = group['height'] \
                        .fillna(DEFAULT_HEIGHT).apply(try_parse)

def _get_building_settings(group):
    settings = {}
    cp = group.copy()
    materials = {}
    if 'building:material' in cp:
        t = cp.groupby(['building:material'])['geometry'].count()
        materials = t.to_dict()
    if materials:
        settings['building:material'] = materials

    return settings


def get_dataframe_from_lat_lon(lat: float,
    lon: float,
    tags: dict,
    radius: int = 500):
    ox.config(log_console=True, use_cache=True)

    data = ox.geometries.geometries_from_point(
        [lat, lon],
        tags=tags,
        dist=radius)
    data.crs = 'epsg:4326'

    return data


def get_dataframe_from_address(address: str,
    tags: dict,
    radius: int = 500):
    ox.config(log_console=True, use_cache=True)

    data = ox.geometries.geometries_from_address(
        address=address,
        tags=tags,
        dist=radius)
    data.crs = 'epsg:4326'

    return data

def get_dataframe_centroid(data:gpd.GeoDataFrame):
    ''' Get avg lat lon from geodaframe '''
    if 'geometry' in data:
        rep_point = data.get('geometry').representative_point()
        lon = rep_point.x.mean()
        lat = rep_point.y.mean()
        return lat, lon
    else:
        return None, None


def find_features(data: gpd.GeoDataFrame,
    tags: dict,
    origin: Optional[Origin]=None,
    clipping_radius: Optional[int]=0):
    ''' Get features from OSM request '''
    city_info = {}
    json_dict = {}
    utm_json_dict = {}

    ox.config(log_console=True, use_cache=True)

    if data.empty:
        return city_info, json_dict, \
            utm_json_dict, None, None

    # global avg lat lon (utm)
    cp = data.copy()
    avg_lat, avg_lon = get_dataframe_centroid(cp)

    utm_group = ox.project_gdf(cp)
    avg_utm_lat, avg_utm_lon = get_dataframe_centroid(utm_group)

    # if origin
    if origin:
        pt = Point(origin.lon, origin.lat)
        origin_df = gpd.GeoDataFrame(geometry=[pt])
        origin_df.crs = 'epsg:4326'
        utm_origin_df = ox.project_gdf(origin_df)
        avg_utm_lat, avg_utm_lon = get_dataframe_centroid(utm_origin_df)
        avg_lat, avg_lon = origin.lat, origin.lon
    
    # clipping mask
    if clipping_radius:
        pt = Point(avg_utm_lon, avg_utm_lat)
        cutter = pt.buffer(clipping_radius)
        cp = gpd.clip(utm_group, mask=cutter, 
            keep_geom_type=True).to_crs('epsg:4326')



    # TODO: fix amenities behavior
    # TODO: improve filters
    for k, v in tags.items():
        try:
            grouped = cp.groupby(k)
        except KeyError as e:
            grouped = None
        if grouped:
            # group=values
            for key, group in grouped:
                unique_key = ':'.join([k, key])

                base_statistic={
                    'count': len(group)
                }

                if k == 'amenity':
                    set_height(group)
                if k == 'building':
                    set_height(group, 'building:levels')
                    # merge additional building info
                    base_statistic = {**base_statistic,
                        **_get_building_settings(group)}

                # copy height series if building
                d = None
                if k == 'building':
                    if 'height' in group:
                        d = group['height']

                # save to json dictionary
                json_dict[unique_key] = group.to_json()

                # project
                utm_group = ox.project_gdf(group)

                # move to origin
                # new geoseries with geometries
                translated = utm_group.translate(-avg_utm_lon, -avg_utm_lat)

                # from geoseries to geodataframe
                envgdf = gpd.GeoDataFrame(geometry=translated,
                    data=d)
                utm_json_dict[unique_key] = envgdf.to_json()

                city_info[unique_key] = base_statistic

    return city_info, json_dict, utm_json_dict, avg_lat, avg_lon
