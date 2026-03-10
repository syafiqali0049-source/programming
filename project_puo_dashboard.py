import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from pyproj import Transformer
from shapely.geometry import Polygon
import math
import io

# ====== CONFIG ======
st.set_page_config(page_title="GIS Polygon Dashboard", layout="wide")

# ====== 1. SISTEM LOG MASUK (LOGIN) ======
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def logout():
    st.session_state.logged_in = False
    st.rerun()

if not st.session_state.logged_in:
    empty_col1, login_col, empty_col2 = st.columns([1, 2, 1])
    with login_col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        try:
            st.image("logo poli.jpeg", use_container_width=True)
        except:
            pass
        st.title("🔐 Log Masuk Sistem GIS")
        with st.form("login_form"):
            user_input = st.text_input("Username", value="admin")
            pass_input = st.text_input("Password", type="password")
            submit = st.form_submit_button("Masuk")
            if submit:
                if user_input == "admin" and pass_input == "12345":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Username atau Password salah!")
    st.stop()

# ====== 2. DASHBOARD UTAMA ======
try:
    st.sidebar.image("logo poli.jpeg", use_container_width=True)
except:
    pass

st.sidebar.header("Tetapan Paparan (Indication)")
stn_font_size = st.sidebar.slider("Saiz Font Station (STN)", 8, 20, 10)
dms_font_size = st.sidebar.slider("Saiz Font Bearing/Jarak (DMS)", 6, 16, 8)
marker_size = st.sidebar.slider("Saiz Marker Station", 2, 12, 6)
stn_color = st.sidebar.color_picker("Warna Font Station", "#FFFFFF")
dms_color = st.sidebar.color_picker("Warna Font DMS", "#00FF00")

st.sidebar.markdown("---")
if st.sidebar.button("Log Keluar"):
    logout()

st.title("GIS Polygon Dashboard (Johor Grid → Google Satellite)")

def deg_to_dms(deg):
    d = int(deg)
    m_float = (deg - d) * 60
    m = int(m_float)
    s = (m_float - m) * 60
    return f"{d}°{m}'{s:.2f}\""

uploaded_file = st.file_uploader("Upload CSV (STN, E, N)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    if all(col in df.columns for col in ['STN','E','N']):
        # Convert Johor Grid → WGS84
        transformer = Transformer.from_crs("epsg:4390","epsg:4326", always_xy=True)
        df["Lon"], df["Lat"] = zip(*[transformer.transform(e, n) for e, n in zip(df["E"], df["N"])])

        df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        distances, bearings = [], []
        for i in range(len(df_poly)-1):
            dx = df_poly["E"][i+1] - df_poly["E"][i]
            dy = df_poly["N"][i+1] - df_poly["N"][i]
            distances.append(math.sqrt(dx**2 + dy**2))
            bearings.append((math.degrees(math.atan2(dx, dy)) + 360) % 360)

        poly_coords_xy = list(zip(df["E"], df["N"]))
        polygon_geom = Polygon(poly_coords_xy)
        area = polygon_geom.area
        perimeter = sum(distances)

        # Info Ringkas di Streamlit UI
        c1, c2 = st.columns(2)
        c1.metric("Polygon Area", f"{area:,.2f} m²")
        c2.metric("Polygon Perimeter", f"{perimeter:,.2f} m")

        # Create Map
        m = folium.Map(location=[df["Lat"].mean(), df["Lon"].mean()], zoom_start=20, control_scale=True)
        folium.TileLayer("OpenStreetMap", name="Street Map").add_to(m)
        folium.TileLayer(tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", attr="Google", name="Google Satellite", max_zoom=22).add_to(m)

        polygon_layer = folium.FeatureGroup(name="Traverse Polygon").add_to(m)
        station_layer = folium.FeatureGroup(name="Stations").add_to(m)
        dimension_layer = folium.FeatureGroup(name="Traverse Dimensions").add_to(m)

        # ====== POLYGON DENGAN INFO CLIK ======
        polygon_coords = list(zip(df["Lat"], df["Lon"]))
        folium.Polygon(
            locations=polygon_coords,
            color="#3388ff", weight=3, fill=True, fill_opacity=0.2,
            popup=folium.Popup(f"<b>INFO LOT</b><br>Keluasan: {area:,.2f} m²<br>Perimeter: {perimeter:,.2f} m", max_width=200)
        ).add_to(polygon_layer)

        # ====== BARU: AREA LABEL DI TENGAH POLIGON ======
        # Mencari titik tengah (Centroid) untuk letak teks AREA
        centroid = polygon_geom.centroid
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

        # ====== STATIONS DENGAN INFO COORDINATE ======
        for _, row in df.iterrows():
            popup_html = f"""
            <div style='font-family: Arial; font-size: 10pt;'>
                <b>Station: {row['STN']}</b><br>
                <hr>
                <b>Johor Grid (E, N):</b><br>
                E: {row['E']:.3f}<br>
                N: {row['N']:.3f}<br>
                <br>
                <b>WGS84 (Lat, Lon):</b><br>
                Lat: {row['Lat']:.7f}<br>
                Lon: {row['Lon']:.7f}
            </div>
            """
            
            folium.CircleMarker(
                location=[row["Lat"], row["Lon"]],
                radius=marker_size, color="yellow", weight=1, fill=True, fill_color="red", fill_opacity=1,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"Klik untuk koordinat STN {row['STN']}"
            ).add_to(station_layer)

            folium.map.Marker(
                [row["Lat"], row["Lon"]],
                icon=folium.DivIcon(icon_anchor=(15, 0),
                html=f"""<div style="font-size: {stn_font_size}pt; color: {stn_color}; font-weight: bold; text-shadow: 2px 2px 2px black; pointer-events: none; white-space: nowrap;">{row['STN']}</div>""")
            ).add_to(station_layer)

        # ====== DIMENSIONS (BEARING & DISTANCE) ======
        for i in range(len(df_poly)-1):
            mid_lat, mid_lon = (df_poly["Lat"][i] + df_poly["Lat"][i+1]) / 2, (df_poly["Lon"][i] + df_poly["Lon"][i+1]) / 2
            label = f"{deg_to_dms(bearings[i])}<br>{distances[i]:.2f}m"
            folium.Marker(
                location=[mid_lat, mid_lon],
                icon=folium.DivIcon(html=f"""<div style="font-size: {dms_font_size}pt; color: {dms_color}; font-weight: bold; text-shadow: 1px 1px 2px black; text-align: center; pointer-events: none; width: 150px; margin-left: -75px;">{label}</div>""")
            ).add_to(dimension_layer)

        # Fit & Show
        m.fit_bounds(polygon_coords)
        folium.LayerControl(collapsed=False).add_to(m)
        st_folium(m, width=1100, height=700)

        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button("Download Converted CSV", csv_buffer.getvalue(), "converted.csv", "text/csv")
