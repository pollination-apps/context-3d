# coding=utf-8
from typing import List
import numpy as np
import json
import pydeck as pdk
import streamlit as st
from geometry_parser import get_geometry
from osm_finder import ( find_features,
    get_dataframe_from_lat_lon, 
    get_dataframe_from_address)
from osm_buildings import osm_find_buildings, from_address_to_lat_lon
from ladybug.location import Location
from pollination_streamlit_io import send_geometry, send_hbjson, manage_settings
from legend import generate_legend
from origin import Origin
from convert import get_model

GEVENT_SUPPORT=True
LEGEND_DATA = {}

def generate_osm_layers(key, values):
    ''' Create pydeck layers from pandas data '''
    color = np.random.choice(range(256), size=3)

    LEGEND_DATA[key] = color

    return pdk.Layer(
        'GeoJsonLayer',
        id=key,
        data=json.loads(values),
        opacity=0.8,
        stroked=False,
        filled=True,
        extruded=True,
        wireframe=True,
        elevation_scale=1,
        get_elevation='properties.height',
        get_fill_color=f'{color.tolist()}',
        get_line_color=color.tolist(),
        pickable=True
    )

def _elaborate_data(dataset, tags, origin, clipping_radius):
    '''Elaborate the OSM request'''
    city_info, gdf_dict, utm_dict, \
        avg_lat, avg_lon = find_features(dataset,
        tags, origin, clipping_radius)

    objects = []
    for k, v in utm_dict.items():
        color = list(np.random.choice(range(256), size=3))
        objects.extend(get_geometry(v, color))

    return gdf_dict, city_info, avg_lat, avg_lon, objects

def _reset_output():
    st.session_state.lbt_objects = []
    st.session_state.data = None
    st.session_state.labels = None

@st.cache(suppress_st_warning=True)
def run_query_by_radius(origin:Origin,
    clipping_radius:int,
    lat:float,
    lon:float,
    tags:List[str],
    radius:float):
    _reset_output()

    dataset = get_dataframe_from_lat_lon(
        lat=lat, 
        lon=lon, 
        tags=tags,
        radius=radius
    )

    gdf_dict, city_info, \
        avg_lat, avg_lon, objects = _elaborate_data(dataset=dataset,
        tags=tags,
        origin=origin,
        clipping_radius=clipping_radius)
    return gdf_dict, city_info, avg_lat, avg_lon, objects

@st.cache(suppress_st_warning=True)
def run_query_by_address(
    origin:Origin,
    clipping_radius:int,
    address:str,
    tags:List[str],
    radius:float):
    _reset_output()

    dataset = get_dataframe_from_address(
        address=address,
        tags=tags,
        radius=radius
    )

    gdf_dict, city_info, \
        avg_lat, avg_lon, objects = _elaborate_data(dataset=dataset,
        tags=tags,
        origin=origin,
        clipping_radius=clipping_radius)
    return gdf_dict, city_info, avg_lat, avg_lon, objects

@st.cache(suppress_st_warning=True)
def run_query_by_zoom_building_only(origin:Origin,
    clipping_radius:int,
    address:str,
    zoom:int):
    _reset_output()

    city_info, gdf_dict, utm_dict, \
        avg_lat, avg_lon = osm_find_buildings(
        address=address, 
        zoom=zoom,
        origin=origin,
        clipping_radius=clipping_radius)
    
    objects = []
    for k, v in utm_dict.items():
        color = list(np.random.choice(range(256), size=3))
        objects.extend(get_geometry(v, color))

    return gdf_dict, city_info, avg_lat, avg_lon, objects


def run_by_radius(lat, 
    lon, tags, radius):
    # set lat lon
    st.session_state.avg_lat = lat
    st.session_state.avg_lon = lon

    gdf_dict, city_info, \
        avg_lat, avg_lon, objects = run_query_by_radius(
            st.session_state.origin,
            st.session_state.clipping_radius,
            lat=lat, lon=lon, 
            tags=tags, radius=radius)
    
    # update lat lon
    if avg_lat and avg_lon:
        st.session_state.avg_lat = avg_lat
        st.session_state.avg_lon = avg_lon
    st.session_state.lbt_objects = objects
    st.session_state.data = gdf_dict
    st.session_state.labels = city_info

def run_by_address(address, tags, radius):
    # set lat lon
    location = from_address_to_lat_lon(address=address)
    if location:
        st.session_state.avg_lat = location.latitude
        st.session_state.avg_lon = location.longitude
    
    gdf_dict, city_info, avg_lat, avg_lon, objects = run_query_by_address(
        st.session_state.origin,
        st.session_state.clipping_radius,
        address=address, 
        tags=tags, 
        radius=radius)

    # update lat lon
    if avg_lat and avg_lon:
        st.session_state.avg_lat = avg_lat
        st.session_state.avg_lon = avg_lon
    st.session_state.lbt_objects = objects
    st.session_state.data = gdf_dict
    st.session_state.labels = city_info

def run_by_zoom(address, zoom):
    gdf_dict, city_info, \
        avg_lat, avg_lon, objects = run_query_by_zoom_building_only(st.session_state.origin,
        st.session_state.clipping_radius,
        address=address, zoom=zoom)
    
    # update output
    st.session_state.avg_lat = avg_lat
    st.session_state.avg_lon = avg_lon
    st.session_state.lbt_objects = objects
    st.session_state.data = gdf_dict
    st.session_state.labels = city_info

def view_output(gdf_dict: dict, 
    city_info: dict):
    lrs = [generate_osm_layers(k, v) for k, v in gdf_dict.items()]
    
    if st.session_state.avg_lat and \
        st.session_state.avg_lon and \
        st.session_state.lbt_objects:
        st.markdown('---')
        INITIAL_VIEW_STATE = pdk.ViewState(
            latitude=st.session_state.avg_lat,
            longitude=st.session_state.avg_lon,
            zoom=16,
            max_zoom=18,
            pitch=45,
            bearing=0)
        
        deck = pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v9',
            initial_view_state=INITIAL_VIEW_STATE,
            layers=lrs)

        # streamlit limit - it does not show hover info
        generate_legend(LEGEND_DATA)
        st.pydeck_chart(deck)
        
        # print city information
        st.markdown(body=f'<h3>Report:</h3>',
            unsafe_allow_html=True)
        st.write(city_info)

def set_cad_settings():
    if st.session_state.platform != 'web':
        loc = Location(latitude=st.session_state.avg_lat,
            longitude=st.session_state.avg_lon)
        manage_settings(key='cad-settings', settings={'location':loc.to_dict()})

def get_output():
    col1, col2 = st.columns(2)
    if st.session_state.platform != 'web':
        set_cad_settings()
        with col1:
            send_geometry(key='geo-preview', 
            geometry=st.session_state.lbt_objects,
            option='subscribe-preview',
            options={'add':True, 
            'delete':True, 
            'preview':False,
            'clear':True})
        with col2:
            model_dict = get_model(st.session_state.lbt_objects)
            send_hbjson(key='model-shades', hbjson=model_dict, 
            option='add',
            options={'subscribe-preview':False,
            'preview':False,
            'clear':False})
    else:
        view_output(st.session_state.data, 
            st.session_state.labels)
