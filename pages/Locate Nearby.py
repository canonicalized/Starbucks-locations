import streamlit as st
import pandas as pd
import pydeck as pdk
from functions import format_open_hours
# import osmnx as ox
from shapely.geometry import Point, Polygon
import openrouteservice as ors
import openrouteservice.exceptions as ors_exc
from geopy.geocoders import Nominatim

from st_pages import Page, show_pages
# Specify what pages should be shown in the sidebar, and what their titles and icons should be
show_pages(
    [
        Page("Locations.py", "Locations", "📍"),
        Page("pages/Demographics.py", "Demographics", "📊"),
        Page("pages/Locate Nearby.py", "Locate Nearby", "🌍")
    ]
)
st.set_page_config(
    layout="wide",
    page_title="Locator",
    page_icon="🌍"
)
st.title("Find a Starbucks Nearby")

# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    return snowflake.connector.connect(
        **st.secrets["snowflake"], client_session_keep_alive=True
    )

conn = init_connection()

# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def run_query(query):
    return pd.read_sql(query, conn) 

df = run_query("SELECT PLACEKEY, LATITUDE, LONGITUDE, STREET_ADDRESS, OPEN_HOURS from CORE_POI;")
# df['CITY_STATE'] = df['CITY'] + ", " + df['REGION']
df['OPEN_HOURS'] = df['OPEN_HOURS'].apply(format_open_hours)

with st.expander("Input your address and we'll find the closest coffee shops to your location", expanded=True):
    with st.container():
        col1, col2, col3 = st.columns(3)

        with col1:
            # Set up input form
            address = st.text_input("Enter your address:", placeholder="19 Washington Square N, New York, NY 10011, USA")

        with col2:
            transit_options = ['Walk','Drive','Cycle']
            transit_selected = st.selectbox("Walk or drive?", transit_options)

        with col3:
            # Set up walk/drive time selection
            time_options = [5, 10, 15]  # in minutes
            time_selected = st.selectbox("Select walk/drive time (minutes):", time_options)
        
        # Add apply button
        fas = st.button('Find a Starbucks')

def mode_transit(transit_selected):
    if transit_selected == 'Walk':
        return 'foot-walking'
    elif transit_selected == 'Drive':
        return 'driving-car'
    elif transit_selected == 'Cycle':
        return 'cycling-regular'
    else:
        return 'foot-walking'

# m = folium.Map(location=(-73.9975615903237, 40.73192615), zoom_start=13)
# st_folium(map, width=700, height=450)
if fas:
    if len(address)<5:
        st.warning("Please input a valid address")
    else:
        with st.spinner('Generating map...'):
            # Calculate user location coordinates using geopy
            geolocator = Nominatim(user_agent="my_app")
            location = geolocator.geocode(address)
            if location is None:
                st.error("Address not found.")
                st.stop()
            user_coords = (location.longitude,location.latitude)

            # st.write(user_coords)

            # Define function to generate isochrone
            def generate_isochrone(location, time, mode=transit_selected):
                try:
                    # Set up OpenRouteService client with API key
                    client = ors.Client(key=st.secrets.ors_creds.api_key)

                    # Specify query parameters
                    query = {
                        "locations": [location],
                        "range": [0, time],
                        "range_type": "time",
                        "profile": mode_transit(mode),
                        "location_type": "start"
                    }

                    # Send request to OpenRouteService API
                    result = client.isochrones(**query)

                    # st.write(result)

                    # Extract isochrone geometry
                    polygons = [Polygon(shape) for shape in result["features"][0]["geometry"]["coordinates"]]
                    # feature = result["features"][0]
                    return polygons#, feature
                except ors_exc.ApiError:
                    st.error("Unable to generate isochrone. Please try again later.")
                    st.stop()

            # Generate isochrone
            isochrone = generate_isochrone(user_coords, time_selected * 60, mode="walking")

            # Convert the Polygon to a list of lists
            coordinates = list(isochrone[0].exterior.coords)
            polypd = [[[c[0], c[1]] for c in coordinates]]

            sb_locations = pd.DataFrame()
            # Define layer for Starbucks locations within isochrone
            for _, row in df.iterrows():
                sb_coords = (row["LONGITUDE"], row["LATITUDE"])
                sb_point = Point(sb_coords)
                if any(sb_point.within(polygon) for polygon in isochrone):
                    sb_locations = sb_locations.append({"LONGITUDE": row["LONGITUDE"], "LATITUDE": row["LATITUDE"], "STREET_ADDRESS":row["STREET_ADDRESS"], "OPEN_HOURS":row["OPEN_HOURS"]}, ignore_index=True)

            st.pydeck_chart(pdk.Deck(
                map_style=None,
                initial_view_state=pdk.ViewState(
                    longitude=location.longitude,
                    latitude=location.latitude,
                    zoom=13,
                    pitch=0,
                    bearing=0
                ),
                layers=[
                    pdk.Layer(
                        "PolygonLayer",
                        polypd,
                        stroked=True,
                        # processes the data as a flat longitude-latitude pair
                        get_polygon="-",
                        get_fill_color=[3, 102, 53, 50],
                        get_line_color=[3, 102, 53, 160],
                        get_line_width=15
                    ),
                    pdk.Layer(
                        'ScatterplotLayer',
                        data=sb_locations,
                        get_position='[LONGITUDE, LATITUDE]',
                        get_color='[0, 112, 74, 160]',
                        get_radius=200,
                        pickable=True,
                        auto_highlight=True,
                        filled=True,
                        radius_scale=2,
                        radius_min_pixels=1,
                        radius_max_pixels=8,
                        line_width_min_pixels=1,
                    ),
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=[{"position": user_coords, "STREET_ADDRESS": "Your Location", "OPEN_HOURS":""}],
                        get_position="position",
                        get_color="[255, 0, 0, 255]",
                        get_radius=100,
                        pickable=True,
                        auto_highlight=True,
                    )
                ],
                tooltip={
                    "text": "Address: {STREET_ADDRESS}\n {OPEN_HOURS}"
                }
            ))

