import streamlit as st
import pandas as pd
from gspread_dataframe import get_as_dataframe
import gspread
from google.oauth2.service_account import Credentials
import json

def load_data():
    """
    Membaca data dari Google Sheets tab 'filtered_data' menggunakan kredensial dari Streamlit Secrets.
    Data disimpan dalam cache selama 5 menit (300 detik) untuk menghemat kuota API.
    """
    @st.cache_data(ttl=300)
    def fetch_cached_data():
        # Mengambil kredensial rahasia dari sistem manajemen Streamlit Cloud
        creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
        spreadsheet_id = st.secrets["SPREADSHEET_ID"]
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Membuka sheet filtered_data yang sudah bersih dari anomali luar Indonesia
        sh = client.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet("filtered_data")
        
        # Konversi data spreadsheet menjadi Pandas DataFrame
        df = pd.DataFrame(worksheet.get_all_records())
        
       if not df.empty:
            # Konversi secara defensif, data yang gagal di-parse akan diubah menjadi NaT (Not a Time)
            df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
            
            # Buang baris data yang format waktunya rusak agar peta tidak crash
            df = df.dropna(subset=["datetime"])
            
            # Mengurutkan dari kejadian yang paling terbaru
            df = df.sort_values(by="datetime", ascending=False)

    return fetch_cached_data()
