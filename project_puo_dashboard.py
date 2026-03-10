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

        # Close polygon
        df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)

        # ===============================
        # DISTANCE & BEARING CALCULATION
        # ===============================
        distances = []
        bearings = []

        for i in range(len(df_poly)-1):

            dx = df_poly['E'][i+1] - df_poly['E'][i]
            dy = df_poly['N'][i+1] - df_poly['N'][i]

            distance = math.sqrt(dx**2 + dy**2)
            bearing = (math.degrees(math.atan2(dx, dy)) + 360) % 360

            distances.append(distance)
            bearings.append(bearing)

        dist_table = pd.DataFrame({
            "From": df_poly['STN'][:-1],
            "To": df_poly['STN'][1:].values,
            "Distance (m)": distances,
            "Bearing (deg)": bearings
        })

        st.subheader("Distance & Bearing")
        st.dataframe(dist_table)

        # ===============================
        # AREA & PERIMETER
        # ===============================

        poly_coords = list(zip(df['E'], df['N']))
        poly_coords.append(poly_coords[0])

        perimeter = sum(distances)
        polygon = Polygon(poly_coords)
        area = polygon.area

        st.markdown(f"**Polygon Area:** {area:,.2f} m²")
        st.markdown(f"**Polygon Perimeter:** {perimeter:,.2f} m")

        # ===============================
        # CREATE MAP
        # ===============================

        m = folium.Map(
            location=[df['Lat'].mean(), df['Lon'].mean()],
            zoom_start=20,
            tiles=None,
            max_zoom=22
        )

        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='Google Satellite',
            max_zoom=22
        ).add_to(m)

        # Polygon
        polygon_coords = list(zip(df['Lat'], df['Lon']))
        polygon_coords.append(polygon_coords[0])

        folium.Polygon(
            locations=polygon_coords,
            color='blue',
            fill=True,
            fill_opacity=0.3
        ).add_to(m)

        # ===============================
        # POINTS (replace markers)
        # ===============================

        for i,row in df.iterrows():

            folium.CircleMarker(
                location=[row['Lat'], row['Lon']],
                radius=3,
                color="red",
                fill=True,
                fill_color="red"
            ).add_to(m)

        # Fit map to polygon
        m.fit_bounds(polygon_coords)

        # Display map
        st_folium(m, width=1000, height=750)

        # ===============================
        # DOWNLOAD CSV
        # ===============================

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
