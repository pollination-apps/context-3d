''' A module for inputs. '''
import streamlit as st
from origin import Origin
from library import read_tags
from simulation import (run_by_radius,
    run_by_address, run_by_zoom)
from search_location import search_by_coordinates, search_location_by_address

GEVENT_SUPPORT=True

def initialize():
    '''Initialize any of the session state variables if they don't already exist.'''
    if 'avg_lat' not in st.session_state:
        st.session_state.avg_lat = 0
    if 'avg_lon' not in st.session_state:
        st.session_state.avg_lon = 0
    if 'lbt_objects' not in st.session_state:
        st.session_state.lbt_objects = []
    if 'origin' not in st.session_state:
        st.session_state.origin = None
    if 'platform' not in st.session_state:
        st.session_state.platform = 'web'
    if 'data' not in st.session_state:
        st.session_state.data = None
    if 'labels' not in st.session_state:
        st.session_state.labels = None
    if 'colors_dict' not in st.session_state:
        st.session_state.colors_dict = {}

def set_origin():
    '''Specify the lat lon of the origin of CAD 3D space'''
    msg = 'It is the latitude and longitude of the origin XY of a 3D space.\n' + \
        'If this input is disable the app will calculate the reference origin using the ' + \
        'boundary box of the geometries.'
    col1, col2, col3 = st.columns([1, 2, 2])
    spec_location = col1.checkbox(
        label='Set origin',
        help=msg
    )
    if spec_location:
        ref_lat = col2.number_input(label='Ref. latitude(deg)',
        min_value=-90.0, 
        step=0.1,
        value=0.0,
        max_value=90.0,
        format='%.6f',
        key='ref_lat')
        ref_lon = col3.number_input(label='Ref. longitude(deg)',
        min_value=-180.0, 
        step=0.1,
        value=0.0,
        max_value=180.0,
        format='%.6f',
        key='ref_lon')

        st.session_state.origin = Origin(
            lat=ref_lat, 
            lon=ref_lon)
    else:
        st.session_state.origin = None

def set_clippin_radius():
    '''Clippin radius to cut geometries'''
    msg = 'It crops objects using a circle.\n' + \
        'Set it to 0 if you want to disable it.'
    st.number_input(
        label='Clipping radius',
        min_value=0,
        max_value=9000,
        value=200,
        key='clipping_radius',
        help=msg
    )

def set_osm_filters(mode: str):
    '''Filter by OSM tags'''
    def get_osm_type(keyword: str):
        ''' Create a multiselection type for library '''
        res = None
        res_nested = filters.get(keyword)
        if res_nested:
            options = [_[1] for _ in res_nested]
            options.sort()
            res = st.multiselect(
                label=keyword.upper(),
                options=options,
                key=keyword)
    
        return res

    filters = read_tags()
    tags = {}
    # with st.container():
    if mode == 'Basic':
        tags['building'] = "yes"
    else:
        with st.expander('OSM filters'):
            amenity = get_osm_type('amenity')
            barrier = get_osm_type('barrier')
            building = get_osm_type('building')
            highway = get_osm_type('highway')
            aerialway = get_osm_type('aerialway')
            aeroway = get_osm_type('aeroway')
            boundary = get_osm_type('boundary')
            craft = get_osm_type('craft')
            emergency = get_osm_type('emergency')
            geological = get_osm_type('geological')
            historic = get_osm_type('historic')
            landuse = get_osm_type('landuse')
            leisure = get_osm_type('leisure')
            man_made = get_osm_type('man_made')
            military = get_osm_type('military')
            natural = get_osm_type('natural')
            office = get_osm_type('office')
            place = get_osm_type('place')
            power = get_osm_type('power')
            public_transport = get_osm_type('public_transport')
            railway = get_osm_type('railway')
            route = get_osm_type('route')
            shop = get_osm_type('shop')
            sport = get_osm_type('sport')
            telecom = get_osm_type('telecom')
            water = get_osm_type('water')
            waterway = get_osm_type('waterway')

            if amenity:
                tags['amenity'] = amenity
            if barrier:
                tags['barrier'] = barrier
            if building:
                tags['building'] = building
            if highway:
                tags['highway'] = highway
            if aerialway:
                tags['aerialway'] = aerialway
            if aeroway:
                tags['aerialway'] = aeroway
            if boundary:
                tags['boundary'] = boundary
            if craft:
                tags['craft'] = craft
            if emergency:
                tags['emergency'] = emergency
            if geological:
                tags['geological'] = geological
            if historic:
                tags['historic'] = historic
            if landuse:
                tags['landuse'] = landuse
            if man_made:
                tags['man_made'] = man_made
            if military:
                tags['military'] = military
            if natural:
                tags['natural'] = natural
            if office:
                tags['office'] = office
            if place:
                tags['place'] = place
            if power:
                tags['power'] = power
            if public_transport:
                tags['public_transport'] = public_transport
            if railway:
                tags['railway'] = railway
            if route:
                tags['route'] = route
            if shop:
                tags['shop'] = shop
            if sport:
                tags['sport'] = sport
            if telecom:
                tags['telecom'] = telecom
            if water:
                tags['water'] = water
            if water:
                tags['waterway'] = waterway
    return tags

