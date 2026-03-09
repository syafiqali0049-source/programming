import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.title("Polygon Visualization with Google Satellite")

uploaded_file = st.file_uploader(
    "Upload CSV file (must contain STN, Lat, Lon columns)", 
    type=["csv"]
)

if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

    if all(col in df.columns for col in ['STN', 'Lat', 'Lon']):

        st.subheader("Data Preview")
        st.write(df)

        # Create map center
        center_lat = df['Lat'].mean()
        center_lon = df['Lon'].mean()

        # Create folium map with Google Satellite
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=18,
            tiles=None
        )

        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Satellite',
            overlay=False,
            control=True
        ).add_to(m)

        # Create polygon coordinates
        coords = list(zip(df['Lat'], df['Lon']))

        # Close polygon
        coords.append(coords[0])

        # Add polygon
        folium.Polygon(
            locations=coords,
            color='blue',
            fill=True,
            fill_opacity=0.3
        ).add_to(m)

        # Add station markers
        for i in range(len(df)):
            folium.Marker(
                location=[df['Lat'][i], df['Lon'][i]],
                popup=df['STN'][i]
            ).add_to(m)

        # Show map in Streamlit
        st_folium(m, width=700, height=500)

    else:
        st.error("CSV must contain STN, Lat, and Lon columns")

else:
    st.info("Upload CSV file to visualize polygon")
