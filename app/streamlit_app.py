import streamlit as st
import pandas as pd
from utils.sheets_connector import load_data
from components.metric_cards import render_metric_cards
from components.filters      import render_filters
from components.map_view     import render_map

# 1. Konfigurasi Dasar Properti Peramban Web (Browser Tab)
st.set_page_config(
    page_title="Sistem Monitoring Gempa Bumi Indonesia",
    page_icon="🌏",
    layout="wide"
)

# 2. Judul Utama Dashboard dan Deskripsi
st.title("🌏 Sistem Pemantauan Gempa Bumi Real-Time Indonesia")
st.caption(
    "Data bersumber langsung dari API Terbuka BMKG TEWS (Tsunami Early Warning System) "
    "dan diperbarui secara otomatis setiap jam melalui arsitektur pipa data GitHub Actions."
)
st.markdown("---")

# 3. Proses Pengambilan Data Historis dari Google Sheets
try:
    with st.spinner("Sinkronisasi data sedang berlangsung dari peladen Google Sheets..."):
        raw_df = load_data()
        
    if not raw_df.empty:
        # 4. Merender Komponen Panel Samping Filter
        filtered_df = render_filters(raw_df)
        
        # 5. Merender Komponen Kartu Statistik Utama
        render_metric_cards(filtered_df)
        st.markdown("###")
        
        # 6. Membagi Layout Utama Menjadi Peta (Kiri) dan Tabel (Kanan)
        left_col, right_col = st.columns([3, 2])
        
        with left_col:
            render_map(filtered_df)
            
        with right_col:
            st.subheader("📋 Tabel Riwayat Aktivitas Seismik")
            # Menampilkan potongan tabel data yang bersih dan dapat diunduh
            display_cols = ["datetime", "magnitude", "depth_km", "region"]
            st.dataframe(
                filtered_df[display_cols].rename(columns={
                    "datetime": "Waktu Kejadian",
                    "magnitude": "Magnitudo (SR)",
                    "depth_km": "Kedalaman (Km)",
                    "region": "Lokasi Wilayah"
                }),
                use_container_width=True,
                height=450
            )
            
    else:
        st.error("Database kosong. Hubungkan pipa data Actions Anda terlebih dahulu.")
except Exception as e:
    st.error(f"Sistem gagal menginisialisasi antarmuka web app: {e}")
