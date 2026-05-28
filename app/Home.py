import streamlit as st
from datetime import timedelta
import pandas as pd

from utils.sheets_connector import load_filtered_data
from components.metric_cards import render_metric_cards
from components.filters      import render_filters
from components.map_view     import render_map

st.set_page_config(
    page_title="Pantau Gempa Indonesia",
    page_icon="🌏",
    layout="wide"
)

st.title("🌏 Pantau Gempa Indonesia")
st.markdown("""
**Sumber:** Data Terbuka BMKG  
*Data kejadian gempabumi yang terjadi di seluruh wilayah Indonesia. Terdapat 3 jenis data kejadian gempabumi, yaitu Gempabumi M 5.0+, Gempabumi Dirasakan, dan Gempabumi Berpotensi Tsunami.*
""")
st.markdown("---")

with st.spinner("Sinkronisasi pangkalan data..."):
    raw_df = load_filtered_data()

if raw_df.empty:
    st.warning("Menunggu masuknya data dari API BMKG. Silakan muat ulang halaman beberapa saat lagi.")
    st.stop()

filtered_df = render_filters(raw_df)
render_metric_cards(filtered_df)

st.markdown("###")
render_map(filtered_df)

st.markdown("---")
st.subheader("📋 Gempa 7 Hari Terakhir")

batas_waktu_7_hari = raw_df['datetime'].max() - timedelta(days=7)
df_7_hari = filtered_df[filtered_df['datetime'] >= batas_waktu_7_hari]

st.dataframe(
    df_7_hari,
    column_config={
        "event_id": None, 
        "ingested_at": None,
        "potensi": st.column_config.TextColumn("Potensi Tsunami"),
        "dirasakan": st.column_config.TextColumn("Skala Dirasakan")
    },
    use_container_width=True,
    hide_index=True
)
