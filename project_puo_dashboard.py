import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from pyproj import Transformer
from shapely.geometry import Polygon
import math
import io

st.set_page_config(page_title="GIS Polygon Dashboard", layout="wide")

# ====== SIDEBAR (Logo & Indication) ======
# Saya tambah logo di sini. Pastikan file "logo poli.jpeg" ada dalam folder yang sama dengan script ini.
try:
    st.sidebar.image("logo poli.jpeg", use_container_width=True)
except:
    st.sidebar.warning("Logo 'logo poli.jpeg' tidak dijumpai. Pastikan nama file betul.")

st.sidebar.header("Tetapan Paparan (Indication)")
stn_font_size = st.sidebar.slider("Saiz Font Station (STN)", 8, 20, 10)
dms_font_size = st.sidebar.slider("Saiz Font Bearing/Jarak (DMS)", 6, 16, 8)
marker_size = st.sidebar.slider("Saiz Marker Station", 2, 12, 4)
stn_color = st.sidebar.color_picker("Warna Font Station", "#FFFFFF")
dms_color = st.sidebar.color_picker("Warna Font DMS", "#00FF00")

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

        # ====== Area & Perimeter ======
        poly_coords = list(zip(df["E"], df["N"]))
        polygon = Polygon(poly_coords)
        area = polygon.area
        perimeter = sum(distances)

        col1, col2 = st.columns(2)
        col1.metric("Polygon Area", f"{area:,.2f} m²")
        col2.metric("Polygon Perimeter", f"{perimeter:,.2f} m")

        # ====== Create Folium Map ======
        m = folium.Map(
            location=[df["Lat"].mean(), df["Lon"].mean()],
            zoom_start=20,
            control_scale=True
        )

        # ====== Base Layers ======
        folium.TileLayer("OpenStreetMap", name="Street Map").add_to(m)
        folium.TileLayer(
            tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            attr="Google Satellite",
            name="Google Satellite",
            max_zoom=22
        ).add_to(m)

        # ====== Feature Groups ======
        polygon_layer = folium.FeatureGroup(name="Traverse Polygon").add_to(m)
        station_layer = folium.FeatureGroup(name="Stations").add_to(m)
        dimension_layer = folium.FeatureGroup(name="Traverse Dimensions").add_to(m)

        # ====== Polygon ======
        polygon_coords = list(zip(df["Lat"], df["Lon"]))
        folium.Polygon(
            locations=polygon_coords,
            color="#3388ff",
            weight=3,
            fill=True,
            fill_opacity=0.2
        ).add_to(polygon_layer)

        # ====== Stations (Guna Sidebar Settings) ======
        for _, row in df.iterrows():
            folium.CircleMarker(
                location=[row["Lat"], row["Lon"]],
                radius=marker_size,
                color="yellow",
                weight=1,
                fill=True,
                fill_color="red",
                fill_opacity=1
            ).add_to(station_layer)

            # Label STN - Clean version with Dynamic Font & Shadow
            folium.map.Marker(
                [row["Lat"], row["Lon"]],
                icon=folium.DivIcon(
                    icon_anchor=(15, 0),
                    html=f"""
                    <div style="
                    font-size: {stn_font_size}pt; 
                    color: {stn_color}; 
                    font-weight: bold;
                    text-shadow: 2px 2px 2px black;
                    pointer-events: none;
                    white-space: nowrap;">
                    {row['STN']}
                    </div>
                    """
                )
            ).add_to(station_layer)

        # ====== Bearing & Distance Labels (Guna Sidebar Settings) ======
        for i in range(len(df_poly)-1):
            mid_lat = (df_poly["Lat"][i] + df_poly["Lat"][i+1]) / 2
            mid_lon = (df_poly["Lon"][i] + df_poly["Lon"][i+1]) / 2
            bearing_dms = deg_to_dms(bearings[i])
            label = f"{bearing_dms}<br>{distances[i]:.2f}m"
            
            folium.Marker(
                location=[mid_lat, mid_lon],
                icon=folium.DivIcon(
                    html=f"""
                    <div style="
                    font-size: {dms_font_size}pt;
                    color: {dms_color};
                    font-weight: bold;
                    text-shadow: 1px 1px 2px black;
                    text-align: center;
                    pointer-events: none;
                    width: 150px;
                    margin-left: -75px;">
                    {label}
                    </div>
                    """
                )
            ).add_to(dimension_layer)

        # ====== Area Label (Pusat) ======
        centroid = polygon.centroid
        cen_lon, cen_lat = transformer.transform(centroid.x, centroid.y)
        folium.Marker(
            location=[cen_lat, cen_lon],
            icon=folium.DivIcon(
                html=f"""
                <div style="
                font-size: 14pt;
                font-weight: bold;
                color: #FFD700;
                text-shadow: 2px 2px 4px black;
                text-align: center;
                pointer-events: none;
                width: 200px;
                margin-left: -100px;">
                AREA<br>{area:,.2f} m²
                </div>
                """
            )
        ).add_to(dimension_layer)

        # ====== Fit Map & Show ======
        m.fit_bounds(polygon_coords)
        folium.LayerControl(collapsed=False).add_to(m)
        st_folium(m, width=1100, height=700)

        # ====== Download ======
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button("Download Converted CSV", csv_buffer.getvalue(), "converted.csv", "text/csv")

    else:
        st.error("CSV must contain columns: STN, E, N")

