import streamlit as st
import pandas as pd
from utils.i18n import translations

def render_filters(df: pd.DataFrame, lang: str = 'id'):
    t = translations.get(lang, translations['id'])
    
    st.sidebar.header(t["filter_title"])
    
    if df.empty:
        return df

    min_mag_val = float(df["magnitude"].min())
    max_mag_val = float(df["magnitude"].max())
    if min_mag_val == max_mag_val:
        min_mag_val = 0.0
        
    # [PERBAIKAN] Penambahan parameter 'key' yang unik secara global
    selected_mag = st.sidebar.slider(
        t["filter_mag"],
        min_value=0.0,
        max_value=10.0,
        value=(min_mag_val, max_mag_val),
        step=0.1,
        key="global_mag_slider" 
    )

    max_depth = int(df["depth_km"].max()) if not df["depth_km"].empty else 700
    
    # [PERBAIKAN] Penambahan parameter 'key'
    selected_depth = st.sidebar.slider(
        t["filter_depth"],
        min_value=0,
        max_value=max_depth if max_depth > 0 else 700,
        value=max_depth,
        key="global_depth_slider"
    )

    categories = [t["cat_all"], t["cat_felt"]]
    
    # [PERBAIKAN] Penambahan parameter 'key'
    selected_cat = st.sidebar.selectbox(
        t["filter_cat"], 
        categories,
        key="global_category_selector"
    )

    mask = (df["magnitude"] >= selected_mag[0]) & \
           (df["magnitude"] <= selected_mag[1]) & \
           (df["depth_km"] <= selected_depth)
           
    filtered_df = df[mask]

    if selected_cat == t["cat_felt"]:
        kondisi_dirasakan = (df["dirasakan"] != "-") if "dirasakan" in df.columns else False
        kondisi_potensi = (df["potensi"].str.contains("Tsunami", case=False, na=False)) if "potensi" in df.columns else False
        filtered_df = filtered_df[kondisi_dirasakan | kondisi_potensi]

    st.sidebar.markdown("---")
    
    caption_text = f"Menampilkan **{len(filtered_df)}** dari {len(df)} kejadian." if lang == 'id' else f"Showing **{len(filtered_df)}** of {len(df)} events."
    st.sidebar.caption(caption_text)
    
    return filtered_df
