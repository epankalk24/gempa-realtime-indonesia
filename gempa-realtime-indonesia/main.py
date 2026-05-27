"""
main.py
-------
Orkestrator utama pipeline data BMKG.
File inilah yang dijalankan oleh GitHub Actions setiap jam.

Urutan eksekusi:
  1. Ambil data terbaru dari API BMKG (fetch_bmkg.py)
  2. Sambungkan ke Google Sheets (push_to_sheets.py)
  3. Cek duplikasi vs data yang sudah ada di sheet raw_data
  4. Tulis data baru ke raw_data
  5. Filter koordinat wilayah Indonesia (preprocess.py)
  6. Tulis data baru yang sudah difilter ke filtered_data

Jika tidak ada data baru sama sekali, script selesai lebih awal tanpa error
sehingga tidak membuang menit eksekusi GitHub Actions.
"""

import os
import sys

from pipeline.fetch_bmkg     import fetch_all_bmkg_data
from pipeline.preprocess     import filter_indonesia_bounds, remove_duplicates
from pipeline.push_to_sheets import get_sheets_client, get_existing_ids, append_to_sheet


# Spreadsheet ID diambil dari environment variable (GitHub Actions Secret)
# Fallback ke ID hardcoded untuk keperluan testing lokal
SPREADSHEET_ID = os.environ.get(
    "SPREADSHEET_ID",
    "11bfOl9ZZQwIsX0u1h5Wd_gYfYm5rdaZV9mGSknadd2k"
)

SHEET_RAW      = "raw_data"
SHEET_FILTERED = "filtered_data"


def run_pipeline():
    print("=" * 50)
    print("  BMKG EARTHQUAKE DATA PIPELINE - STARTED")
    print("=" * 50)

    # ── LANGKAH 1: Ambil data dari API ──────────────────
    print("\n[STEP 1] Mengambil data dari API BMKG...")
    raw_df = fetch_all_bmkg_data()

    if raw_df.empty:
        print("[EXIT] Tidak ada data yang berhasil diambil dari BMKG. Pipeline berhenti.")
        sys.exit(0)

    print(f"        Total {len(raw_df)} record berhasil diambil")

    # ── LANGKAH 2: Koneksi ke Google Sheets ─────────────
    print("\n[STEP 2] Menghubungkan ke Google Sheets...")
    client = get_sheets_client()

    # ── LANGKAH 3: Cek duplikasi untuk raw_data ─────────
    print("\n[STEP 3] Memeriksa duplikasi di sheet raw_data...")
    existing_raw_ids = get_existing_ids(client, SPREADSHEET_ID, SHEET_RAW)
    new_raw_df = remove_duplicates(raw_df, existing_raw_ids)

    if new_raw_df.empty:
        print("[EXIT] Semua record sudah ada di database. Tidak ada yang perlu ditulis.")
        sys.exit(0)

    # ── LANGKAH 4: Tulis ke raw_data ────────────────────
    print(f"\n[STEP 4] Menulis {len(new_raw_df)} record baru ke sheet raw_data...")
    count_raw = append_to_sheet(client, SPREADSHEET_ID, SHEET_RAW, new_raw_df)

    # ── LANGKAH 5: Filter koordinat Indonesia ───────────
    print("\n[STEP 5] Memfilter berdasarkan batas wilayah Indonesia...")
    filtered_df = filter_indonesia_bounds(new_raw_df)

    # ── LANGKAH 6: Tulis ke filtered_data ───────────────
    count_filtered = 0
    if not filtered_df.empty:
        print(f"\n[STEP 6] Menulis {len(filtered_df)} record ke sheet filtered_data...")
        existing_filtered_ids = get_existing_ids(client, SPREADSHEET_ID, SHEET_FILTERED)
        new_filtered_df       = remove_duplicates(filtered_df, existing_filtered_ids)
        count_filtered        = append_to_sheet(client, SPREADSHEET_ID, SHEET_FILTERED, new_filtered_df)
    else:
        print("\n[STEP 6] Tidak ada record yang lolos filter spasial.")

    # ── RINGKASAN ────────────────────────────────────────
    print("\n" + "=" * 50)
    print(f"  PIPELINE SELESAI")
    print(f"  raw_data      : +{count_raw} baris")
    print(f"  filtered_data : +{count_filtered} baris")
    print("=" * 50)


if __name__ == "__main__":
    run_pipeline()
