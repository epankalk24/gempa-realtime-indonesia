"""
push_to_sheets.py
-----------------
Menangani semua interaksi dengan Google Sheets:
  - Autentikasi via Service Account
  - Membaca event_id yang sudah ada (untuk deduplication)
  - Menulis baris baru ke sheet yang ditentukan
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
    
    Urutan prioritas autentikasi:
      1. Environment variable GOOGLE_CREDENTIALS (digunakan saat berjalan di GitHub Actions)
      2. File credentials.json lokal (digunakan saat development di komputer Anda)
    
    Dengan cara ini, kode yang sama berjalan baik di lokal maupun di server GitHub
    tanpa perlu mengubah apapun.
    """
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")

    if creds_json:
        # GitHub Actions: kredensial disimpan sebagai Secret string JSON
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        print("[AUTH] Menggunakan kredensial dari environment variable")
    else:
        # Development lokal: baca langsung dari file
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
        print("[AUTH] Menggunakan kredensial dari file credentials.json")

    return gspread.authorize(creds)


def get_existing_ids(client: gspread.Client, spreadsheet_id: str, sheet_name: str) -> set:
    """
    Membaca semua event_id yang sudah ada di sebuah sheet.
    Mengembalikan set kosong jika sheet masih kosong atau terjadi error.
    
    Mengapa menggunakan set? Karena pengecekan `x in set` jauh lebih cepat
    daripada pengecekan di list — O(1) vs O(n). Ini penting ketika data
    sudah mencapai ribuan baris di bulan ke-2 dan ke-3.
    """
    try:
        sh        = client.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet(sheet_name)
        all_rows  = worksheet.get_all_values()

        # Jika sheet hanya berisi header atau kosong sama sekali
        if len(all_rows) <= 1:
            return set()

        headers = all_rows[0]
        if "event_id" not in headers:
            print(f"[WARNING] Kolom 'event_id' tidak ditemukan di sheet '{sheet_name}'")
            return set()

        id_col = headers.index("event_id")
        return set(row[id_col] for row in all_rows[1:] if len(row) > id_col and row[id_col])

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
    Menambahkan baris-baris DataFrame ke bawah sheet yang sudah ada.
    Mengembalikan jumlah baris yang berhasil ditulis.
    
    Catatan teknis: kita menggunakan value_input_option="USER_ENTERED" agar
    Google Sheets memformat angka seperti yang diketik pengguna (bukan raw string).
    """
    if df.empty:
        print(f"[SKIP] Tidak ada data baru untuk sheet '{sheet_name}'")
        return 0

    try:
        sh        = client.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet(sheet_name)

        # Pastikan urutan kolom konsisten dengan header yang ada di Sheets
        column_order = [
            "event_id", "datetime", "magnitude", "depth_km",
            "latitude", "longitude", "region", "source_endpoint", "ingested_at"
        ]
        df_ordered = df[column_order]
        rows = df_ordered.values.tolist()

        worksheet.append_rows(rows, value_input_option="USER_ENTERED")
        print(f"[OK] {len(rows)} baris berhasil ditulis ke sheet '{sheet_name}'")
        return len(rows)

    except gspread.exceptions.WorksheetNotFound:
        print(f"[ERROR] Sheet '{sheet_name}' tidak ditemukan")
        raise
    except Exception as e:
        print(f"[ERROR] Gagal menulis ke sheet '{sheet_name}': {e}")
        raise
