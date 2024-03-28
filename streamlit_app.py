import folium
import streamlit as st
from streamlit_folium import st_folium, folium_static
from folium.plugins import MarkerCluster
import pandas as pd
from pathlib import Path
import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import Point
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
import math
import seaborn as sns
import numpy as np
import pandas as pd

st.set_page_config(
    page_title="streamlit-folium documentation",
    page_icon="🗺️🇬🇧",
    layout="wide",
)

# Page title and description
st.title("🗺️ Misregistration Messurements between 2D and 3D data")
st.write("""
This is a demonstrator for using 3D collected data from Integrated mesh layer and in comparison to 2D MasterMap Topo data. 
You can select a tile from the dropdown list and view the total number of points within that tile and carry offset analysis.
""")

# Read your CSV data
data_path = "/workspaces/os-gp/data/"
STSW_1 = pd.read_csv(data_path + "STSW_1_Data.csv")
STSW_2 = pd.read_csv(data_path + "STSW_2_Data.csv")
STNE_2 = pd.read_csv(data_path + "STNE_2_Data.csv")

# Read the shapefiles
shapefiles_path = "/workspaces/os-gp/Shapefiles/Shapefile/"
gdf_tiles = gpd.read_file(shapefiles_path + "Standard_southwest_mesh_tiles/Standard_southwest_mesh_tiles.shp")
gdf_centre = gpd.read_file(shapefiles_path + "central_meridian/central_meridian.shp")
gdf_county = gpd.read_file(shapefiles_path + "county_boundaries/county_boundaries.shp")
gdf_STSW_1 = gpd.read_file(shapefiles_path + "Vector/STSW_1_Vector.shp")
gdf_STSW_2 = gpd.read_file(shapefiles_path + "Vector/STSW_2_Vector.shp")
gdf_STNE_2 = gpd.read_file(shapefiles_path + "Vector/STNE_2_Vector.shp")

# Convert coordinates to Web Mercator
def convert_to_web_mercator(df):
    transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326")
    df['latitude'], df['longitude'] = transformer.transform(df['3D_Easting'], df['3D_Northing'])
    return df

STSW_1 = convert_to_web_mercator(STSW_1)
STSW_2 = convert_to_web_mercator(STSW_2)
STNE_2 = convert_to_web_mercator(STNE_2)

# Create Folium map
map_center = [STSW_1['latitude'].mean(), STSW_1['longitude'].mean()]
mymap = folium.Map(location=map_center, zoom_start=10)

# Add markers for each coordinate from CSV data
for df in [STSW_1, STSW_2, STNE_2]:
    for _, row in df.iterrows():
        folium.CircleMarker(location=[row['latitude'], row['longitude']], radius=1, color='red', fill=True, fill_color='red').add_to(mymap)

# Add the shapefiles to the map as layers
folium.GeoJson(gdf_tiles, name='Tiles', tooltip='Tiles').add_to(mymap)
folium.GeoJson(gdf_centre, name='Central Meridian', style_function=lambda x: {'color': 'black', 'fillOpacity': 0.5}, tooltip='Central Meridian').add_to(mymap)
folium.GeoJson(gdf_county, name='County Boundaries', style_function=lambda x: {'color': 'orange', 'fillOpacity': 0.5}, tooltip='County Boundaries').add_to(mymap)


# Add layer control
folium.LayerControl().add_to(mymap)

# Display the map using st_folium
#folium_static(mymap)

# Create columns layout
left_column, right_column = st.columns(2)

with left_column:
    # Select tile
    selected_tile = st.selectbox("Select a tile:", gdf_tiles['tile_ref'].tolist())
    st.write("You selected Tile:", selected_tile)

# Convert selected tile to GeoDataFrame
selected_tile_gdf = gdf_tiles[gdf_tiles['tile_ref'] == selected_tile].copy()
selected_tile_gdf = selected_tile_gdf.to_crs("EPSG:4326")

# Calculate total number of points within selected tile
total_points = 0

# Initialize an empty DataFrame with zeros
summary_df = pd.DataFrame({
    'Distance_Easting': [0, 0, 0, 0],
    'Distance_Northing': [0, 0, 0, 0]
}, index=['Min', 'Mean', 'Std', 'Max'])