def address_inputs():
    mode = st.selectbox(
        label='Query type',
        options=('Basic', 'Advanced'),
        key='addr-filter')
    tags = set_osm_filters(mode)
    with st.container():
        col1, col2 = st.columns(2)
        address = col1.text_input(
            label='Address',
            value='Times Square, Manhattan, NY 10036, US',
            placeholder='Address here!',
            autocomplete='street-address',
            key='address'
        )
        search_location_by_address(address=address)
        radius = col2.slider(
            label='Radius',
            min_value=10,
            max_value=2000,
            value=500,
            step=10,
            key='by_address_radius'
        )
        
        submitted = st.checkbox(label='Run', 
            value=False, key='run-addr')
    if submitted:
        run_by_address(address, tags, radius)
        return True

def zoom_inputs():
    msg = 'It is a GIS property. For more info see' + \
        ' https://wiki.openstreetmap.org/wiki/Zoom_levels' +\
        '. Common zoom indexes for cities are 13, 14, 15.'
    with st.container():
        col1, col2 = st.columns(2)
        address = col1.text_input(
            label='Address',
            value='Times Square, Manhattan, NY 10036, US',
            placeholder='Address here!',
            autocomplete='street-address',
            key='zoom_address'
        )
        zoom = col2.selectbox(
            options=(11, 12, 13, 14, 15),
            label='Zoom',
            index=3,
            key='zoom',
            help=msg
        )
        search_location_by_address(address=address, 
            zoom=zoom)
        set_osm_filters('Basic')

        submitted = st.checkbox(label='Run', 
            value=False, key='run-zoom')
    if submitted:
        run_by_zoom(address, zoom)
        return True

def radius_inputs():
    mode = st.selectbox(
        label='Query type',
        options=('Basic', 'Advanced'),
        key='rad-filter')
    tags = set_osm_filters(mode)
    with st.container():
        col1, col2 = st.columns(2)
        lat = col1.number_input(
            'Latitude (deg)',
            min_value=-90.0,
            max_value=90.0,
            value=40.7495292, 
            step=0.1,
            format='%.6f',
            key='lat')
        lon = col2.number_input(
            'Longitude (deg)',
            min_value=-180.0,
            max_value=180.0,
            value=-73.9928448,
            step=0.1,
            format='%.6f',
            key='lon')
        search_by_coordinates(lat=lat, 
            lon=lon)
        radius = st.slider(
            label='Radius',
            min_value=10,
            max_value=2000,
            value=500,
            step=10,
            key='by_radius_radius'
        )

        submitted = st.checkbox(label='Run', 
            value=False, key='run-rad')
    if submitted:
        run_by_radius(lat, lon, tags, radius)
        return True