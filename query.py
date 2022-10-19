# coding=utf-8
from typing import Optional
import osmnx as ox
import pandas as pd
from geopy.geocoders import Nominatim
import geopandas as gpd
import asyncio
import aiohttp
import ssl
from origin import Origin
from shapely.geometry.point import Point
from ladybug_geojson.slippy.map import ( 
    tile_from_lat_lon,
    get_recurrent_tiles )
import json
# docs
# https://geopandas.org/en/stable/docs/reference.html
# https://osmnx.readthedocs.io/en/stable/index.html

DEFAULT_HEIGHT = 3.0

# OSM Buildings

async def get(
    session: aiohttp.ClientSession,
    url: str,
    **kwargs
) -> dict:
    print(f"Requesting {url}")
    resp = await session.request('GET', url=url, **kwargs)
    data = await resp.json()
    print(f"Received data for {url}")
    return data

async def main(urls, **kwargs):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for u in urls:
            tasks.append(get(session=session, url=u, **kwargs))
        htmls = await asyncio.gather(*tasks, return_exceptions=True)
        return htmls

def from_address_to_lat_lon(address):
    locator = Nominatim(user_agent='loc-finder')
    location = locator.geocode(address)

    return location

def generate_urls(lat: float, 
        lon: float, 
        zoom: int):
    
    urls = []
    coord = (lat, lon)
    pt = tile_from_lat_lon(*coord, zoom)
    tiles = get_recurrent_tiles(*pt, zoom, 15)

    if tiles:
        urls = [
        f'https://data.osmbuildings.org/0.2/anonymous/tile/15/{x}/{y}.json' \
        for x, y in tiles]

    return urls

def osm_find_buildings(address: str, 
        zoom: int,
        origin: Origin,
        clipping_radius: Optional[int]=0):
    
    city_info = {}
    json_dict = {}
    utm_json_dict = {}

    location = from_address_to_lat_lon(address)

    if not location:
        return city_info, json_dict, \
            utm_json_dict, None, None

    lat, lon = location.latitude, location.longitude
    urls = generate_urls(lat=lat, 
        lon=lon, zoom=zoom)
    htmls = asyncio.run(main(urls))
    
    print(f'building tiles: {len(htmls)}')

    df_list = []
    for feat in htmls:
        data = gpd.GeoDataFrame.from_features(feat)
        if data.size != 0:
            data.crs = 'epsg:4326'
            df_list.append(data)

    df = gpd.GeoDataFrame(pd.concat(df_list, ignore_index=True))
    
    if df.empty:
        return city_info, json_dict, \
            utm_json_dict, lat, lon

    cp = df.copy()
    cp.crs = 'epsg:4326'
    utm_group = ox.project_gdf(cp)

    # calculate centroid from init location
    avg_lat, avg_lon = lat, lon
    avg_utm_lat, avg_utm_lon = _from_origin_to_utm(Origin(lat=lat, 
        lon=lon))

    # clipping mask
    if clipping_radius:
        pt = Point(avg_utm_lon, avg_utm_lat)
        cutter = pt.buffer(clipping_radius)
        utm_group = gpd.clip(utm_group, mask=cutter, 
            keep_geom_type=True)
        utm_group_copy = utm_group.copy()
        cp = utm_group_copy.to_crs('epsg:4326')

    # if origin
    if origin:
        avg_utm_lat, avg_utm_lon = _from_origin_to_utm(origin)
        avg_lat, avg_lon = origin.lat, origin.lon

    # save to json dictionary
    json_dict['buildings'] = cp.to_json()

    d = None
    if 'height' in cp:
        d = cp['height']

    # move to origin
    # new geoseries with geometries
    translated = utm_group.translate(-avg_utm_lon, -avg_utm_lat)
    
    # from geoseries to geodataframe
    envgdf = gpd.GeoDataFrame(geometry=translated,
        data=d)
    utm_json_dict['buildings'] = envgdf.to_json()

    return city_info, json_dict, utm_json_dict, avg_lat, avg_lon

def _from_origin_to_utm(origin):
    pt = Point(origin.lon, origin.lat)
    origin_df = gpd.GeoDataFrame(geometry=[pt])
    origin_df.crs = 'epsg:4326'
    utm_origin_df = ox.project_gdf(origin_df)
    avg_utm_lat, avg_utm_lon = get_dataframe_centroid(utm_origin_df)
    return avg_utm_lat,avg_utm_lon

# OpenStreetMap

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
    ox.settings.log_console=True
    ox.settings.use_cache=True

    data = ox.geometries.geometries_from_point(
        [lat, lon],
        tags=tags,
        dist=radius)
    data.crs = 'epsg:4326'

    return data

def get_dataframe_from_address(address: str,
    tags: dict,
    radius: int = 500):
    ox.settings.log_console=True
    ox.settings.use_cache=True

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
    clipping_radius: Optional[int]=0,
    init_origin: Optional[Origin]=None):
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
    utm_group = ox.project_gdf(cp)

    # calculate centroid from init location
    avg_lat, avg_lon = init_origin.lat, init_origin.lon
    avg_utm_lat, avg_utm_lon = _from_origin_to_utm(init_origin)

    # clipping mask
    if clipping_radius:
        pt = Point(avg_utm_lon, avg_utm_lat)
        cutter = pt.buffer(clipping_radius)
        cp = gpd.clip(utm_group, mask=cutter, 
            keep_geom_type=True).to_crs('epsg:4326')

    # if origin
    if origin:
        avg_utm_lat, avg_utm_lon = _from_origin_to_utm(origin)
        avg_lat, avg_lon = origin.lat, origin.lon

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
