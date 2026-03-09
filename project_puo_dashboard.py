import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from pyproj import Transformer

st.title("Polygon Visualization on Google Satellite")

uploaded_file = st.file_uploader(
    "Upload CSV (must contain STN, E, N in EPSG:4390 Johor Grid)", type=["csv"]
)

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    # pastikan columns wujud
    if all(col in df.columns for col in ['STN','E','N']):

        st.subheader("Data Preview")
        st.write(df)

        # transform dari EPSG:4390 → WGS84
        transformer = Transformer.from_crs("epsg:4390","epsg:4326", always_xy=True)
        df['Lon'], df['Lat'] = zip(*[transformer.transform(e,n) for e,n in zip(df['E'], df['N'])])

        # map center
        center_lat = df['Lat'].mean()
        center_lon = df['Lon'].mean()

        # create folium map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=18, tiles=None)

        # add Google Satellite tiles
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='Google Satellite',
            name='Google Satellite'
        ).add_to(m)

        # buat polygon
        coords = list(zip(df['Lat'], df['Lon']))
        coords.append(coords[0])  # tutup polygon
        folium.Polygon(
            locations=coords,
            color='blue',
            fill=True,
            fill_opacity=0.4
        ).add_to(m)

        # tambah marker untuk setiap station
        for i,row in df.iterrows():
            folium.Marker([row['Lat'], row['Lon']], popup=row['STN']).add_to(m)

        # paparkan map di Streamlit
        st_folium(m, width=700, height=500)

    else:
        st.error("CSV must contain columns: STN, E, N")
