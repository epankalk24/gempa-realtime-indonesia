"""
1_Riwayat_Lengkap.py
--------------------
Halaman dedikasi untuk penelusuran tabular dan pengunduhan dataset murni.
Memiliki opsi pemanggilan 'Cold Storage' (raw_data).
"""

import streamlit as st
import pandas as pd
from utils.sheets_connector import load_filtered_data, load_raw_data

st.set_page_config(page_title="Riwayat Lengkap Seismik", page_icon="📚", layout="wide")

st.title("📚 Eksplorasi Riwayat Data Seismik")
st.markdown("Gunakan panel ini untuk menelusuri atau mengunduh dataset aktivitas gempa bumi secara spesifik.")

# 1. Kontrol Seleksi Basis Data
col_kontrol, col_ruang = st.columns([1, 2])
with col_kontrol:
    sumber_data = st.radio(
        "Pilih Sumber Basis Data:",
        options=["30 Hari Terakhir (Operasional)", "Seluruh Riwayat (Data Mentah)"],
        help="Data 30 hari memuat lebih cepat. Seluruh riwayat akan menarik puluhan ribu baris data dari arsip."
    )

# 2. Pemuatan Data Berdasarkan Pilihan
with st.spinner('Menghubungkan ke pangkalan data...'):
    if sumber_data == "30 Hari Terakhir (Operasional)":
        df = load_filtered_data()
    else:
        df = load_raw_data()

if df.empty:
    st.warning("Data belum tersedia di pangkalan data ini.")
    st.stop()

# 3. Mekanisme Penyaringan Berbasis Tanggal
df['tanggal_murni'] = df['datetime'].dt.date
st.markdown("---")
st.subheader("Filter Spesifik Rentang Waktu")

tanggal_min = df['tanggal_murni'].min()
tanggal_max = df['tanggal_murni'].max()

rentang_tanggal = st.date_input(
    "Tentukan Rentang Tanggal",
    value=(tanggal_min, tanggal_max),
    min_value=tanggal_min,
    max_value=tanggal_max
)

if len(rentang_tanggal) == 2:
    mulai, selesai = rentang_tanggal
    df_tampil = df[(df['tanggal_murni'] >= mulai) & (df['tanggal_murni'] <= selesai)]
else:
    df_tampil = df

st.metric("Total Kejadian Ditemukan", f"{len(df_tampil)} Gempa")

# 4. Rendering Tabel & Ekspor CSV
st.dataframe(
    df_tampil.drop(columns=['tanggal_murni']), 
    column_config={"event_id": None},
    use_container_width=True,
    hide_index=True
)

csv_data = df_tampil.drop(columns=['tanggal_murni']).to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Unduh Dataset (CSV)",
    data=csv_data,
    file_name='dataset_gempa_bmkg.csv',
    mime='text/csv',
)
