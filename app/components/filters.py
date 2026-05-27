import streamlit as st
import pandas as pd

def render_filters(df: pd.DataFrame):
    """
    Menampilkan filter interaktif di bilah samping (sidebar) dan mengembalikan DataFrame yang tersaring.
    """
    st.sidebar.header("🎛️ Panel Penyaringan Data")
    
    if df.empty:
        return df

    # Filter 1: Slider Skala Magnitudo (Batas bawah minimum dan maksimum otomatis dari data)
    min_mag_val = float(df["magnitude"].min())
    max_mag_val = float(df["magnitude"].max())
    
    # Validasi jika nilai min dan max sama untuk menghindari crash sistem
    if min_mag_val == max_mag_val:
        min_mag_val = 0.0
        
    selected_mag = st.sidebar.slider(
        "Pilih Rentang Magnitudo (SR):",
        min_value=0.0,
        max_value=10.0,
        value=(min_mag_val, max_mag_val),
        step=0.1
    )

    # Filter 2: Slider Kedalaman Gempa (Dalam satuan Kilometer)
    max_depth = int(df["depth_km"].max()) if not df["depth_km"].empty else 700
    selected_depth = st.sidebar.slider(
        "Pilih Kedalaman Maksimum (Km):",
        min_value=0,
        max_value=max_depth if max_depth > 0 else 700,
        value=max_depth
    )

    # Filter 3: Dropdown Kategori Sumber Data
    categories = ["Semua Kategori", "Gempa M 5.0+", "Gempa Dirasakan / Berpotensi Tsunami"]
    selected_cat = st.sidebar.selectbox("Kategori Klasifikasi Gempa:", categories)

    # Proses Logika Penyaringan Data Berdasarkan Pilihan Komponen UI
    filtered_df = df[
        (df["magnitude"] >= selected_mag[0]) & 
        (df["magnitude"] <= selected_mag[1]) &
        (df["depth_km"] <= selected_depth)
    ]

    if selected_cat == "Gempa M 5.0+":
        filtered_df = filtered_df[filtered_df["source_endpoint"].isin(["bmkg_tews_m5", "bmkg_tews_autogempa"])]
    elif selected_cat == "Gempa Dirasakan / Berpotensi Tsunami":
        filtered_df = filtered_df[filtered_df["source_endpoint"] == "bmkg_tews_dirasakan"]

    return filtered_df
