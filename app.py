import streamlit as st
from inputs import (initialize, 
    address_inputs, zoom_inputs, radius_inputs, 
    set_origin, set_clippin_radius)
from pollination_streamlit_io import get_host
from simulation import get_output

st.set_page_config(
    page_title='Context 3D',
    page_icon='https://app.pollination.cloud/favicon.ico',
    initial_sidebar_state='collapsed',
)  # type: ignore
st.sidebar.image(
    'https://uploads-ssl.webflow.com/6035339e9bb6445b8e5f77d7/616da00b76225ec0e4d975ba'
    '_pollination_brandmark-p-500.png',
    use_column_width=True
)

QUERY_MODE = ['By Zoom & Address',
    'By Address & Radius',
    'By Coordinates & Radius']

COMMENTS = ['Source: OSM Buildings',
    'Source: OpenStreetMap',
    'Source: OpenStreetMap']

def main():
    """Get context from an OSM query."""

    # title
    st.header('Context 3D')

    # initialize the app and load up all of the inputs
    initialize()
    st.session_state.platform = get_host(key='host-platform')
    
    if st.session_state.platform != 'web':
        set_origin()
    set_clippin_radius()

    mode = st.sidebar.selectbox(
        label='Search',
        options=QUERY_MODE,
        key='search-by')
    
    if mode == QUERY_MODE[0]:
        zoom_inputs()
    elif mode == QUERY_MODE[1]:
        address_inputs()
    else:
        radius_inputs()
    st.sidebar.info(COMMENTS[QUERY_MODE.index(mode)], 
        icon="ℹ️")

    if st.session_state.data:
        get_output()

if __name__ == '__main__':
    main()