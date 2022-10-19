import streamlit as st
from inputs import (initialize, 
    address_inputs, zoom_inputs, radius_inputs, 
    set_origin, set_clippin_radius)
from pollination_streamlit_io import get_host
from simulation import get_output

st.set_page_config(
    page_title='Find & Import 3D Building Context',
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
    st.header('Find & Import 3D Building Context')
    st.caption('This Pollination App demonstrates connecting '
        'a third party data source to the Pollination ecosystem.\n' 
        'You can also use the Pollination Rhino Plugin to ' 
        'import your context geometry directly into Rhino ')

    # initialize the app and load up all of the inputs
    initialize()
    st.session_state.platform = get_host(key='host-platform')
    # tab1, tab2 = st.tabs(('Search', 'Results'))
    
    # with tab1:
    col1, col2 = st.columns(2)
    sel_provider = col1.selectbox(
        label='Provider',
        options=('OSM Buildings', 'OpenStreetMap'),
        key='provider',
        help='Select the source for data.')

    if sel_provider == 'OSM Buildings':
        q_options = QUERY_MODE[:1]
    else:
        q_options = QUERY_MODE[1:]

    mode = col2.selectbox(
        label='Criteria',
        options=q_options,
        key='search-by',
        help='Parameters used by the query.')
    set_clippin_radius()
    set_origin()
    
    if mode == QUERY_MODE[0]:
        status = zoom_inputs()
    elif mode == QUERY_MODE[1]:
        status = address_inputs()
    else:
        status = radius_inputs()

    # if status:
    #     st.success('Done! Go to Results tab.')

    # with tab2:
    if st.session_state.data:
        get_output()

if __name__ == '__main__':
    main()