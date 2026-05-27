"""
preprocess.py
-------------
Menangani dua tugas pembersihan data:
  1. Filter spasial: buang gempa yang lokasinya di luar wilayah Indonesia
  2. Deduplication: buang event yang sudah ada di Google Sheets (mencegah baris ganda)
"""

import pandas as pd


# Bounding box wilayah Indonesia
# Lintang: 6°LU (positif) hingga 11°LS (negatif)
# Bujur:  95°BT hingga 141°BT
LAT_MIN = -11.0
LAT_MAX =   6.0
LON_MIN =  95.0
LON_MAX = 141.0


def filter_indonesia_bounds(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menyaring hanya gempa yang terjadi di dalam batas wilayah Indonesia.
    
    Ini penting karena endpoint BMKG kadang memasukkan gempa dari wilayah
    tetangga seperti Filipina (Mindanao) atau Papua Nugini yang secara geografis
    dekat dengan perbatasan Indonesia tapi bukan data yang kita targetkan.
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
    Hanya baris dengan event_id BARU yang akan di-return untuk di-append.
    
    Parameter:
        new_df       : DataFrame hasil fetch terbaru dari API BMKG
        existing_ids : set berisi semua event_id yang sudah tersimpan di Sheets
    """
    if new_df.empty:
        return new_df

    # Baris yang event_id-nya TIDAK ada di existing_ids = data baru
    mask       = ~new_df["event_id"].isin(existing_ids)
    new_only   = new_df[mask].copy()
    duplicates = len(new_df) - len(new_only)

    if duplicates > 0:
        print(f"[DEDUP] {duplicates} record dilewati karena sudah ada di Sheets")
    print(f"[DEDUP] {len(new_only)} record baru siap ditulis ke Sheets")

    return new_only
