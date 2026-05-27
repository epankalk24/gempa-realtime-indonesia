import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import pandas as pd

def render_map(df: pd.DataFrame):
    """
    Merender peta spasial interaktif menggunakan Folium dengan klasterisasi titik.
    """
    st.subheader("🗺️ Peta Distribusi Episentrum Gempa")
    
    # Koordinat pusat awal peta terkunci di tengah kepulauan Indonesia
    indonesia_center = [-2.5, 118.0]
    
    # Inisialisasi peta dasar dengan tema CartoDB Positron (Minimalis & Elegan)
    m = folium.Map(location=indonesia_center, zoom_start=5, tiles="CartoDB positron", prefer_canvas=True)
    
    # Mengaktifkan fungsi Marker Cluster agar titik tidak bertumpuk berantakan
    marker_cluster = MarkerCluster().add_to(m)

    if df.empty:
        st.info("Tidak ada data koordinat yang memenuhi kriteria filter untuk ditampilkan di peta.")
        # Tetap tampilkan peta kosong Indonesia
        st_folium(m, width=700, height=450, returned_objects=[])
        return

    # Loop membaca baris data spasial untuk plotting
    for _, row in df.iterrows():
        # Aturan Warna Konsep Minimalis: < 5.0 Terracotta, >= 5.0 Deep Teal
        mag = row["magnitude"]
        color_code = "#C4533E" if mag < 5.0 else "#1B6B71"
        
        # Formula ukuran radius lingkaran proporsional terhadap magnitudo
        radius_size = mag * 3

        # Penyusunan jendela pop-up informasi yang rapi saat titik diklik
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; font-size: 12px; width: 200px;">
            <h4 style="margin: 0 0 5px 0; color: {color_code};">Gempa {mag} SR</h4>
            <b>Waktu:</b> {row['datetime'].strftime('%Y-%m-%d %H:%M:%S')}<br>
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

    # Tampilkan komponen peta spasial ke halaman web Streamlit
    st_folium(m, width=700, height=450, returned_objects=[])
