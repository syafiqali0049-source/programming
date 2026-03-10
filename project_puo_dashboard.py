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

# ====== Function: Decimal Degree → DMS ======
def deg_to_dms(deg):
    d = int(deg)
    m_float = (deg - d) * 60
    m = int(m_float)
    s = (m_float - m) * 60
    return f"{d}°{m}'{s:.2f}\""

# ====== Upload CSV ======
uploaded_file = st.file_uploader(
    "Upload CSV (must contain STN, E, N in EPSG:4390 Johor Grid)", type=["csv"]
)

if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

    if all(col in df.columns for col in ['STN','E','N']):

        st.subheader("Data Preview")
        st.dataframe(df)

        # ====== Convert Johor Grid → WGS84 ======
        transformer = Transformer.from_crs("epsg:4390","epsg:4326", always_xy=True)
        df["Lon"], df["Lat"] = zip(*[
            transformer.transform(e, n)
            for e, n in zip(df["E"], df["N"])
        ])

        # ====== Close polygon for traverse ======
        df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)

        # ====== Calculate Distance & Bearing ======
        distances = []
        bearings = []

        for i in range(len(df_poly)-1):
            dx = df_poly["E"][i+1] - df_poly["E"][i]
            dy = df_poly["N"][i+1] - df_poly["N"][i]
            distance = math.sqrt(dx**2 + dy**2)
            bearing = (math.degrees(math.atan2(dx, dy)) + 360) % 360
            distances.append(distance)
            bearings.append(bearing)

        # ====== Distance & Bearing Table (DMS) ======
        dist_table = pd.DataFrame({
            "From": df_poly["STN"][:-1],
            "To": df_poly["STN"][1:].values,
            "Distance (m)": distances,
            "Bearing (DMS)": [deg_to_dms(b) for b in bearings]
        })

        st.subheader("Distance & Bearing")
        st.dataframe(dist_table)

        # ====== Area & Perimeter ======
        poly_coords = list(zip(df["E"], df["N"]))
        poly_coords.append(poly_coords[0])
        polygon = Polygon(poly_coords)
        area = polygon.area
        perimeter = sum(distances)

        st.markdown(f"**Polygon Area:** {area:,.2f} m²")
        st.markdown(f"**Polygon Perimeter:** {perimeter:,.2f} m")

        # ====== Create Folium Map ======
        m = folium.Map(
            location=[df["Lat"].mean(), df["Lon"].mean()],
            zoom_start=20,
            control_scale=True
        )

        # ====== Base Layers ======
        folium.TileLayer("OpenStreetMap", name="Street Map", control=True).add_to(m)
        folium.TileLayer(
            tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            attr="Google Satellite",
            name="Google Satellite",
            control=True,
            max_zoom=22
        ).add_to(m)

        # ====== Feature Groups ======
        polygon_layer = folium.FeatureGroup(name="Traverse Polygon").add_to(m)
        station_layer = folium.FeatureGroup(name="Stations").add_to(m)
        dimension_layer = folium.FeatureGroup(name="Traverse Dimensions").add_to(m)

        # ====== Polygon ======
        polygon_coords = list(zip(df["Lat"], df["Lon"]))
        polygon_coords.append(polygon_coords[0])
        folium.Polygon(
            locations=polygon_coords,
            color="blue",
            fill=True,
            fill_opacity=0.3
        ).add_to(polygon_layer)

        # ====== Stations with Labels ======
        for _, row in df.iterrows():
            folium.CircleMarker(
                location=[row["Lat"], row["Lon"]],
                radius=4,
                color="red",
                fill=True,
                fill_color="red"
            ).add_to(station_layer)

            folium.map.Marker(
                [row["Lat"], row["Lon"]],
                icon=folium.DivIcon(
                    html=f"""
                    <div style="
                    font-size:10pt;
                    background:white;
                    padding:2px;
                    border-radius:3px;
                    text-align:center;">
                    {row['STN']}
                    </div>
                    """
                )
            ).add_to(station_layer)

        # ====== Bearing & Distance Labels ======
        for i in range(len(df_poly)-1):
            lat1 = df_poly["Lat"][i]
            lon1 = df_poly["Lon"][i]
            lat2 = df_poly["Lat"][i+1]
            lon2 = df_poly["Lon"][i+1]
            mid_lat = (lat1 + lat2) / 2
            mid_lon = (lon1 + lon2) / 2
            bearing_dms = deg_to_dms(bearings[i])
            label = f"{bearing_dms} / {distances[i]:.2f} m"
            folium.Marker(
                location=[mid_lat, mid_lon],
                icon=folium.DivIcon(
                    html=f"""
                    <div style="
                    font-size:10pt;
                    background:white;
                    padding:2px;
                    border-radius:3px;
                    text-align:center;">
                    {label}
                    </div>
                    """
                )
            ).add_to(dimension_layer)

        # ====== Area Label ======
        centroid = polygon.centroid
        cen_lon, cen_lat = transformer.transform(centroid.x, centroid.y)
        folium.Marker(
            location=[cen_lat, cen_lon],
            icon=folium.DivIcon(
                html=f"""
                <div style="
                font-size:14pt;
                font-weight:bold;
                color:white;
                background:rgba(0,0,0,0.6);
                padding:6px;
                border-radius:5px;
                text-align:center;">
                AREA<br>{area:,.2f} m²
                </div>
                """
            )
        ).add_to(dimension_layer)

        # ====== Fit Map ======
        m.fit_bounds(polygon_coords)

        # ====== Layer Control ======
        folium.LayerControl(collapsed=False).add_to(m)

        # ====== Show Map ======
        st_folium(m, width=1000, height=750)

        # ====== Download CSV ======
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="Download Converted CSV",
            data=csv_buffer.getvalue(),
            file_name="converted_polygon.csv",
            mime="text/csv"
        )

    else:
        st.error("CSV must contain columns: STN, E, N")
