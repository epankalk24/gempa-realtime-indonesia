import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import pandas as pd

def get_marker_color(magnitude: float) -> str:
    """Menentukan warna berdasarkan kekuatan magnitudo gempa (Intuitive Hazard Color)."""
    if magnitude < 4.0:
        return "#2E7D32"  # Hijau (Kecil)
    elif magnitude < 5.5:
        return "#F57C00"  # Oren (Menengah)
    else:
        return "#D32F2F"  # Merah (Tinggi)

def render_map(df: pd.DataFrame, selected_coords=None):
    """
    Merender peta spasial interaktif dengan ukuran penuh.
    Jika selected_coords (lat, lon) dikirim dari tabel, peta akan otomatis berpusat di titik tersebut.
    """
    st.markdown("### 🗺️ Peta Distribusi Episentrum Gempa")
    
    # Logika penentuan pusat peta (Center Lokasi)
    if selected_coords:
        map_center = selected_coords
        zoom_level = 8  # Zoom-in langsung ke lokasi gempa yang diklik
    else:
        map_center = [-2.5, 118.0]  # Pusat default Indonesia
        zoom_level = 5

    # Inisialisasi peta dengan lebar penuh (Full-Width)
    m = folium.Map(location=map_center, zoom_start=zoom_level, tiles="CartoDB positron", prefer_canvas=True)
    marker_cluster = MarkerCluster().add_to(m)

    if df.empty:
        st.info("Tidak ada data koordinat yang memenuhi kriteria filter.")
        st_folium(m, width="100%", height=500, returned_objects=[])
        return

    for _, row in df.iterrows():
        mag = row["magnitude"]
        color_code = get_marker_color(mag)
        radius_size = max(mag * 3.5, 10)  # Memastikan lingkaran terkecil tetap terlihat jelas

        popup_html = f"""
        <div style="font-family: Arial, sans-serif; font-size: 12px; width: 220px;">
            <h4 style="margin: 0 0 5px 0; color: {color_code};">Gempa {mag} SR</h4>
            <b>Waktu (UTC):</b> {row['datetime'].strftime('%Y-%m-%d %H:%M:%S')}<br>
            <b>Kedalaman:</b> {row['depth_km']} Km<br>
            <b>Lokasi:</b> {row['region']}
        </div>
        """
        
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=radius_size,
            popup=folium.Popup(popup_html, max_width=250),
            color=color_code,
            fill=True,
            fill_color=color_code,
            fill_opacity=0.6,
            weight=1.5
        ).add_to(marker_cluster)

    # Tambahkan penanda khusus berwarna biru jika pengguna memilih gempa dari tabel
    if selected_coords:
        folium.Marker(
            location=selected_coords,
            icon=folium.Icon(color="blue", icon="info-sign"),
            tooltip="Lokasi Gempa yang Anda Pilih"
        ).add_to(m)

    # Render peta dengan width="100%" agar memenuhi layar
    st_folium(m, width="100%", height=500, key=f"map_{selected_coords}", returned_objects=[])
