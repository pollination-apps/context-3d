# coding=utf-8
import numpy as np
import json
import pydeck as pdk
import streamlit as st
from geometry_parser import get_geometry
from osm_finder import ( find_features,
    get_dataframe_from_lat_lon, 
    get_dataframe_from_address)
from library import read_tags
from osm_buildings import ( osm_find_buildings,
    from_address_to_lat_lon )

from pollination_streamlit_io import ( button, 
    inputs, special )
from ladybug.color import Color
from legend import generate_legend
from origin import Origin
from convert import get_model

LEGEND_DATA = {}
GEVENT_SUPPORT=True

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
    city_info, gdf_dict, utm_dict, \
        avg_lat, avg_lon = find_features(dataset,
        tags, origin, clipping_radius)

    objects = []
    for k, v in utm_dict.items():
        objects.extend(get_geometry(v))

    st.session_state.lbt_objects = objects

    return gdf_dict, city_info, avg_lat, avg_lon


@st.cache(suppress_st_warning=True)
def run_query_by_radius(origin:Origin,
    clipping_radius:int):
    dataset = get_dataframe_from_lat_lon(
        lat=st.session_state.lat, 
        lon=st.session_state.lon, 
        tags=st.session_state.in_tags,
        radius=st.session_state.by_radius_radius
    )

    gdf_dict, city_info, \
        avg_lat, avg_lon = _elaborate_data(dataset=dataset,
        tags=st.session_state.in_tags,
        origin=origin,
        clipping_radius=clipping_radius)
    return gdf_dict, city_info, avg_lat, avg_lon

@st.cache(suppress_st_warning=True)
def run_query_by_address(origin:Origin,
    clipping_radius:int):
    dataset = get_dataframe_from_address(
        address=st.session_state.address,
        tags=st.session_state.in_tags,
        radius=st.session_state.by_address_radius
    )

    gdf_dict, city_info, \
        avg_lat, avg_lon = _elaborate_data(dataset=dataset,
        tags=st.session_state.in_tags,
        origin=origin,
        clipping_radius=clipping_radius)
    return gdf_dict, city_info, avg_lat, avg_lon


@st.cache(suppress_st_warning=True)
def run_query_by_zoom_building_only(origin:Origin,
    clipping_radius:int):
    city_info, gdf_dict, utm_dict, \
        avg_lat, avg_lon = osm_find_buildings(
        address=st.session_state.zoom_address, 
        zoom=st.session_state.zoom,
        origin=origin,
        clipping_radius=clipping_radius)
    
    objects = []
    for k, v in utm_dict.items():
        objects.extend(get_geometry(v))

    st.session_state.lbt_objects = objects

    return gdf_dict, city_info, avg_lat, avg_lon


# begin of the app
st.sidebar.image(
    'https://uploads-ssl.webflow.com/6035339e9bb6445b8e5f77d7/616da00b76225ec0e4d975ba'
    '_pollination_brandmark-p-500.png',
    use_column_width=True
)

# location settings type
QUERY_MODE = {
    'by_zoom': 'Search latitude longitude zoom',
    'by_address': 'Search address',
    'by_radius': 'Search latitude longitude'
}

# query param from URL
query = st.experimental_get_query_params()
platform = special.get_host()

# shared session state for osm query
run = False
if 'query_mode' not in st.session_state:
    st.session_state.query_mode = QUERY_MODE['by_zoom']
if 'avg_lat' not in st.session_state:
    st.session_state.avg_lat = 0
if 'avg_lon' not in st.session_state:
    st.session_state.avg_lon = 0

# sidebar start
st.sidebar.header(
    'Welcome to pollination context app!'+
    '\n1. 🔎 Select search criteria'
    '\n2. 📍 Set base point (Optional)'
    '\n3. 🏠 Select filters (if available)'
    '\n4. 👍 Click on submit'
    '\n5. 🌎 Change location settings'
)
st.sidebar.markdown('---')

st.session_state.query_mode = st.sidebar.selectbox(
        label='Search criteria',
        options=QUERY_MODE.values())

if st.session_state.query_mode == QUERY_MODE['by_radius']:
    with st.expander('Settings', 
        expanded=True):
        cities = {
            'New York': [40.7495292, -73.9928448],
            'Boston': [42.361145, -71.057083],
            'Sydney': [-33.865143, 151.209900],
            'Rio De Janeiro': [-22.9094545, -43.1823189],
            'London': [51.5072, -0.1276]
        }

        option = st.selectbox('Samples',  cities.keys())
        st.write(f'Lat: {cities[option][0]} ',
                f'Lon: {cities[option][1]}')

        st.number_input(
            'Latitude (deg)',
            min_value=-90.0,
            max_value=90.0,
            value=cities[option][0], step=0.1,
            format='%f',
            key='lat')
        st.number_input(
            'Longitude (deg)',
            min_value=-180.0,
            max_value=180.0,
            value=cities[option][1],
            step=0.1,
            format='%f',
            key='lon')
        st.slider(
            label='Radius',
            min_value=10,
            max_value=2000,
            value=500,
            step=10,
            key='by_radius_radius'
    )
