#data modelling
import pandas as pd
import numpy as np
import snowflake.connector

#charting
import pydeck as pdk
import plotly.express as px

#streamlit
import streamlit as st

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
    page_title="Starbucks Locations App",
    page_icon="🧋")

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

df = run_query("SELECT PLACEKEY, PARENT_PLACEKEY, LATITUDE, LONGITUDE, STREET_ADDRESS, CITY, REGION, POSTAL_CODE from CORE_POI;")
df["CITY_STATE"] = df["CITY"] + ", " + df['REGION']

st.title('Starbucks Locations Across The US')

# Display the map with filtered data
def smap(df):
    st.pydeck_chart(pdk.Deck(
        map_style=None,
        # initial_view_state=pdk.ViewState(
        #     latitude=df['LATITUDE'].mean(),
        #     longitude=df['LONGITUDE'].mean(),
        #     zoom=3,
        #     # pitch=50,
        # ),
        initial_view_state=pdk.ViewState(
            longitude=df['LONGITUDE'].mean(),
            latitude=df['LATITUDE'].mean(),
            zoom=3,
            pitch=0,
            bearing=0
        ),
        layers=[
            pdk.Layer(
                'ScatterplotLayer',
                data=df,
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

smap(df)

def smap_city(df):
    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            longitude=df['LONGITUDE'].mean(),
            latitude=df['LATITUDE'].mean(),
            zoom=9,
            pitch=0,
            bearing=0
        ),
        layers=[
            pdk.Layer(
                'ScatterplotLayer',
                data=df,
                get_position='[LONGITUDE, LATITUDE]',
                get_color='[0, 112, 74, 200]',
                get_radius=200,
                pickable=True,
                auto_highlight=True,
                filled=True,
                radius_scale=2.5,
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
        st.metric(label="Locations", value=df['PLACEKEY'].nunique())

    with col2:
        st.metric(label="ZIP Codes", value=df['POSTAL_CODE'].nunique())

    with col3:
        st.metric(label="Cities", value=df['CITY_STATE'].nunique())

st.write("---")


top_cities = df.groupby(["CITY_STATE"])["PLACEKEY"].nunique().sort_values(ascending=False).head(10).rename("Locations").rename_axis('City')
top_states = df.groupby(["REGION"])["PLACEKEY"].nunique().sort_values(ascending=False).head(10).rename("Locations").rename_axis('State')

with st.container():
    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(top_cities.reset_index().sort_values(by='Locations',ascending=True),
             x='Locations',
             y='City',
             orientation='h',
             color_discrete_sequence=['#036635'],
             text='Locations',
             title='Top Cities by # of Locations'
            )
        fig.update_layout(xaxis_title='Locations', yaxis_title=None)
        st.plotly_chart(fig, theme="streamlit", use_container_width=True, config={'displayModeBar': False})

    with col2:
        fig = px.bar(top_states.reset_index().sort_values(by='Locations',ascending=True),
             x='Locations',
             y='State',
             orientation='h',
             color_discrete_sequence=['#036635'],
             text='Locations',
             title='Top States by # of Locations'
            )
        fig.update_layout(xaxis_title='Locations', yaxis_title=None)
        st.plotly_chart(fig, theme="streamlit", use_container_width=True, config={'displayModeBar': False})


st.write("---")

# Get the list of selected cities
cities = st.multiselect(
    'What are your favorite cities?',
    df["CITY_STATE"].unique(),
    ["Los Angeles, CA","New York, NY","Seattle, WA"])

# Display a warning if no cities are selected
if len(cities) == 0:
    st.warning('Please select at least one city')
else:
    # Divide the screen into a grid of columns
    num_cols = 3
    num_rows = (len(cities) - 1) // num_cols + 1
    cols = st.columns(num_cols)

    # Display a map for each selected city in a separate column
    for i, city in enumerate(cities):
        row = i // num_cols
        col = i % num_cols
        filtered_df = df[df['CITY_STATE'] == city]
        with cols[col]:
            st.subheader(city)
            st.metric(label="Locations", value=filtered_df['PLACEKEY'].nunique())
            smap_city(filtered_df)    
