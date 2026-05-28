"""
push_to_sheets.py
-----------------
Menangani semua interaksi dengan Google Sheets:
  - Autentikasi via Service Account
  - Membaca event_id secara spesifik (Low-Memory Fetching) untuk deduplication
  - Menulis baris baru ke sheet dengan skema 10 kolom ketat
"""

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import os
import json

# Izin akses yang diminta ke Google API
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def get_sheets_client() -> gspread.Client:
    """
    Membuat koneksi terautentikasi ke Google Sheets.
    """
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")

    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        print("[AUTH] Menggunakan kredensial dari environment variable (GitHub Actions)")
    else:
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
        print("[AUTH] Menggunakan kredensial dari file lokal credentials.json")

    return gspread.authorize(creds)

def get_existing_ids(client: gspread.Client, spreadsheet_id: str, sheet_name: str) -> set:
    """
    Membaca semua event_id yang sudah ada di sebuah sheet menggunakan Low-Memory Fetching.
    Mengembalikan set kosong jika sheet masih kosong atau terjadi error.
    
    Pendekatan ini menggunakan col_values(1) untuk mengekstrak hanya Kolom A,
    menghindari penarikan seluruh data tabel yang boros memori (O(1) lookup constraint).
    """
    try:
        sh = client.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet(sheet_name)
        
        # Ekstraksi hanya pada Kolom A (indeks 1 di gspread)
        id_column = worksheet.col_values(1)

        # Jika sheet hanya berisi header atau kosong sama sekali
        if len(id_column) <= 1:
            return set()

        # Konversi ke struktur Set untuk pencarian O(1), melewati baris pertama (header)
        existing_ids = set(id_column[1:])
        return existing_ids

    except gspread.exceptions.WorksheetNotFound:
        print(f"[ERROR] Sheet '{sheet_name}' tidak ditemukan di spreadsheet")
        return set()
    except Exception as e:
        print(f"[WARNING] Gagal membaca existing IDs dari '{sheet_name}': {e}")
        return set()

def append_to_sheet(
    client: gspread.Client,
    spreadsheet_id: str,
    sheet_name: str,
    df: pd.DataFrame
) -> int:
    """
    Menambahkan baris-baris DataFrame ke bawah sheet yang sudah ada (Idempotent Append).
    Mengembalikan jumlah baris yang berhasil ditulis.
    """
    if df.empty:
        print(f"[SKIP] Tidak ada data baru untuk disisipkan ke sheet '{sheet_name}'")
        return 0

    try:
        sh = client.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet(sheet_name)

        # Penetapan Skema Deterministik 10 Kolom (Wajib identik dengan GAS pipeline)
        # Menghapus 'source_endpoint' dan menambahkan 'potensi' serta 'dirasakan'
        column_order = [
            "event_id", "datetime", "magnitude", "depth_km",
            "latitude", "longitude", "region", "potensi", "dirasakan", "ingested_at"
        ]
        
        # Filter data frame agar hanya memuat urutan kolom yang benar
        df_ordered = df[column_order]
        rows = df_ordered.values.tolist()

        # Eksekusi Write API
        worksheet.append_rows(rows, value_input_option="USER_ENTERED")
        print(f"[OK] {len(rows)} baris data baru berhasil ditulis ke sheet '{sheet_name}'")
        return len(rows)

    except KeyError as e:
        print(f"[ERROR] Kolom tidak cocok dengan skema yang ditetapkan: {e}")
        raise
    except gspread.exceptions.WorksheetNotFound:
        print(f"[ERROR] Sheet '{sheet_name}' tidak ditemukan")
        raise
    except Exception as e:
        print(f"[ERROR] Gagal menulis ke sheet '{sheet_name}': {e}")
        raise
