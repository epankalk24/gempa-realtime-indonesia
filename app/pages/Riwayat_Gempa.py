import streamlit as st
import pandas as pd
from utils.sheets_connector import load_filtered_data, load_raw_data

st.set_page_config(page_title="Riwayat Gempa", page_icon="📚", layout="wide")

st.title("📚 Cari & Unduh Data Gempa")
st.markdown("Cari gempa berdasarkan tanggal atau rentang waktu, lalu unduh datanya")

col_kontrol, col_ruang = st.columns([1, 2])
with col_kontrol:
    sumber_data = st.radio(
        "Tampilkan data dari:",
        options=["30 Hari Terakhir", "Semua Riwayat"]
    )

with st.spinner('Menghubungkan ke pangkalan data...'):
    if sumber_data == "30 Hari Terakhir":
        df = load_filtered_data()
    else:
        df = load_raw_data()

if df.empty:
    st.warning("Data belum tersedia di pangkalan data ini.")
    st.stop()

df['tanggal_murni'] = df['datetime'].dt.date
st.markdown("---")
st.subheader("Pilih Rentang Tanggal")

tanggal_min = df['tanggal_murni'].min()
tanggal_max = df['tanggal_murni'].max()

# label_visibility="collapsed" menyembunyikan label bawaan agar tidak redundan
rentang_tanggal = st.date_input(
    "Rentang Tanggal",
    value=(tanggal_min, tanggal_max),
    min_value=tanggal_min,
    max_value=tanggal_max,
    label_visibility="collapsed" 
)

if len(rentang_tanggal) == 2:
    mulai, selesai = rentang_tanggal
    df_tampil = df[(df['tanggal_murni'] >= mulai) & (df['tanggal_murni'] <= selesai)]
else:
    df_tampil = df

st.metric("Ditemukan", f"{len(df_tampil)} Gempa")

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