elif st.session_state.query_mode == QUERY_MODE['by_address']:
    with st.expander('Settings', 
        expanded=True):
        st.text_input(
            label='Address',
            value='Times Square, Manhattan, NY 10036, US',
            placeholder='Address here!',
            autocomplete='street-address',
            key='address'
        )
        st.slider(
            label='Radius',
            min_value=10,
            max_value=2000,
            value=500,
            step=10,
            key='by_address_radius'
    )
elif st.session_state.query_mode == QUERY_MODE['by_zoom']:
    st.warning(body='Use it carefully.'+ \
        ' Common zoom indexes are 13, 14, 15.')
    with st.expander('Settings', 
        expanded=True):
        st.text_input(
            label='Address',
            value='Times Square, Manhattan, NY 10036, US',
            placeholder='Address here!',
            autocomplete='street-address',
            key='zoom_address'
        )
        st.slider(
            label='zoom',
            min_value=12,
            max_value=15,
            value=14,
            step=1,
            key='zoom'
    )

# origin specification
spec_location = st.sidebar.checkbox(
    label='Set origin'
)
if 'origin' not in st.session_state:
    st.session_state.origin = None
if spec_location:
    st.sidebar.info(body='It is the latitude and longitude of the origin XY of a 3D space.\n' + \
        'Use this input if you want to build context gradually.\n' + \
        'If this input is disable the app will calculate the reference origin using the ' + \
        'boundary box of the geometries.')
    ref_lat = st.sidebar.number_input(label='Ref. latitude(deg)',
    min_value=-90.0, 
    step=0.1,
    value=0.0,
    max_value=90.0,
    key='ref_lat')
    ref_lon = st.sidebar.number_input(label='Ref. longitude(deg)',
    min_value=-180.0, 
    step=0.1,
    value=0.0,
    max_value=180.0,
    key='ref_lon')

    st.session_state.origin = Origin(
        lat=ref_lat, 
        lon=ref_lon)
else:
    st.session_state.origin = None

# filter by OSM tags
filters = read_tags()

# tags session state
if 'in_tags' not in st.session_state:
    st.session_state.in_tags = None

if st.session_state.query_mode == QUERY_MODE['by_zoom']:
    mode = 'Basic'
else:
    mode = st.sidebar.selectbox(
            label='Select filters',
            options=('Basic', 'Advanced'))

with st.sidebar.form('tags'):
    tags = {}

    if mode == 'Basic':
        tags['building'] = "yes"
    else:
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

    submitted = st.form_submit_button('Submit')
    if submitted:
        st.write(tags)
        st.session_state.in_tags = tags

clipping_radius = st.sidebar.number_input(
    label='Clipping radius',
    min_value=0,
    max_value=9000,
    value=0,
    key='clipping_radius'
)

# tags session state
if 'lbt_objects' not in st.session_state:
    st.session_state.lbt_objects = []

session_vars = [st.session_state.get('lat'), 
    st.session_state.get('lon'),
    st.session_state.get('address'),
    st.session_state.get('zoom_address')]
can_run = len(list(filter(None, session_vars)))

if can_run \
    and st.session_state.in_tags:
    try:
        gdf_dict = city_info =  None
        if st.session_state.query_mode == QUERY_MODE['by_radius']:
            # set lat lon
            st.session_state.avg_lat = st.session_state.lat            
            st.session_state.avg_lon = lon=st.session_state.lon

            gdf_dict, city_info, \
                avg_lat, avg_lon = run_query_by_radius(st.session_state.origin,
                st.session_state.clipping_radius)
            
            # update lat lon
            if avg_lat and avg_lon:
                st.session_state.avg_lat = avg_lat
                st.session_state.avg_lon = avg_lon

        elif st.session_state.query_mode == QUERY_MODE['by_address']:
            # set lat lon
            location = from_address_to_lat_lon(address=st.session_state)
            if location:
                st.session_state.avg_lat = location.latitude
                st.session_state.avg_lon = location.longitude

            gdf_dict, city_info, \
                avg_lat, avg_lon = run_query_by_address(st.session_state.origin,
                st.session_state.clipping_radius)

            # update lat lon
            if avg_lat and avg_lon:
                st.session_state.avg_lat = avg_lat
                st.session_state.avg_lon = avg_lon

        elif st.session_state.query_mode == QUERY_MODE['by_zoom']:
            gdf_dict, city_info, \
                avg_lat, avg_lon = run_query_by_zoom_building_only(st.session_state.origin,
                st.session_state.clipping_radius)
            
            # update lat lon
            st.session_state.avg_lat = avg_lat
            st.session_state.avg_lon = avg_lon

        lrs = [generate_osm_layers(k, v) for k, v in gdf_dict.items()]
        
        if st.session_state.avg_lat and \
            st.session_state.avg_lon:
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

    except Exception as e:
        st.error('Convert to LBT failed.')

