#data modelling
import pandas as pd
import numpy as np
import snowflake.connector

#charting
import pydeck as pdk

#streamlit
import streamlit as st
st.set_page_config(
    layout="wide",
    page_title="Multipage App",
    page_icon="👋")

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
    # with conn.cursor() as cur:
    #     cur.execute(query)
    #     return cur.fetchall()


df = run_query("SELECT PLACEKEY, PARENT_PLACEKEY, LATITUDE, LONGITUDE, STREET_ADDRESS, CITY, REGION, POSTAL_CODE from CORE_POI;")

states = np.append('All', df['REGION'].unique())
cities = np.append('All', df['CITY'].unique())
zipcodes = np.append('All', df['POSTAL_CODE'].unique())

fdf = df.copy()

st.title('Starbucks Locations Across The US')
with st.expander("Filters", expanded=True):
    with st.container():
        col1, col2, col3 = st.columns(3)

        with col1:
            selected_states = st.multiselect(
                'Choose States',
                states,
                'All')

        with col2:
            selected_cities = st.multiselect(
                'Choose Cities',
                cities,
                'All')

        with col3:
            selected_zipcodes = st.multiselect(
                'Choose ZIP Codes',
                zipcodes,
                'All')
            
    # Add apply button
    if st.button('Apply filters'):

        # Filter the DataFrame based on selected options
        if 'All' not in selected_states and len(selected_states) > 0:
            fdf = fdf[fdf['REGION'].isin(selected_states)]

        if 'All' not in selected_cities and len(selected_cities) > 0:
            fdf = fdf[fdf['CITY'].isin(selected_cities)]

        if 'All' not in selected_zipcodes and len(selected_zipcodes) > 0:
            fdf = fdf[fdf['POSTAL_CODE'].isin(selected_zipcodes)]
    
# # Display the filtered DataFrame
# st.dataframe(fdf)

# st.map(fdf)

# Display the map with filtered data
st.pydeck_chart(pdk.Deck(
    map_style=None,
    initial_view_state=pdk.ViewState(
        latitude=fdf['LATITUDE'].mean(),
        longitude=fdf['LONGITUDE'].mean(),
        zoom=3,
        # pitch=50,
    ),
    layers=[
        pdk.Layer(
            'ScatterplotLayer',
            data=fdf,
            get_position='[LONGITUDE, LATITUDE]',
            get_color='[0, 112, 74, 160]',
            get_radius=200,
            pickable=True,
            auto_highlight=True,


    filled=True,
    radius_scale=6,
    radius_min_pixels=1,
    radius_max_pixels=10,
    line_width_min_pixels=1,
        )
    ],
    tooltip = {
        "text": "Address: {STREET_ADDRESS}"
    }
))





with st.container():
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="Locations", value=fdf['PLACEKEY'].count(), delta="1.2 °F")

    with col2:
        st.metric(label="Cities", value=fdf['CITY'].nunique(), delta="1.2 °F")

    with col3:
        st.metric(label="ZIP Codes", value=fdf['REGION'].nunique(), delta="1.2 °F")
        
# observable("Voronoi Map", 
#     notebook="@mbostock/u-s-voronoi-map-o-matic", 
#     targets=["map"],
#     redefine={
#         "data": fdf[["LONGITUDE", "LATITUDE", "PLACEKEY"]].to_dict(orient="records")
#     }
# )