for df in [STSW_1, STSW_2, STNE_2]:
    points_in_selected_tile = df[df.apply(lambda row: selected_tile_gdf.geometry.iloc[0].contains(Point(row['longitude'], row['latitude'])), axis=1)]
    total_points += len(points_in_selected_tile)

    # Summary statistics for the selected tile
    summary_stats = {
        "Distance_Easting": {
            "Min": df['Distance_Easting'].min(),
            "Mean": df['Distance_Easting'].mean(),
            "Std": df['Distance_Easting'].std(),
            "Max": summary_df['Distance_Easting'].max()
        },
        "Distance_Northing": {
            "Min": df['Distance_Northing'].min(),
            "Mean": df['Distance_Northing'].mean(),
            "Std": df['Distance_Northing'].std(),
            "Max": df['Distance_Northing'].max()
        }
    }

    # Populate the DataFrame with the actual statistics
    for col, stats in summary_stats.items():
        for row, value in stats.items():
            summary_df.at[row, col] = value

    # Plot scatter plot
    print("Points in selected tile:", points_in_selected_tile)

    fig, axs = plt.subplots(1, 2, figsize=(18, 5))
    # Scatter plot
    axs[0].scatter(df['Distance_Easting'], df['Distance_Northing'], color='blue', s=5)
    axs[0].set_title('Scatter Plot of Points in Selected Tile')
    axs[0].set_xlabel('Distance Easting')
    axs[0].set_ylabel('Distance Northing')

    # Distribution plot
    axs[1].hist(df['Distance_Easting'], bins=20, color='green', alpha=0.7, label='Distance Easting')
    axs[1].hist(df['Distance_Northing'], bins=20, color='orange', alpha=0.7, label='Distance Northing')
    axs[1].set_title('Distribution of Distance')
    axs[1].set_xlabel('Distance')
    axs[1].set_ylabel('Frequency')
    axs[1].legend()

st.write("Visualization plots for the selected tile:", selected_tile)
st.pyplot(fig)

# Update the map
def update_map(selected_tile, mymap):
    # Convert selected tile to GeoDataFrame
    selected_tile_gdf = gdf_tiles[gdf_tiles['tile_ref'] == selected_tile].copy()
    selected_tile_gdf = selected_tile_gdf.to_crs("EPSG:4326")

    # Zoom into the selected tile
    tile_center = selected_tile_gdf.geometry.centroid.values[0].coords[0]
    mymap.location = [tile_center[1], tile_center[0]]
    mymap.zoom_start = selected_tile_gdf  # You can adjust the zoom level as needed

    # Display the updated map using st_folium
    return folium_static(mymap, width=600, height=300)


# Display map in the right column
with right_column:
    # Call the function to update the map
    update_map(selected_tile, mymap)
"""
    # Add GeoJson layers for each grid
    folium.GeoJson(gdf_STSW_1, name='Grid STSW_1', tooltip='Grid STSW_1').add_to(mymap)
    folium.GeoJson(gdf_STSW_2, name='Grid STSW_2', tooltip='Grid STSW_2').add_to(mymap)
    folium.GeoJson(gdf_STNE_2, name='Grid STNE_2', tooltip='Grid STNE_2').add_to(mymap)


    # Iterate over each feature in the GeoJSON for each grid
    for feature in gdf_STSW_1:
        geometry = feature.get('geometry', None)
        if geometry and geometry['type'] == 'LineString':
            coords = geometry['coordinates']
            if len(coords) > 1:
                start_lat, start_lon = coords[0]
                end_lat, end_lon = coords[-1]
                folium.RegularPolygonMarker(location=(start_lat, start_lon), fill_color='blue', number_of_sides=3, radius=10,
                                            rotation=['Angle']).add_to(mymap)

    for feature in gdf_STSW_2:
        geometry = feature.get('geometry', None)
        if geometry and geometry['type'] == 'LineString':
            coords = geometry['coordinates']
            if len(coords) > 1:
                start_lat, start_lon = coords[0]
                end_lat, end_lon = coords[-1]
                #angle = calculate_angle(coords)  # You need to implement a function to calculate the angle
                folium.RegularPolygonMarker(location=(start_lat, start_lon), fill_color='red', number_of_sides=3, radius=10,
                                            rotation=['Angle']).add_to(mymap)

    for feature in gdf_STNE_2:
        geometry = feature.get('geometry', None)
        if geometry and geometry['type'] == 'LineString':
            coords = geometry['coordinates']
            if len(coords) > 1:
                start_lat, start_lon = coords[0]
                end_lat, end_lon = coords[-1]
                #angle = calculate_angle(coords)  # You need to implement a function to calculate the angle
                folium.RegularPolygonMarker(location=(start_lat, start_lon), fill_color='green', number_of_sides=3, radius=10,
                                            rotation=['Angle']).add_to(mymap)

    folium_static(mymap)
"""
with left_column:
    # Display summary statistics in a table
    st.write("Total number of points within selected tile:", total_points)
    st.write("Summary Statistics for Selected Tile:")
    st.table(pd.DataFrame(summary_stats))
    st.write(""" This table displays the statistics of the distance (in m) of the selected tile.""")











