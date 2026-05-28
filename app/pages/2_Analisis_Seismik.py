"""
2_Analisis_Seismik.py
---------------------
Pusat analitik visual. Membandingkan data operasional mikro (30 Hari)
dengan tren makro (archive_summary bulanan).
"""

import streamlit as st
import plotly.express as px
from utils.sheets_connector import load_filtered_data, load_archive_summary

st.set_page_config(page_title="Analisis Grafis Seismik", page_icon="📈", layout="wide")

st.title("📈 Analisis Tren & Distribusi Seismik")

df_filtered = load_filtered_data()
df_archive = load_archive_summary()

# ==========================================
# SEGMEN 1: DINAMIKA OPERASIONAL (MIKRO)
# ==========================================
st.header("1. Dinamika Mikro (30 Hari Terakhir)")

if not df_filtered.empty:
    col_kiri, col_kanan = st.columns(2)
    
    with col_kiri:
        st.subheader("Frekuensi Gempa Harian")
        df_filtered['tanggal_murni'] = df_filtered['datetime'].dt.date
        frekuensi_harian = df_filtered.groupby('tanggal_murni').size().reset_index(name='Jumlah Kejadian')
        
        fig_bar = px.bar(
            frekuensi_harian, x='tanggal_murni', y='Jumlah Kejadian',
            labels={"tanggal_murni": "Tanggal", "Jumlah Kejadian": "Frekuensi"},
            color_discrete_sequence=["#1B6B71"]
        )
        fig_bar.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=400)
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col_kanan:
        st.subheader("Distribusi Magnitudo vs Kedalaman")
        fig_scatter = px.scatter(
            df_filtered, x="magnitude", y="depth_km",
            color="magnitude",
            labels={"magnitude": "Magnitudo (SR)", "depth_km": "Kedalaman (Km)"},
            color_continuous_scale=["#2E7D32", "#F57C00", "#D32F2F"],
            hover_name="region"
        )
        # Sumbu Y dibalik sesuai standar plot seismologi (kedalaman turun ke bawah)
        fig_scatter.update_yaxes(autorange="reversed")
        fig_scatter.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=400)
        st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.info("Pangkalan data operasional belum memiliki entri yang cukup untuk diplot.")

st.markdown("---")

# ==========================================
# SEGMEN 2: TREN MAKRO HISTORIS (MACRO)
# ==========================================
st.header("2. Analisis Tren Makro Jangka Panjang")

# Defensive Programming: Mencegah KeyError jika arsip belum terbentuk oleh GAS
if not df_archive.empty and "Tahun_Minggu" in df_archive.columns:
    
    tren_waktu = df_archive.groupby('Tahun_Minggu')['Total_Kejadian'].sum().reset_index()
    
    st.subheader("Agregasi Frekuensi Gempa Nasional (Mingguan)")
    fig_line = px.line(
        tren_waktu, x='Tahun_Minggu', y='Total_Kejadian',
        markers=True,
        labels={"Tahun_Minggu": "Minggu ISO", "Total_Kejadian": "Total Kejadian"},
        color_discrete_sequence=["#C4533E"]
    )
    st.plotly_chart(fig_line, use_container_width=True)
    
else:
    # Elegan fallback explanation
    st.info(
        "💡 **Data Arsip Sedang Dalam Fase Inkubasi.**\n\n"
        "Mesin diagregasi Google Apps Script (GAS) dirancang untuk memproses data berumur lebih dari 30 hari. "
        "Grafik tren jangka panjang akan otomatis muncul di sini setelah *cron job* GAS mingguan pertama Anda tereksekusi."
    )
