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
    """
    Fungsi generik untuk mengambil dan mem-parsing JSON dari satu endpoint BMKG.
    """
    print(f"[FETCH] Meminta data dari {source_name}...")
    try:
        response = requests.get(url, timeout=15)
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
                dt_str = f"{g.get('Tanggal', '')} {g.get('Jam', '')}"
                
                # Format datetime BMKG kadang bervariasi, kita coba parse
                # Contoh: "26 Mei 2024 10:15:30 WIB"
                
                lat_str, lon_str = g.get("Coordinates", ",").split(",")
                latitude  = float(lat_str)
                longitude = float(lon_str)

                magnitude = float(g.get("Magnitude", 0.0))
                depth_km  = parse_depth(g.get("Kedalaman", "0"))

                # Buat ID unik (hash) berdasarkan waktu dan magnitudo agar konsisten
                # Ini berguna jika BMKG mengupdate narasi wilayah tapi event-nya sama
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
