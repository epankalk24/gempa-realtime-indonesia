import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def render_metric_cards(df: pd.DataFrame):
    """
    Menampilkan visualisasi ringkasan statistik gempa bumi menggunakan st.metric()
    """
    if df.empty:
        st.warning("Tidak ada data untuk kalkulasi metrik.")
        return

    # Kalkulasi Gempa Hari Ini (24 jam terakhir)
    now = datetime.now()
    one_day_ago = now - timedelta(days=1)
    total_hari_ini = len(df[df["datetime"] >= one_day_ago])

    # Kalkulasi Magnitudo Tertinggi Minggu Ini (7 hari terakhir)
    one_week_ago = now - timedelta(days=7)
    df_minggu_ini = df[df["datetime"] >= one_week_ago]
    max_mag_minggu_ini = df_minggu_ini["magnitude"].max() if not df_minggu_ini.empty else 0.0

    # Kalkulasi Total Gempa Dirasakan Bulan Ini (30 hari terakhir)
    one_month_ago = now - timedelta(days=30)
    df_bulan_ini = df[df["datetime"] >= one_month_ago]
    total_dirasakan_bulan_ini = len(df_bulan_ini[df_bulan_ini["source_endpoint"] == "bmkg_tews_dirasakan"])

    # Render komponen visual ke dalam 3 kolom horizontal
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="📊 Total Gempa (24 Jam Terakhir)", value=f"{total_hari_ini} Kejadian")
    with col2:
        st.metric(label="💥 Magnitudo Tertinggi (7 Hari Terakhir)", value=f"{max_mag_minggu_ini} SR")
    with col3:
        st.metric(label="🏠 Gempa Dirasakan (30 Hari Terakhir)", value=f"{total_dirasakan_bulan_ini} Laporan")
