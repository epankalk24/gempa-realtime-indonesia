import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone

def render_metric_cards(df: pd.DataFrame):
    if df.empty:
        st.warning("Tidak ada data untuk kalkulasi metrik.")
        return

    now = datetime.now(timezone.utc)
    
    # Kalkulasi
    one_day_ago = now - timedelta(days=1)
    total_hari_ini = len(df[df["datetime"] >= one_day_ago])

    one_week_ago = now - timedelta(days=7)
    df_minggu_ini = df[df["datetime"] >= one_week_ago]
    max_mag_minggu_ini = df_minggu_ini["magnitude"].max() if not df_minggu_ini.empty else 0.0

    one_month_ago = now - timedelta(days=30)
    df_bulan_ini = df[df["datetime"] >= one_month_ago]
    
    # Defensive check
    if "dirasakan" in df_bulan_ini.columns:
        total_dirasakan_bulan_ini = len(df_bulan_ini[df_bulan_ini["dirasakan"] != "-"])
    else:
        total_dirasakan_bulan_ini = 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Gempa Hari Ini", value=f"{total_hari_ini} Kejadian")
    with col2:
        # Mengubah SR menjadi M
        st.metric(label="Terkuat Minggu Ini", value=f"{max_mag_minggu_ini} M")
    with col3:
        st.metric(label="Dirasakan Bulan Ini", value=f"{total_dirasakan_bulan_ini} Kejadian")
