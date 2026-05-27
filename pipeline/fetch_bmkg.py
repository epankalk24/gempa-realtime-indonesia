"""
fetch_bmkg.py
-------------
Mengambil data gempa dari TIGA endpoint API resmi BMKG TEWS (Tsunami Early Warning System).
Script ini hanya bertanggung jawab untuk MENGAMBIL dan MERAPIKAN data mentah menjadi
DataFrame pandas — logika filter dan deduplication ditangani di preprocess.py.
"""

import requests
import pandas as pd
from datetime import datetime, timezone
import hashlib


# Tiga endpoint resmi BMKG (termasuk autogempa untuk kecepatan real-time instan)
BMKG_ENDPOINTS = {
    "bmkg_tews_autogempa": "https://data.bmkg.go.id/DataMKG/TEWS/autogempa.json",
    "bmkg_tews_m5":        "https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json",
    "bmkg_tews_dirasakan": "https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.json",
}


def parse_coordinate(coord_str: str) -> float:
    """
    Mengubah string koordinat BMKG menjadi angka float bernotasi standar.
    
    Contoh input dari BMKG:
      "6.82 LS"  -> -6.82  (LS = Lintang Selatan, negatif)
      "106.91 BT" -> 106.91 (BT = Bujur Timur, positif)
    """
    parts = str(coord_str).strip().split()
    value = float(parts[0])
    direction = parts[1].upper() if len(parts) > 1 else ""
    if direction in ("LS", "S"):
        value = -value  # Lintang Selatan = negatif
    return round(value, 6)


def parse_depth(depth_str: str) -> int:
    """
    Mengubah string kedalaman BMKG ('10 km') menjadi integer (10).
    """
    return int(''.join(filter(str.isdigit, str(depth_str))))


def fetch_from_endpoint(url: str, source_name: str) -> pd.DataFrame:
   def fetch_from_endpoint(url: str, source_name: str) -> pd.DataFrame:
    """
    Fungsi generik untuk mengambil dan mem-parsing JSON dari satu endpoint BMKG.
    """
    print(f"[FETCH] Meminta data dari {source_name}...")
    try:
        # SOLUSI 403 FORBIDDEN: Menambahkan identitas browser Chrome (User-Agent) 
        # agar tidak diblokir oleh sistem keamanan server BMKG
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        
        # Masukkan parameter headers ke dalam requests.get
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        # Ekstraksi array gempa
        data_gempa = data.get("Infogempa", {}).get("gempa", [])
        
        # BMKG API mengembalikan dict tunggal (autogempa) jika hanya ada 1 gempa
        if isinstance(data_gempa, dict):
            data_gempa = [data_gempa]

        if not data_gempa:
            print(f"[WARNING] Tidak ada data gempa ditemukan di {source_name}")
            return pd.DataFrame()

        records = []
        # ... (Biarkan sisa kode di bawahnya sama persis seperti sebelumnya) ...
        for g in data_gempa:
            try:
                dt_str = f"{g.get('Tanggal', '')} {g.get('Jam', '')}"
# ... LANJUTAN KODE ANDA SEBELUMNYA ...

def fetch_all_bmkg_data() -> pd.DataFrame:
    """
    Mengambil data dari KETIGA endpoint BMKG dan menggabungkannya.
    Event yang sama mungkin muncul di beberapa endpoint — deduplikasi awal dilakukan di sini
    berdasarkan event_id, deduplication final (vs data yang sudah ada di Sheets)
    dilakukan di preprocess.py.
    """
    all_data = []
    for source_name, url in BMKG_ENDPOINTS.items():
        df = fetch_from_endpoint(url, source_name)
        if not df.empty:
            all_data.append(df)

    if not all_data:
        print("[ERROR] Tidak ada data berhasil diambil dari semua endpoint BMKG.")
        return pd.DataFrame()

    combined = pd.concat(all_data, ignore_index=True)
    
    # KUNCI: Hapus duplikat antar endpoint (autogempa hampir pasti ada juga di gempaterkini)
    # Ini memastikan database kita tetap bersih
    combined = combined.drop_duplicates(subset=["event_id"], keep="first")
    
    print(f"[OK] Total {len(combined)} record unik berhasil digabungkan dari semua endpoint.")
    return combined
