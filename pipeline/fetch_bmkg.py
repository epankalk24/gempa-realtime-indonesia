"""
fetch_bmkg.py
-------------
Mengambil data gempa dari dua endpoint API resmi BMKG TEWS (Tsunami Early Warning System).
Script ini hanya bertanggung jawab untuk MENGAMBIL dan MERAPIKAN data mentah menjadi
DataFrame pandas — logika filter dan deduplication ditangani di preprocess.py.
"""

import requests
import pandas as pd
from datetime import datetime, timezone
import hashlib


# Dua endpoint resmi BMKG yang akan kita gunakan
BMKG_ENDPOINTS = {
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
    Mengubah string kedalaman BMKG menjadi integer kilometer.
    Contoh: "10 km" -> 10
    """
    return int(str(depth_str).replace(" km", "").replace("km", "").strip())


def generate_event_id(datetime_str: str, magnitude: float, lat: float, lon: float) -> str:
    """
    Membuat ID unik untuk setiap kejadian gempa.
    
    Mengapa perlu ID buatan? Karena BMKG TEWS API tidak menyediakan ID per kejadian
    secara konsisten. Kita buat ID dengan meng-hash kombinasi waktu + magnitudo + koordinat
    — kombinasi ini secara praktis unik untuk setiap gempa.
    """
    key = f"{datetime_str}_{magnitude}_{lat}_{lon}"
    short_hash = hashlib.md5(key.encode()).hexdigest()[:12]
    return f"ev_{short_hash}"


def fetch_from_endpoint(url: str, source_name: str) -> pd.DataFrame:
    """
    Mengambil dan mem-parsing data dari satu endpoint BMKG.
    Mengembalikan DataFrame kosong jika terjadi error apapun
    (pipeline tidak akan crash jika satu endpoint gagal).
    """
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        # Struktur JSON BMKG: { "Infogempa": { "gempa": [...] } }
        gempa_list = data.get("Infogempa", {}).get("gempa", [])
        if not gempa_list:
            print(f"[WARNING] Tidak ada data dari endpoint: {source_name}")
            return pd.DataFrame()

        # Kadang BMKG mengembalikan satu object dict alih-alih list — normalisasi dulu
        if isinstance(gempa_list, dict):
            gempa_list = [gempa_list]

        records = []
        ingested_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        for g in gempa_list:
            try:
                datetime_str = g.get("DateTime", "")
                magnitude    = float(g.get("Magnitude", 0))
                latitude     = parse_coordinate(g.get("Lintang", "0"))
                longitude    = parse_coordinate(g.get("Bujur", "0"))
                depth_km     = parse_depth(g.get("Kedalaman", "0 km"))
                region       = g.get("Wilayah", "")
                event_id     = generate_event_id(datetime_str, magnitude, latitude, longitude)

                records.append({
                    "event_id":        event_id,
                    "datetime":        datetime_str,
                    "magnitude":       magnitude,
                    "depth_km":        depth_km,
                    "latitude":        latitude,
                    "longitude":       longitude,
                    "region":          region,
                    "source_endpoint": source_name,
                    "ingested_at":     ingested_at,
                })
            except Exception as e:
                # Lewati satu record bermasalah tanpa menghentikan seluruh proses
                print(f"[WARNING] Gagal parse satu record dari {source_name}: {e}")
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
    Mengambil data dari SEMUA endpoint BMKG dan menggabungkannya.
    Event yang sama mungkin muncul di kedua endpoint — deduplikasi awal dilakukan di sini
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
    # Hapus duplikat antar endpoint (event yang sama bisa muncul di keduanya)
    combined = combined.drop_duplicates(subset=["event_id"])
    print(f"[OK] Total {len(combined)} record unik setelah menggabungkan semua endpoint")
    return combined
