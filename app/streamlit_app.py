"""
streamlit_app.py
----------------
Dasbor operasional utama. Hanya memuat data 30 hari terakhir (Hot Storage).
Difokuskan pada metrik instan, filter spasial, dan peta interaktif folium.
"""

import streamlit as st
from datetime import timedelta
import pandas as pd

from utils.sheets_connector import load_filtered_data
from components.metric_cards import render_metric_cards
from components.filters      import render_filters
from components.map_view     import render_map

# 1. Konfigurasi Properti Browser Tab
st.set_page_config(
    page_title="Sistem Monitoring Gempa Bumi Indonesia",
    page_icon="🌏",
    layout="wide"
)

st.title("🌏 Dasbor Pemantauan Gempa Bumi Real-Time")
st.markdown("""
**Sumber:** Data Terbuka BMKG (Terintegrasi secara otomatis)  
*Dasbor ini menampilkan aktivitas seismik mutakhir di seluruh wilayah Indonesia. 
Data operasional diperbarui secara berkala melalui pipeline serverless.*
""")
st.markdown("---")

# 2. Pemuatan Data Operasional Laten Rendah
with st.spinner("Sinkronisasi pangkalan data operasional..."):
    raw_df = load_filtered_data()

if raw_df.empty:
    st.warning("Menunggu masuknya data dari API BMKG. Silakan muat ulang halaman beberapa saat lagi.")
    st.stop()

# 3. Eksekusi Modul Antarmuka
filtered_df = render_filters(raw_df)
render_metric_cards(filtered_df)

st.markdown("###")

# 4. Render Peta Spasial
# Logika interaktivitas klik tabel dinonaktifkan di halaman utama untuk menjaga kecepatan render
render_map(filtered_df)

# 5. Tabel Ringkas Aktivitas Seismik (7 Hari Terakhir)
st.markdown("---")
st.subheader("📋 Log Aktivitas Seismik (7 Hari Terakhir)")

batas_waktu_7_hari = raw_df['datetime'].max() - timedelta(days=7)
df_7_hari = filtered_df[filtered_df['datetime'] >= batas_waktu_7_hari]

# Membersihkan tampilan tabel dari ID sistem agar scannable
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
