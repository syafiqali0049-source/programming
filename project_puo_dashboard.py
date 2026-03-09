import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from pyproj import Transformer
from shapely.geometry import Polygon
import math
import io

st.set_page_config(page_title="GIS Polygon Dashboard", layout="wide")
st.title("GIS Polygon Dashboard (Johor Grid → Google Satellite)")

uploaded_file = st.file_uploader(
    "Upload CSV (must contain STN, E, N in EPSG:4390 Johor Grid)", type=["csv"]
)

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    if all(col in df.columns for col in ['STN','E','N']):

        st.subheader("Data Preview")
        st.dataframe(df)

        # Convert EPSG:4390 → WGS84
        transformer = Transformer.from_crs("epsg:4390","epsg:4326", always_xy=True)
        df['Lon'], df['Lat'] = zip(*[transformer.transform(e,n) for e,n in zip(df['E'], df['N'])])

        # Polygon coordinates for shapely
        poly_coords = list(zip(df['E'], df['N']))
        poly_coords.append(poly_coords[0])  # close polygon

        # Calculate Perimeter
        perimeter = 0
        for i in range(len(poly_coords)-1):
            dx = poly_coords[i+1][0] - poly_coords[i][0]
            dy = poly_coords[i+1][1] - poly_coords[i][1]
            perimeter += math.sqrt(dx*dx + dy*dy)

        # Calculate Area using Shoelace formula
        polygon = Polygon(poly_coords)
        area = polygon.area  # in square meters

        st.markdown(f"**Polygon Area:** {area:,.2f} m²")
        st.markdown(f"**Polygon Perimeter:** {perimeter:,.2f} m")

        # Create folium map
        m = folium.Map(tiles=None)

        # Add Google Satellite tiles
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='Google Satellite'
        ).add_to(m)

        # Create polygon for folium (Lat/Lon)
        polygon_coords = list(zip(df['Lat'], df['Lon']))
        polygon_coords.append(polygon_coords[0])
        folium.Polygon(
            locations=polygon_coords,
            color='blue',
            fill=True,
            fill_opacity=0.4
        ).add_to(m)

        # Add markers
        for i,row in df.iterrows():
            folium.Marker([row['Lat'], row['Lon']], popup=row['STN']).add_to(m)

        # Fit map to polygon bounds
        m.fit_bounds(polygon_coords)

        # Display map
        st_folium(m, width=900, height=700)

        # Optional: Download area/perimeter + coordinates
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="Download Converted CSV (Lat/Lon)",
            data=csv_buffer.getvalue(),
            file_name="converted_polygon.csv",
            mime="text/csv"
        )

    else:
        st.error("CSV must contain columns: STN, E, N")
