"""
fetch_bmkg.py
-------------
Mengambil data gempa dari TIGA endpoint API resmi BMKG TEWS.
Script ini bertanggung jawab untuk mengambil dan merapikan data mentah menjadi
DataFrame pandas.
"""

import requests
import pandas as pd
from datetime import datetime, timezone
import hashlib

# Tiga endpoint resmi BMKG (termasuk autogempa untuk kecepatan real-time instan)
BMKG_ENDPOINTS = {
    "bmkg_tews_m5":        "https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json",
    "bmkg_tews_dirasakan": "https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.json",
}

def parse_coordinate(coord_str: str) -> float:
    """Mengubah string koordinat BMKG menjadi angka float bernotasi standar."""
    parts = str(coord_str).strip().split()
    value = float(parts[0])
    direction = parts[1].upper() if len(parts) > 1 else ""
    if direction in ("LS", "S"):
        value = -value
    return round(value, 6)

def parse_depth(depth_str: str) -> int:
    """Mengubah string kedalaman BMKG ('10 km') menjadi integer (10)."""
    return int(''.join(filter(str.isdigit, str(depth_str))))

def fetch_from_endpoint(url: str, source_name: str) -> pd.DataFrame:
    """Fungsi generik untuk mengambil dan mem-parsing JSON dari satu endpoint BMKG."""
    print(f"[FETCH] Meminta data dari {source_name}...")
    try:
        # SOLUSI 403 FORBIDDEN: Menambahkan identitas browser Chrome (User-Agent)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        
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
        for g in data_gempa:
            try:
                # Menggunakan format ISO 8601 UTC langsung dari API BMKG
                dt_str = g.get("DateTime")
                
                lat_str, lon_str = g.get("Coordinates", ",").split(",")
                latitude  = float(lat_str)
                longitude = float(lon_str)

                magnitude = float(g.get("Magnitude", 0.0))
                depth_km  = parse_depth(g.get("Kedalaman", "0"))

                # Buat ID unik (hash) berdasarkan waktu dan magnitudo
                unique_string = f"{dt_str}_{magnitude}_{latitude}_{longitude}"
                event_id = hashlib.md5(unique_string.encode('utf-8')).hexdigest()[:12]
                event_id = f"ev_{event_id}"

                record = {
                    "event_id": event_id,
                    "datetime": dt_str,
                    "magnitude": magnitude,
                    "depth_km": depth_km,
                    "latitude": latitude,
                    "longitude": longitude,
                    "region": g.get("Wilayah", ""),
                    "source_endpoint": source_name,
                    "ingested_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                }
                records.append(record)
            except Exception as e:
                print(f"[WARNING] Gagal mem-parsing satu baris data dari {source_name}: {e}")
                continue

        print(f"[OK] Berhasil mengambil {len(records)} record dari {source_name}")
        return pd.DataFrame(records)

    # Blok except yang sebelumnya tidak sengaja terhapus:
    except requests.exceptions.Timeout:
        print(f"[ERROR] Timeout saat mengakses {source_name}")
        return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Gagal mengakses {source_name}: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"[ERROR] Error tidak terduga dari {source_name}: {e}")
        return pd.DataFrame()

def fetch_all_bmkg_data() -> pd.DataFrame:
    """Mengambil data dari SEMUA endpoint BMKG dan menggabungkannya."""
    all_data = []
    for source_name, url in BMKG_ENDPOINTS.items():
        df = fetch_from_endpoint(url, source_name)
        if not df.empty:
            all_data.append(df)

    if not all_data:
        print("[ERROR] Tidak ada data berhasil diambil dari semua endpoint BMKG.")
        return pd.DataFrame()

    combined = pd.concat(all_data, ignore_index=True)
    
    # Hapus duplikat antar endpoint (autogempa pasti tumpang tindih dengan gempaterkini)
    combined = combined.drop_duplicates(subset=["event_id"], keep="first")
    
    print(f"[OK] Total {len(combined)} record unik berhasil digabungkan dari semua endpoint.")
    return combined
