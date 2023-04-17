import pandas as pd
import numpy as np
import snowflake.connector
import plotly.graph_objs as go
import plotly.express as px
import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="Demographics",
    page_icon="📊"
)

st.title("Demographics")
st.markdown("Let's see the income demographics of people living in neighborhoods with at least one Starbucks location as opposed to those that don't have any")

@st.cache_resource
def init_connection():
    return snowflake.connector.connect(
        **st.secrets["snowflake"], client_session_keep_alive=True
    )

conn = init_connection()

@st.cache_data(ttl=600)
def run_query(query):
    return pd.read_sql(query, conn)

df = run_query("SELECT * from DORIAN.PUBLIC.STARBUCKS_DEMOGRAPHICS;")


with st.container():
    col1, col2 = st.columns(2)

    with col1:
        # Filter the data by rows where Breakdown is null
        null_data = df[df["Breakdown"].isnull()]

        null_data["Starbucks in neighborhood"] = null_data["Starbucks in neighborhood"].map({True: "Starbucks in neighborhood", False: "Starbucks not in neighborhood"})

        # Group the data by Starbucks in neighborhood and calculate the sum of the Population column
        grouped_data = null_data.groupby("Starbucks in neighborhood").sum()

        # Create the pie chart using plotly.express
        fig = px.pie(grouped_data, values="Value", names=grouped_data.index, hole=0.5, color=grouped_data.index,
                    color_discrete_map={"Starbucks in neighborhood": "#036635", "Starbucks not in neighborhood": "#BAB0AC"})

        # Update the layout of the chart
        fig.update_layout(
            title="Total Population by Starbucks in Neighborhood",
            font=dict(size=12),
            height=400,
            width=400
        )

        # Show the chart
        st.plotly_chart(fig, theme="streamlit", use_container_width=True, config={'displayModeBar': False})

    with col2:
        col21, col22 = st.columns(2)
        with col21:
            st.text("")
            st.markdown("The pie chart shows what percentage of people live in areas with a Starbucks nearby.")
            st.markdown("The bottom chart compares the percentage of people with different income levels who have access to a Starbucks in their neighborhood (green) versus those who don't (gray).")

        with col22:
            st.text("")
            st.markdown("It becomes clear that Starbucks coffee shops are less common in lower-income areas and more prevalent in higher-income neighborhoods.")
            st.markdown("To come up with this analysis, we used US Census data to match up the Starbucks location data by census block group.")
        




grouped = df.groupby(["Starbucks in neighborhood","Breakdown"])["Value"].sum()
pot = pd.concat([grouped / grouped.groupby("Starbucks in neighborhood").transform("sum"), grouped.rename("Population")],axis=1)
pot = pot.reset_index()
pot["Breakdown Order"] = pot["Breakdown"].str.extract("(\d+)").astype(int)
pot["Breakdown Order"] = pot["Breakdown"].apply(lambda x: 0 if x == "Less than $10 000" else int(x.replace("$", "").replace(",", "").split(" ")[0]))
pot = pot.sort_values(by="Breakdown Order")
pot["Population"] = pot["Population"].astype(str)

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=pot[pot["Starbucks in neighborhood"] == False]["Breakdown"],
        y=pot[pot["Starbucks in neighborhood"] == False]["Value"]*100,
        mode="lines+markers",
        name="Starbucks not in neighborhood",
        line_color='#BAB0AC',
        hovertemplate='<b>Income level:</b> %{x}<br><b>Population % of total from neighborhoods without Starbucks:</b> %{y:.1f}%'
    )
)

fig.add_trace(
    go.Scatter(
        x=pot[pot["Starbucks in neighborhood"] == True]["Breakdown"],
        y=pot[pot["Starbucks in neighborhood"] == True]["Value"]*100,
        mode="lines+markers",
        name="Starbucks in neighborhood",
        fill='tonexty', # fill area between trace0 and trace1
        line_color='#036635',
        hovertemplate='<b>Income level:</b> %{x}<br><b>Population % of total from neighborhoods with Starbucks:</b> %{y:.1f}%'
    )
)

# Update the layout of the chart
fig.update_layout(
    title="Starbucks presence in neighborhoods by Household Income Level",
    xaxis_title="",
    yaxis_title="Percentage of Total Value",
    legend_title="Starbucks in neighborhood",
    font=dict(size=12),
    height=600,
    width=800,
    xaxis=dict(showticklabels=False)
)


# Show the chart
st.plotly_chart(fig, theme="streamlit", use_container_width=True, config={'displayModeBar': False})

