import streamlit as st
import pandas as pd
import folium 
from streamlit_folium import st_folium
import plotly.express as px
import json

st.set_page_config(layout="wide")

st.markdown("""
    <h1 style='text-align: center;
               color: white;
               background: linear-gradient(120deg, #1f4037, #99f2c8);
               padding: 20px;
               border-radius: 12px;'>
        Socioeconomic Spatial Analysis of US Food Access
    </h1>
""", unsafe_allow_html=True)

#st.title("Food Insecurity & Food Desert Analytics Dashboard")

# LOAD DATA
df = pd.read_csv("master_dataset_only_common_counties.csv")

# Load GeoJSON 
with open("geojson-counties-fips.json") as f:
    counties_geojson = json.load(f)

# Ensure FIPS is string
df["CountyFIPS"] = df["CountyFIPS"].astype(str).str.zfill(5)
df['Food_Insecurity_Rate'] =(df['Overall Food Insecurity Rate']*100).round(2)
df['Population'] = df['Pop2010'].round(1)
df['Food Access Vulnerability Rate'] = ((df['Vulnerability_Score_PCA']).round(2)).copy()
df['snap_participation_rate'] = (df['snap_participation_rate']*100).round(2)
df['food_insecurity_risk_index'] = (df['food_insecurity_risk_index']*100).round(2)

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.header("Filters")

level = st.sidebar.radio('Select Level', ['County', 'State'])

selected_states = st.sidebar.multiselect(
    "Select State(s)",
    options=sorted(df["State"].unique()),
    default=None
)
if selected_states:
    df = df[df["State"].isin(selected_states)]

# -----------------------------
# TOP COUNTIES
# -----------------------------

# Aggregate if state level
if level == "State":
    df_grouped = df.groupby("State").mean(numeric_only=True).round(2).reset_index()
    df_grouped["Name"] = df_grouped["State"]
else:
    df_grouped = df.copy()
    # df_grouped["County_State"] = df["County"] + ", " + df["State"]
    df_grouped["Name"] = df_grouped["County"]

top_n = st.sidebar.slider("Top N", 5, 20, 10)

# KPI cards with Food Insecurity, Food Desert Index, SNAP Participation, Risk Index and Populaiton

st.markdown('###')
st.subheader("Key Insights")
def kpi_card(title, value, color):
    st.markdown(f"""
        <div style="
            background: {color};
            padding: 14px;
            border-radius: 10px;
            text-align: center;
            color: white;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.15);
        ">
            <h5 style='margin-bottom:5px'>{title}</h5>
            <h2>{value}</h2>
        </div>
    """, unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:kpi_card(
    "Avg Food Insecurity",
    f"{df['Food_Insecurity_Rate'].mean():.2f}%", "#ff6b6b"
)

with col2: kpi_card(
    "Food Access Vulnerability Rate",
    f"{df['Food Access Vulnerability Rate'].mean():.2f}" ,"#4ecdc4"
)

with col3: kpi_card(
    "SNAP Participation Rate",
    f"{df['snap_participation_rate'].mean():.2f}%", "#1a535c"
)

with col4: kpi_card(
    "Food Insecurity Risk Index",
    f"{df['food_insecurity_risk_index'].mean():.2f}%","#ffa600"
)

with col5: kpi_card(
    "Total Population",
    f"{int(df['Population'].sum()):,}", "#6a4c93"
)
df['PovertyRate'] = df['PovertyRate'].round(2)
df['MedianFamilyIncome'] = df['MedianFamilyIncome'].round(2)
features = [
    "PovertyRate",
    "MedianFamilyIncome",
    "snap_participation_rate"
]

target = "Food_Insecurity_Rate"

# Create two main columns one for bar chart and one for scatter analysis
col1, col2 = st.columns(2)


with col1:
    st.markdown("###")
    st.markdown("#### Bar Chart")

    metric = st.selectbox(
        "Select Metric",
        [
            "Food Access Vulnerability Rate",
            "Food_Insecurity_Rate",
            "snap_participation_rate"
        ],
        key="bar_metric"
    )
    st.subheader(f"Top {top_n} {level} by {metric}")
    if metric not in df_grouped.columns:
        st.error(f"{metric} not found in data")
    else:
        top_df = df_grouped.sort_values(metric, ascending=False).round(2).head(top_n)
    
    y_col = 'Name'
    fig_bar = px.bar(
        top_df,
        x=metric,
        y=y_col,
        orientation="h",
        hover_data=["Population", "PovertyRate", "MedianFamilyIncome"]
    )

    st.plotly_chart(fig_bar, width='stretch')

# -----------------------------
# SCATTER PLOT
# -----------------------------
with col2:
    st.markdown("###")
    st.subheader("Scatter Analysis")
    c1, c2 = st.columns(2)
    with c1:
        x_var = st.selectbox(
            "X-axis",
            features,
         key="scatter_x"
        )

    with c2:
        y_var = st.selectbox(
        "Y-axis",
        ["Food_Insecurity_Rate"],
        key="scatter_y"
    )

    fig_scatter = px.scatter(
        top_df,
        x=x_var,
        y=y_var,
        size="Population",
        color="food_insecurity_risk_index",
        hover_name="Name"
    )

    st.plotly_chart(fig_scatter, width='stretch')

# -----------------------------
# CHOROPLETH MAP
# -----------------------------
st.subheader("US Map with Counties")

fig_map = px.choropleth(
    df,
    geojson=counties_geojson,
    locations="CountyFIPS",
    color=metric,
    color_continuous_scale="Viridis",
    scope="usa",
    hover_data=[
        "County",
        "State",
        "Population",
        "PovertyRate",
        "MedianFamilyIncome",
        "Food Access Vulnerability Rate"
        
    ]
)
fig_map.update_traces(
    marker_line_width=0.3,
    marker_line_color="white",
    hovertemplate=
    "<b>%{customdata[0]}, %{customdata[1]}</b><br>" +
    "Population: %{customdata[2]:,}<br>" +
    "Poverty: %{customdata[3]:.2f}%<br>" +
    "SNAP: %{customdata[4]:.2f}%<br>" +
    "Income: $%{customdata[5]:,.0f}<br>" +
    "Vulnerability: %{customdata[6]:.2f}<extra></extra>",
    customdata=df[[
        "County",
        "State",
        "Population",
        "PovertyRate",
        "snap_participation_rate",
        "MedianFamilyIncome",
        "Food Access Vulnerability Rate"
    ]]
)

fig_map.update_layout(
    margin={"r":0,"t":0,"l":0,"b":0},
    geo=dict(
        scope="usa",
        projection_type="albers usa",
        showframe=True,
        showland=True,
        landcolor="rgb(245,245,245)",

        showocean=True,
        oceancolor="rgb(220,240,255)",

        showlakes=True,
        lakecolor="rgb(220,240,255)",

        showcoastlines=True,
        coastlinecolor="gray",
    ),
    coloraxis_colorbar=dict(
    
        thickness=15,
        len=0.7
    )
)

st.plotly_chart(fig_map, width='stretch')


# DATA TABLE
st.subheader("Data Preview")
st.dataframe(df.head(10))
