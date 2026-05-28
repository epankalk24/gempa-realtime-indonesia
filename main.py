"""
main.py
-------
Orkestrator utama pipeline data BMKG (Berjalan di GitHub Actions).

Urutan eksekusi (ETL):
  1. EXTRACT: Ambil data JSON mentah terbaru dari API BMKG (fetch_bmkg.py).
  2. TRANSFORM: Standardisasi skema 10 kolom deterministik seperti GAS (preprocess.py).
  3. FILTER: Buang koordinat wilayah di luar batas Indonesia (preprocess.py).
  4. DEDUPLICATE: Cek event_id terhadap data yang sudah ada di raw_data (push_to_sheets.py).
  5. LOAD: Tulis HANYA data baru ke tab raw_data.

Catatan: Pengisian tab 'filtered_data' dan 'archive_summary' kini ditangani 
sepenuhnya oleh Google Apps Script (GAS) di background.
"""

import os
import sys

from pipeline.fetch_bmkg import fetch_all_data
from pipeline.preprocess import standardize_bmkg_data, filter_indonesia_bounds, remove_duplicates
from pipeline.push_to_sheets import get_sheets_client, get_existing_ids, append_to_sheet

# Spreadsheet ID diambil dari environment variable (GitHub Actions Secret)
SPREADSHEET_ID = os.environ.get(
    "SPREADSHEET_ID",
    "11bfOl9ZZQwIsX0u1h5Wd_gYfYm5rdaZV9mGSknadd2k" # Fallback untuk testing lokal
)

SHEET_RAW = "raw_data"

def run_pipeline():
    print("=" * 50)
    print("  BMKG EARTHQUAKE DATA PIPELINE - STARTED")
    print("=" * 50)

    # ── LANGKAH 1: Ekstraksi Data JSON ──────────────────
    print("\n[STEP 1] Mengambil data mentah dari API BMKG...")
    raw_json_list = fetch_all_data()

    if not raw_json_list:
        print("[EXIT] Tidak ada data yang berhasil diambil dari BMKG. Pipeline berhenti.")
        sys.exit(0)

    # ── LANGKAH 2: Transformasi & Standardisasi Skema ───
    print("\n[STEP 2] Standardisasi data menjadi skema 10 kolom (Format GAS)...")
    df_standard = standardize_bmkg_data(raw_json_list)

    if df_standard.empty:
        print("[EXIT] Gagal menstandardisasi data. Pipeline berhenti.")
        sys.exit(0)

    # ── LANGKAH 3: Filter Koordinat Spasial ─────────────
    print("\n[STEP 3] Memfilter berdasarkan batas wilayah Indonesia...")
    df_filtered = filter_indonesia_bounds(df_standard)
    
    if df_filtered.empty:
        print("[EXIT] Tidak ada record yang lolos filter spasial. Pipeline berhenti.")
        sys.exit(0)

    # ── LANGKAH 4: Koneksi ke Google Sheets ─────────────
    print("\n[STEP 4] Menghubungkan ke Google Sheets...")
    client = get_sheets_client()

    # ── LANGKAH 5: Cek Duplikasi Database (Idempotent) ──
    print(f"\n[STEP 5] Memeriksa duplikasi ID di sheet '{SHEET_RAW}'...")
    existing_raw_ids = get_existing_ids(client, SPREADSHEET_ID, SHEET_RAW)
    df_new = remove_duplicates(df_filtered, existing_raw_ids)

    if df_new.empty:
        print(f"[EXIT] Semua {len(df_filtered)} record sudah ada di '{SHEET_RAW}'. Tidak ada penulisan data.")
        sys.exit(0)

    # ── LANGKAH 6: Load / Tulis ke Database ─────────────
    print(f"\n[STEP 6] Menulis {len(df_new)} record baru ke sheet '{SHEET_RAW}'...")
    count_raw = append_to_sheet(client, SPREADSHEET_ID, SHEET_RAW, df_new)

    # ── RINGKASAN ────────────────────────────────────────
    print("\n" + "=" * 50)
    print(f"  PIPELINE SELESAI")
    print(f"  raw_data : +{count_raw} baris baru")
    print("=" * 50)


if __name__ == "__main__":
    run_pipeline()
