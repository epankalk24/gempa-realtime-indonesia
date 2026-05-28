"""
preprocess.py
-------------
Menangani tiga tugas pemrosesan data (ETL):
  1. Standardisasi: Parsing raw JSON menjadi DataFrame 10 kolom deterministik (setara GAS).
  2. Filter spasial: Membuang gempa yang lokasinya di luar wilayah Indonesia.
  3. Deduplication: Membuang event yang sudah ada di Google Sheets (mencegah duplikasi GHA vs GAS).
"""

import pandas as pd
import re
from datetime import datetime, timezone

# ==========================================
# KONFIGURASI FILTER SPASIAL (BOUNDING BOX)
# ==========================================
# Lintang: 6°LU (positif) hingga 11°LS (negatif)
# Bujur:  95°BT hingga 141°BT
LAT_MIN = -11.0
LAT_MAX =   6.0
LON_MIN =  95.0
LON_MAX = 141.0

def standardize_bmkg_data(raw_json_list: list) -> pd.DataFrame:
    """
    Mengubah list dictionary dari API BMKG menjadi DataFrame 10 kolom.
    Struktur ini dijamin 100% identik dengan hasil generate dari Google Apps Script,
    memastikan raw_data di Google Sheets selalu konsisten.
    """
    standardized_rows = []
    
    for item in raw_json_list:
        datetime_val = str(item.get('DateTime', ''))
        magnitude_val = str(item.get('Magnitude', ''))
        
        # 1. Hashing ID Deterministik (Identik dengan logika GAS)
        raw_id_str = f"ID_{datetime_val}_{magnitude_val}"
        event_id = re.sub(r'[^a-zA-Z0-9]', '', raw_id_str)
        
        # 2. Pembersihan String Kedalaman (Hanya mengekstrak angka mutlak)
        depth_raw = str(item.get('Kedalaman', ''))
        depth = re.sub(r'[^0-9.]', '', depth_raw)
        
        # 3. Pemisahan Koordinat Spasial
        coords = str(item.get('Coordinates', '')).split(',')
        lat = coords[0].strip() if len(coords) > 0 else ''
        lon = coords[1].strip() if len(coords) > 1 else ''
        
        # 4. Fallback Parameter Deskriptif (Penanganan data kosong)
        region = item.get('Wilayah', '')
        potensi = item.get('Potensi', 'Tidak berpotensi tsunami') 
        dirasakan = item.get('Dirasakan', '-')
        
        # 5. Timestamp Ingestion (Menggunakan UTC agar seragam)
        ingested_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + "Z"
        
        # 6. Penyusunan Dictionary 10 Kolom
        row = {
            "event_id": event_id,
            "datetime": datetime_val,
            "magnitude": magnitude_val,
            "depth_km": depth,
            "latitude": lat,
            "longitude": lon,
            "region": region,
            "potensi": potensi,
            "dirasakan": dirasakan,
            "ingested_at": ingested_at
        }
        standardized_rows.append(row)
        
    df = pd.DataFrame(standardized_rows)
    
    # Casting tipe data koordinat menjadi numerik agar filter spasial dapat bekerja
    if not df.empty:
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
        
    return df


def filter_indonesia_bounds(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menyaring hanya gempa yang terjadi di dalam batas wilayah Indonesia.
    Ini penting karena endpoint BMKG kadang memasukkan gempa dari wilayah
    tetangga seperti Filipina (Mindanao) atau Papua Nugini.
    """
    if df.empty:
        return df

    mask = (
        (df["latitude"]  >= LAT_MIN) & (df["latitude"]  <= LAT_MAX) &
        (df["longitude"] >= LON_MIN) & (df["longitude"] <= LON_MAX)
    )

    filtered  = df[mask].copy()
    excluded  = len(df) - len(filtered)

    if excluded > 0:
        print(f"[FILTER] {excluded} record dibuang karena berada di luar batas wilayah Indonesia")
    print(f"[FILTER] {len(filtered)} record lolos filter spasial")

    return filtered


def remove_duplicates(new_df: pd.DataFrame, existing_ids: set) -> pd.DataFrame:
    """
    Membandingkan event_id baru dengan yang sudah ada di Sheets.
    Hanya baris dengan event_id BARU yang akan dikembalikan.
    """
    if new_df.empty:
        return new_df

    # Mempertahankan baris yang event_id-nya TIDAK ada di existing_ids
    mask       = ~new_df["event_id"].isin(existing_ids)
    new_only   = new_df[mask].copy()
    duplicates = len(new_df) - len(new_only)

    if duplicates > 0:
        print(f"[DEDUP] {duplicates} record dilewati karena sudah ada di Sheets")
    print(f"[DEDUP] {len(new_only)} record baru siap ditulis ke Sheets")

    return new_only