if st.session_state.lbt_objects:
    st.download_button(
        label='Download Ladybug Json',
        data=json.dumps(st.session_state.lbt_objects),
        file_name='lbt.json')

# user color
def get_colored_geometry_json_strings(geometries: dict, 
    hex_color: str) -> dict:
    '''
    Add colors to dict. So rhino will know what color 
    to use with solids.
    '''
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    geometry_dicts = [g for g in geometries]
    for d in geometry_dicts:
        d['color'] = Color(*rgb).to_dict()
        d['transparency'] = 0.6
    return geometry_dicts


# rhino integration here!
if platform == 'rhino':
    # set rhino location
    st.markdown(body=f'<h3>Settings to rhino:</h3>',
                    unsafe_allow_html=True)
    settings = {
            'earth_anchor': {
                'lat': st.session_state.avg_lat,
                'lon': st.session_state.avg_lon
            }
        }
    special.settings(
        data=settings,
        defaultChecked=True,
        key='to-rhino'
    )

    # get settings from rhino
    # use SETTINGS keyword to get it statically
    # use special.sync token to get it from rhino events
    st.markdown(body=f'<h3>Settings from rhino:</h3>',
                    unsafe_allow_html=True)
    token = special.sync(defaultChecked=True)
    keyword = 'SETTINGS'
    if token and token.startswith('SETTINGS'):
        keyword = token
        st.write(token)

    settings = special.settings(
        data=keyword,
        defaultChecked=True,
        key='from-rhino'
    )
    if settings:
        units = settings.get('units')
    else:
        units = 'Meters'

    # pollination bake button
    # options: Layer to use for baking 
    #          source units
    st.markdown(body=f'<h3>Bake and preview:</h3>',
                    unsafe_allow_html=True)

    # color picker
    color = st.color_picker('Context Color', '#eb2126', 
            key='context-color').lstrip('#')

    # add your favourite color
    # geometries_to_send = rh_dict
    colored_geometries = get_colored_geometry_json_strings(
        st.session_state.lbt_objects,
        color)
    
    button.send('BakeGeometry',
        colored_geometries, 'my-lbt-geometry', 
        options={
            'layer':'StreamlitLayer',
            'units': units
        },
        key='my-lbt-geometry',
        platform=platform)
    
    # display pollination checkbox
    inputs.send(colored_geometries, 
        'my-super-secret-key', 
        options={'layer':'StreamlitLayer', 
            'units': 'Meters'}, 
        key='my-super-secret-key')

    # from geometries to pollination model
    st.markdown(body=f'<h3>Convert to Pollination Model:</h3>',
                    unsafe_allow_html=True)

    to_pollination = st.checkbox(label='Convert to pollination',
        value=False)    
    if to_pollination:
        model_dict = get_model(colored_geometries)

        button.send(action='BakePollinationModel',
            data=model_dict, 
            uniqueId='po-shd-model',
            key='po-shd-model')
elif platform=="sketchup":
    # TODO: Add settings integration with sketchup
    units = "Meters"

    # pollination bake button
    # options: Layer to use for baking 
    #          source units
    st.markdown(body=f'<h3>Bake and preview:</h3>',
                    unsafe_allow_html=True)

    # color picker
    color = st.color_picker('Context Color', '#eb2126', 
            key='context-color').lstrip('#')

    # add your favourite color
    # geometries_to_send = rh_dict
    colored_geometries = get_colored_geometry_json_strings(
        st.session_state.lbt_objects,
        color)

    button.send('BakeGeometry',
        colored_geometries, 'my-lbt-geometry', 
        options={
            'layer':'StreamlitLayer',
            'units': units
        },
        key='my-lbt-geometry',
        platform=platform)
    
    button.send('DrawGeometry',
        colored_geometries, 'my-preview', 
        options={
            'layer':'StreamlitLayer',
            'units': units
        },
        key='my-preview',
        platform=platform)

    # from geometries to pollination model
    st.markdown(body=f'<h3>Convert to Pollination Model:</h3>',
                    unsafe_allow_html=True)

    to_pollination = st.checkbox(label='Convert to pollination',
        value=False)    
    if to_pollination:
        model_dict = get_model(colored_geometries)

        button.send(action='BakePollinationModel',
            data=model_dict, 
            uniqueId='po-shd-model',
            key='po-shd-model',
            platform=platform)