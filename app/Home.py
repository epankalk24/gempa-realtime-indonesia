import streamlit as st
from datetime import timedelta
import pandas as pd

from utils.sheets_connector import load_filtered_data
from utils.i18n import translations
from components.metric_cards import render_metric_cards
from components.filters import render_filters
from components.map_view import render_map

st.set_page_config(
    page_title="Pantau Gempa Indonesia",
    page_icon="🌏",
    layout="wide"
)

# ==========================================
# MANAJEMEN STATE BAHASA 
# (Wajib dideklarasikan di sini sebelum komponen lain membaca st.session_state.lang)
# ==========================================
if 'lang' not in st.session_state:
    st.session_state.lang = 'id'

# Toggle radio button di sidebar
pilihan_bahasa = st.sidebar.radio(
    translations[st.session_state.lang]["lang_label"], 
    ['id', 'en'], 
    index=0 if st.session_state.lang == 'id' else 1
)
st.session_state.lang = pilihan_bahasa

# Inisialisasi variabel 't' sebagai proksi kamus bahasa aktif
t = translations[st.session_state.lang]
# ==========================================

st.title(t["home_title"])
st.markdown(t["home_desc"])
st.markdown("---")

with st.spinner(t["home_wait"]):
    raw_df = load_filtered_data()

if raw_df.empty:
    st.warning(t["home_wait"])
    st.stop()

# Eksekusi komponen dengan menyuntikkan parameter bahasa aktif
filtered_df = render_filters(raw_df, lang=st.session_state.lang)
render_metric_cards(filtered_df, lang=st.session_state.lang)

st.markdown("###")
render_map(filtered_df)

st.markdown("---")
st.subheader(t["home_table"])

batas_waktu_7_hari = raw_df['datetime'].max() - timedelta(days=7)
df_7_hari = filtered_df[filtered_df['datetime'] >= batas_waktu_7_hari]

st.dataframe(
    df_7_hari,
    column_config={
        "event_id": None, 
        "ingested_at": None,
        "potensi": st.column_config.TextColumn("Potensi Tsunami" if st.session_state.lang == 'id' else "Tsunami Potential"),
        "dirasakan": st.column_config.TextColumn("Skala Dirasakan" if st.session_state.lang == 'id' else "Felt Scale")
    },
    use_container_width=True,
    hide_index=True
)
