import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import pandas as pd

def get_marker_color(magnitude: float) -> str:
    if magnitude < 4.0:
        return "#2E7D32"
    elif magnitude < 5.5:
        return "#F57C00"
    else:
        return "#D32F2F"

def render_map(df: pd.DataFrame, selected_coords=None):
    st.markdown("### 🗺️ Peta Gempa Terkini")
    
    if selected_coords:
        map_center = selected_coords
        zoom_level = 8 
    else:
        map_center = [-2.5, 118.0]
        zoom_level = 5

    m = folium.Map(location=map_center, zoom_start=zoom_level, tiles="CartoDB positron", prefer_canvas=True)
    marker_cluster = MarkerCluster().add_to(m)

    if df.empty:
        st_folium(m, width="100%", height=500, returned_objects=[])
        return

    for _, row in df.iterrows():
        mag = row["magnitude"]
        color_code = get_marker_color(mag)
        radius_size = max(mag * 3.5, 10)

        # Ubah satuan SR menjadi M di dalam H4 Popup
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; font-size: 12px; width: 220px;">
            <h4 style="margin: 0 0 5px 0; color: {color_code};">Gempa {mag} M</h4>
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

    if selected_coords:
        folium.Marker(
            location=selected_coords,
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

    st_folium(m, width="100%", height=500, returned_objects=[])
