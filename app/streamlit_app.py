import streamlit as st
import pandas as pd
import plotly.express as px
from utils.sheets_connector import load_data
from components.metric_cards import render_metric_cards
from components.filters      import render_filters
from components.map_view     import render_map, get_marker_color

# 1. Konfigurasi Properti Browser Tab
st.set_page_config(
    page_title="Sistem Monitoring Gempa Bumi Indonesia",
    page_icon="🌏",
    layout="wide"
)

# 2. Perbaikan Narasi Sesuai Permintaan (Clean Data Copywriting)
st.title("🌏 Sistem Pemantauan Gempa Bumi Real-Time Indonesia")
st.markdown("""
**Sumber:** Data Terbuka BMKG  
*Data kejadian gempabumi yang terjadi di seluruh wilayah Indonesia. Terdapat 3 jenis data kejadian gempabumi, 
yaitu Gempabumi M 5.0+, Gempabumi Dirasakan, dan Gempabumi Berpotensi Tsunami.*
""")
st.markdown("---")

try:
    with st.spinner("Sinkronisasi data sedang berlangsung dari peladen Google Sheets..."):
        raw_df = load_data()
        
    if not raw_df.empty:
        # 3. Render Panel Filter di Sidebar
        filtered_df = render_filters(raw_df)
        
        # 4. Render Kartu Statistik Utama
        render_metric_cards(filtered_df)
        st.markdown("###")
        
        # 5. Logika Interaktivitas Klik Tabel -> Peta
        # Membuat penampung variabel koordinat terpilih di dalam session state Streamlit
        if "selected_coordinates" not in st.session_state:
            st.session_state.selected_coordinates = None

        # 6. TATA LETAK VERTIKAL: PETA DI ATAS (LEBAR PENUH)
        render_map(filtered_df, selected_coords=st.session_state.selected_coordinates)
        st.markdown("---")
        
        # 7. BAGIAN BAWAH: TABEL INTERAKTIF & GRAFIK (SIDE-BY-SIDE DI BAWAH PETA)
        bottom_left, bottom_right = st.columns([1, 1])
        
       with bottom_left:
            st.markdown("### 📋 Tabel Riwayat Aktivitas Seismik")
            st.caption("💡 *Klik baris pada tabel di bawah ini untuk mengunci dan menggeser peta langsung ke pusat gempa.*")
            
            display_cols = ["datetime", "magnitude", "depth_km", "region", "latitude", "longitude"]
            df_display = filtered_df[display_cols].copy()
            df_display["datetime"] = df_display["datetime"].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Eksekusi tabel interaktif versi Streamlit 1.35.0+
            selected_row = st.dataframe(
                df_display.rename(columns={
                    "datetime": "Waktu Kejadian (UTC)",
                    "magnitude": "Magnitudo (SR)",
                    "depth_km": "Kedalaman (Km)",
                    "region": "Lokasi Wilayah",
                    "latitude": "Lintang",
                    "longitude": "Bujur"
                }),
                use_container_width=True,
                height=400,
                on_select="rerun",
                selection_mode="single_row"
            )
            
            # KUNCI PERBAIKAN LOGIKA: Ekstraksi indeks baris secara defensif untuk Streamlit v1.35.0
            try:
                # Pola pembacaan indeks baris terpilih pada versi awal fitur dirilis
                selection_data = selected_row.get("selection", {}) if hasattr(selected_row, "get") else getattr(selected_row, "selection", {})
                rows_selected = selection_data.get("rows", []) if isinstance(selection_data, dict) else getattr(selection_data, "rows", [])
                
                if len(rows_selected) > 0:
                    row_idx = rows_selected[0]
                    lat = float(df_display.iloc[row_idx]["latitude"])
                    lon = float(df_display.iloc[row_idx]["longitude"])
                    
                    # Amankan kondisi koordinat dalam session state
                    if st.session_state.selected_coordinates != (lat, lon):
                        st.session_state.selected_coordinates = (lat, lon)
                        st.rerun()
                else:
                    if st.session_state.selected_coordinates is not None:
                        st.session_state.selected_coordinates = None
                        st.rerun()
            except Exception as e:
                # Mencegah crash jika struktur objek internal dibaca berbeda oleh peladen
                pass
                # Reset koordinat jika klik dilepas
                if st.session_state.selected_coordinates is not None:
                    st.session_state.selected_coordinates = None
                    st.rerun()

        with bottom_right:
            st.markdown("### 📊 Analisis Grafis Seismik")
            
            # Membuat dua tab grafik agar tampilan ringkas dan rapi
            tab1, tab2 = st.tabs(["📈 Tren Harian", "🧪 Korelasi Kedalaman"])
            
            with tab1:
                if not filtered_df.empty:
                    # Menghitung frekuensi gempa per tanggal kejadian
                    filtered_df["tanggal"] = filtered_df["datetime"].dt.date
                    trend_df = filtered_df.groupby("tanggal").size().reset_index(name="Jumlah Kejadian")
                    
                    fig_trend = px.bar(
                        trend_df, x="tanggal", y="Jumlah Kejadian",
                        labels={"tanggal": "Tanggal Kejadian", "Jumlah Kejadian": "Frekuensi Gempa"},
                        color_discrete_sequence=["#1B6B71"]
                    )
                    fig_trend.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=320)
                    st.plotly_chart(fig_trend, use_container_width=True)
                else:
                    st.info("Tidak ada data untuk grafik tren.")
                    
            with tab2:
                if not filtered_df.empty:
                    # Membuat Scatter plot korelasi antara magnitudo dengan kedalaman pusat gempa
                    fig_scatter = px.scatter(
                        filtered_df, x="magnitude", y="depth_km",
                        color="magnitude",
                        labels={"magnitude": "Magnitudo (SR)", "depth_km": "Kedalaman (Km)"},
                        color_continuous_scale=["#2E7D32", "#F57C00", "#D32F2F"],
                        hover_name="region"
                    )
                    fig_scatter.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=320)
                    # Membalik sumbu Y agar kedalaman semakin ke bawah semakin besar angkanya
                    fig_scatter.update_yaxes(autorange="reverse")
                    st.plotly_chart(fig_scatter, use_container_width=True)
                else:
                    st.info("Tidak ada data untuk grafik korelasi.")
                    
except Exception as e:
    st.error(f"Sistem gagal menginisialisasi antarmuka web app: {e}")
