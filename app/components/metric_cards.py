import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
from utils.i18n import translations

def render_metric_cards(df: pd.DataFrame, lang: str = 'id'):
    # Tarik kamus bahasa yang sesuai (default ke 'id' jika tidak ditemukan)
    t = translations.get(lang, translations['id'])
    
    if df.empty:
        # Peringatan kosong juga disesuaikan dengan bahasa (fallback ke Indonesia jika key tidak ada)
        peringatan = "Tidak ada data untuk kalkulasi metrik." if lang == 'id' else "No data available for metric calculation."
        st.warning(peringatan)
        return

    now = datetime.now(timezone.utc)
    
    # Kalkulasi Gempa Hari Ini (24 jam terakhir)
    one_day_ago = now - timedelta(days=1)
    total_hari_ini = len(df[df["datetime"] >= one_day_ago])

    # Kalkulasi Magnitudo Tertinggi Minggu Ini (7 hari terakhir)
    one_week_ago = now - timedelta(days=7)
    df_minggu_ini = df[df["datetime"] >= one_week_ago]
    max_mag_minggu_ini = df_minggu_ini["magnitude"].max() if not df_minggu_ini.empty else 0.0

    # Kalkulasi Total Gempa Dirasakan Bulan Ini (30 hari terakhir)
    one_month_ago = now - timedelta(days=30)
    df_bulan_ini = df[df["datetime"] >= one_month_ago]
    
    # Defensive check untuk kolom 'dirasakan'
    if "dirasakan" in df_bulan_ini.columns:
        total_dirasakan_bulan_ini = len(df_bulan_ini[df_bulan_ini["dirasakan"] != "-"])
    else:
        total_dirasakan_bulan_ini = 0

    # Setup akhiran kata (Kejadian vs Events) berdasarkan bahasa
    suffix_kejadian = "Kejadian" if lang == 'id' else "Events"

    # Render komponen visual ke dalam 3 kolom horizontal
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label=t["metric_today"], value=f"{total_hari_ini} {suffix_kejadian}")
    with col2:
        st.metric(label=t["metric_week"], value=f"{max_mag_minggu_ini} M")
    with col3:
        st.metric(label=t["metric_month"], value=f"{total_dirasakan_bulan_ini} {suffix_kejadian}")
