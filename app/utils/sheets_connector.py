import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

def get_gspread_client():
    """Fungsi internal untuk inisialisasi koneksi ke Google API."""
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def normalize_dataframe(df: pd.DataFrame, is_archive: bool = False) -> pd.DataFrame:
    """Membersihkan baris kosong, konversi datetime, dan mengurutkan data."""
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Hapus baris yang seluruhnya kosong (artefak Google Sheets)
    df = df.dropna(how='all')
    
    if not df.empty and not is_archive:
        if 'datetime' in df.columns:
            # Konversi string ISO ke objek datetime Pandas
            df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
        
        # Buang baris data yang format waktunya rusak agar peta tidak crash
        df = df.dropna(subset=['datetime'])
        
        # Mengurutkan dari kejadian paling terbaru
        df = df.sort_values(by="datetime", ascending=False)
        
    return df

@st.cache_data(ttl=300)
def load_filtered_data() -> pd.DataFrame:
    """Memuat data operasional (30 hari terakhir). Cache 5 menit."""
    try:
        client = get_gspread_client()
        sh = client.open_by_key(st.secrets["SPREADSHEET_ID"])
        worksheet = sh.worksheet("filtered_data")
        df = pd.DataFrame(worksheet.get_all_records())
        return normalize_dataframe(df)
    except Exception as e:
        st.error(f"Gagal memuat data operasional (filtered_data): {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_raw_data() -> pd.DataFrame:
    """Memuat seluruh data mentah. Cache 1 jam."""
    try:
        client = get_gspread_client()
        sh = client.open_by_key(st.secrets["SPREADSHEET_ID"])
        worksheet = sh.worksheet("raw_data")
        df = pd.DataFrame(worksheet.get_all_records())
        return normalize_dataframe(df)
    except Exception as e:
        st.error(f"Gagal memuat data mentah (raw_data): {e}")
        return pd.DataFrame()

@st.cache_data(ttl=86400)
def load_archive_summary() -> pd.DataFrame:
    """Memuat agregasi tren historis bulanan. Cache 24 jam."""
    try:
        client = get_gspread_client()
        sh = client.open_by_key(st.secrets["SPREADSHEET_ID"])
        worksheet = sh.worksheet("archive_summary")
        df = pd.DataFrame(worksheet.get_all_records())
        return normalize_dataframe(df, is_archive=True)
    except Exception:
        # Mengembalikan DataFrame kosong diam-diam jika tab archive belum memiliki data
        return pd.DataFrame()
