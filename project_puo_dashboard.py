import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from pyproj import Transformer

st.title("Polygon Visualization with Google Satellite")

uploaded_file = st.file_uploader(
    "Upload CSV file (must contain STN, E, N columns)",
    type=["csv"]
)

if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

    if all(col in df.columns for col in ['STN','E','N']):

        st.subheader("Data Preview")
        st.write(df)

        # Convert UTM to Lat/Lon (example: UTM Zone 47N)
        transformer = Transformer.from_crs("epsg:32647","epsg:4326",always_xy=True)

        lat = []
        lon = []

        for e,n in zip(df['E'],df['N']):
            lo,la = transformer.transform(e,n)
            lat.append(la)
            lon.append(lo)

        df['Lat'] = lat
        df['Lon'] = lon

        center_lat = df['Lat'].mean()
        center_lon = df['Lon'].mean()

        m = folium.Map(
            location=[center_lat,center_lon],
            zoom_start=18,
            tiles=None
        )

        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='Google Satellite'
        ).add_to(m)

        coords = list(zip(df['Lat'],df['Lon']))
        coords.append(coords[0])

        folium.Polygon(
            locations=coords,
            color='blue',
            fill=True,
            fill_opacity=0.4
        ).add_to(m)

        for i in range(len(df)):
            folium.Marker(
                [df['Lat'][i],df['Lon'][i]],
                popup=df['STN'][i]
            ).add_to(m)

        st_folium(m,width=700,height=500)

    else:
        st.error("CSV must contain STN, E, N columns")
