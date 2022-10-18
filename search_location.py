import folium
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium

def search_location_by_address(address: str, zoom:int=12):
    location = Nominatim(user_agent="GetLoc")
    getLocation = location.geocode(address)
    x, y = getLocation.latitude, getLocation.longitude

    m = folium.Map(location=[x,y],zoom_start=zoom)
    folium.Marker(
        [getLocation.latitude, getLocation.longitude], 
        popup=address, 
        tooltip=address
    ).add_to(m)
    map = st_folium(m, width = 700, 
        height=500)

def search_by_coordinates(lat:float, lon:float, zoom:int=12):
    m = folium.Map(location=[lat, lon], zoom_start=zoom)
    folium.Marker(
        [lat, lon]
    ).add_to(m)
    map = st_folium(m, width = 700, 
        height=500)