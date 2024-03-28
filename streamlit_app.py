import folium
import streamlit as st
from streamlit_folium import st_folium
import pandas as pd
import math
from pathlib import Path
import geopandas as gpd
from pyproj import Transformer



# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Misregistration between 2D and 3D Dashboard',
    page_icon=':earth_americas:', # This is an emoji shortcode. Could be a URL too.
)

# -----------------------------------------------------------------------------
# Declare some useful functions.
# Read your CSV data
STSW_1 = pd.read_csv("/workspaces/os-gp/data/STSW_1_Data.csv")
STSW_2 = pd.read_csv("/workspaces/os-gp/data/STSW_2_Data.csv")
STNE_2 = pd.read_csv("/workspaces/os-gp/data/STNE_2_Data.csv")

# Set SHAPE_RESTORE_SHX config option
#gpd.io.file.fiona.drvsupport.supported_drivers['ESRI Shapefile'] = 'rw'
#gpd.io.file.fiona.drvsupport.supported_drivers['SHP'] = 'rw'
#gpd.io.file.fiona.drvsupport.supported_drivers['SHAPEFILE'] = 'rw'

# Read the shapefile
shapefile_path_tiles = "/workspaces/os-gp/Shapefiles/Shapefile/Standard_southwest_mesh_tiles/Standard_southwest_mesh_tiles.shp"
gdf_tiles = gpd.read_file(shapefile_path_tiles)

shapefile_path_centre = "/workspaces/os-gp/Shapefiles/Shapefile/central_meridian/central_meridian.shp"
gdf_centre = gpd.read_file(shapefile_path_centre)

shapefile_path_county = "/workspaces/os-gp/Shapefiles/Shapefile/county_boundaries/county_boundaries.shp"
gdf_county = gpd.read_file(shapefile_path_county)
@st.cache_data
def convert_to_web_mercator(row):

    # Define the transformer from OSGB36 to Web Mercator
    transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326")
    easting, northing = transformer.transform(row['3D_Easting'], row['3D_Northing'])

    return northing, easting  # Return in lat/lon format for Folium


STSW_1['longitude'], STSW_1['latitude'] = zip(*STSW_1.apply(convert_to_web_mercator, axis=1))
STSW_2['longitude'], STSW_2['latitude'] = zip(*STSW_2.apply(convert_to_web_mercator, axis=1))
STNE_2['longitude'], STNE_2['latitude'] = zip(*STNE_2.apply(convert_to_web_mercator, axis=1))


# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
'''
# :earth_americas: GDP Dashboard

Browse GDP data from the [World Bank Open Data](https://data.worldbank.org/) website. As you'll
notice, the data only goes to 2022 right now, and datapoints for certain years are often missing.
But it's otherwise a great (and did I mention _free_?) source of data.
'''

# Add some spacing
''
''



# center on Liberty Bell, add marker
map_center = [STSW_1['latitude'].mean(), STSW_1['longitude'].mean()]
mymap = folium.Map(location=map_center, zoom_start=10)
# Add markers for each coordinate from CSV data
for _, row in STSW_1.iterrows():
    folium.CircleMarker(location=[row['latitude'], row['longitude']], popup='STSW_1', radius=1, color='red', fill=True, fill_color='red').add_to(mymap)
for _, row in STSW_2.iterrows():
    folium.CircleMarker(location=[row['latitude'], row['longitude']], popup='STSW_2', radius=1, color='red', fill=True, fill_color='red').add_to(mymap)
for _, row in STNE_2.iterrows():
    folium.CircleMarker(location=[row['latitude'], row['longitude']], popup='STNE_2', radius=1, color='red', fill=True, fill_color='red').add_to(mymap)

# Add the shapefiles to the map as layers
folium.GeoJson(gdf_tiles, name='Tiles', tooltip='Tiles').add_to(mymap)
folium.GeoJson(gdf_centre, name='Central Meridian', style_function=lambda x: {'color': 'black', 'fillOpacity': 0.5}, tooltip='Central Meridian').add_to(mymap)
folium.GeoJson(gdf_county, name='County Boundaries', style_function=lambda x: {'color': 'orange', 'fillOpacity': 0.5}, tooltip='County Boundaries').add_to(mymap)

# Add layer control
folium.LayerControl().add_to(mymap)

# Display the map
mymap

# call to render Folium map in Streamlit
st_data = st_folium(m, width=725)


min_value = gdp_df['Year'].min()
max_value = gdp_df['Year'].max()

from_year, to_year = st.slider(
    'Which years are you interested in?',
    min_value=min_value,
    max_value=max_value,
    value=[min_value, max_value])

countries = gdp_df['Country Code'].unique()

if not len(countries):
    st.warning("Select at least one country")

selected_countries = st.multiselect(
    'Which countries would you like to view?',
    countries,
    ['DEU', 'FRA', 'GBR', 'BRA', 'MEX', 'JPN'])

''
''
''

# Filter the data
filtered_gdp_df = gdp_df[
    (gdp_df['Country Code'].isin(selected_countries))
    & (gdp_df['Year'] <= to_year)
    & (from_year <= gdp_df['Year'])
]

st.header('GDP over time', divider='gray')

''

st.line_chart(
    filtered_gdp_df,
    x='Year',
    y='GDP',
    color='Country Code',
)

''
''


first_year = gdp_df[gdp_df['Year'] == from_year]
last_year = gdp_df[gdp_df['Year'] == to_year]

st.header(f'GDP in {to_year}', divider='gray')

''

cols = st.columns(4)

for i, country in enumerate(selected_countries):
    col = cols[i % len(cols)]

    with col:
        first_gdp = first_year[gdp_df['Country Code'] == country]['GDP'].iat[0] / 1000000000
        last_gdp = last_year[gdp_df['Country Code'] == country]['GDP'].iat[0] / 1000000000

        if math.isnan(first_gdp):
            growth = 'n/a'
            delta_color = 'off'
        else:
            growth = f'{last_gdp / first_gdp:,.2f}x'
            delta_color = 'normal'

        st.metric(
            label=f'{country} GDP',
            value=f'{last_gdp:,.0f}B',
            delta=growth,
            delta_color=delta_color
        )
