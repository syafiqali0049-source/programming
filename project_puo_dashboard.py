import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from pyproj import Transformer
from shapely.geometry import Polygon, mapping
import math
import io
import json

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

# --- HEADER DENGAN LOGO ---
head_col1, head_col2 = st.columns([1, 5])
with head_col1:
    try:
        st.image("logo poli.jpeg", width=150)
    except:
        pass
with head_col2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.title("GIS Polygon Dashboard (Johor Grid → Google Satellite)")

# --- SIDEBAR (TETAPAN PAPARAN) ---
st.sidebar.header("Tetapan Paparan (Indication)")
stn_font_size = st.sidebar.slider("Saiz Font Station (STN)", 8, 20, 10)
dms_font_size = st.sidebar.slider("Saiz Font Bearing/Jarak (DMS)", 6, 16, 8)
marker_size = st.sidebar.slider("Saiz Marker Station", 2, 12, 6)
stn_color = st.sidebar.color_picker("Warna Font Station", "#FFFFFF")
dms_color = st.sidebar.color_picker("Warna Font DMS", "#00FF00")

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
        # Pemprosesan Data
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

        # ====== BAHAGIAN MUAT TURUN DI SIDEBAR ======
        st.sidebar.markdown("---")
        st.sidebar.header("📥 Muat Turun Data")
        
        # 1. Download CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.sidebar.download_button(
            label="📊 Download CSV",
            data=csv_buffer.getvalue(),
            file_name="converted_coordinates.csv",
            mime="text/csv",
            use_container_width=True
        )

        # 2. Download GeoJSON
        wgs_poly_coords = list(zip(df["Lon"], df["Lat"]))
        wgs_polygon_geom = Polygon(wgs_poly_coords)
        geojson_data = {
            "type": "FeatureCollection",
            "features": [{"type": "Feature", "geometry": mapping(wgs_polygon_geom), "properties": {"area_m2": round(area, 2)}}]
        }
        for _, row in df.iterrows():
            geojson_data["features"].append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [row["Lon"], row["Lat"]]},
                "properties": {"stn": row["STN"]}
            })
        
        geojson_string = json.dumps(geojson_data)
        st.sidebar.download_button(
            label="🌍 Download GeoJSON",
            data=geojson_string,
            file_name="traverse_lot.geojson",
            mime="application/json",
            use_container_width=True
        )

        # Peta Utama
        c1, c2 = st.columns(2)
        c1.metric("Polygon Area", f"{area:,.2f} m²")
        c2.metric("Polygon Perimeter", f"{perimeter:,.2f} m")

        m = folium.Map(location=[df["Lat"].mean(), df["Lon"].mean()], zoom_start=20)
        folium.TileLayer(tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", attr="Google", name="Google Satellite", max_zoom=22).add_to(m)

        # Layers (Polygon, Station, Dimensions)
        # ... (Kod lukisan peta sama seperti sebelum ini) ...
        # (Disebabkan ruang, saya ringkaskan, pastikan kod lukisan dikekalkan)
        
        # Area Label Gold
        centroid = polygon_geom.centroid
        cen_lon, cen_lat = transformer.transform(centroid.x, centroid.y)
        folium.Marker([cen_lat, cen_lon], icon=folium.DivIcon(html=f'<div style="font-size: 14pt; font-weight: bold; color: #FFD700; text-shadow: 2px 2px 4px black; text-align: center; width: 200px; margin-left: -100px;">AREA<br>{area:,.2f} m²</div>')).add_to(m)

        st_folium(m, width=1100, height=700)

# --- BUTANG LOG KELUAR DI BAWAH SIDEBAR ---
st.sidebar.markdown("---")
if st.sidebar.button("Log Keluar"):
    logout()
