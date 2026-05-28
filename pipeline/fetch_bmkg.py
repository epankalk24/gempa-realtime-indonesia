"""
fetch_bmkg.py
-------------
Hanya mengambil data mentah (JSON) dari endpoint M5+ dan Dirasakan.
Fungsi ini bertindak murni sebagai "Dumb Extractor" yang mengembalikan List of Dictionaries.
Seluruh logika transformasi, standardisasi 10 kolom, dan deduplikasi 
kini dipindahkan ke preprocess.py agar identik dengan format Google Apps Script.
"""

import requests

# Tiga endpoint resmi BMKG (autogempa dihapus karena sudah di-handle oleh GAS)
BMKG_ENDPOINTS = {
    "bmkg_tews_m5":        "https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json",
    "bmkg_tews_dirasakan": "https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.json",
}

def fetch_all_data() -> list:
    """
    Mengambil data dari SEMUA endpoint BMKG dan menggabungkannya
    menjadi satu List mentah (tanpa manipulasi skema/DataFrame).
    """
    all_raw_data = []
    
    # SOLUSI 403 FORBIDDEN: Menambahkan identitas browser Chrome (User-Agent)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    for source_name, url in BMKG_ENDPOINTS.items():
        print(f"[FETCH] Meminta data dari {source_name}...")
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()

            # Ekstraksi array gempa
            data_gempa = data.get("Infogempa", {}).get("gempa", [])
            
            # BMKG API mengembalikan dict tunggal jika hanya ada 1 gempa
            if isinstance(data_gempa, dict):
                data_gempa = [data_gempa]

            if not data_gempa:
                print(f"[WARNING] Tidak ada data gempa ditemukan di {source_name}")
                continue

            # Langsung kumpulkan JSON mentah ke dalam list utama
            all_raw_data.extend(data_gempa)
            print(f"[OK] Berhasil mengambil {len(data_gempa)} record mentah dari {source_name}")

        except requests.exceptions.Timeout:
            print(f"[ERROR] Timeout saat mengakses {source_name}")
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Gagal mengakses {source_name}: {e}")
        except Exception as e:
            print(f"[ERROR] Kesalahan parsing JSON pada {source_name}: {e}")

    if not all_raw_data:
        print("[ERROR] Tidak ada data berhasil diambil dari semua endpoint BMKG.")
        
    return all_raw_data

# Note: Fungsi fetch_all_bmkg_data() yang lama dihapus karena
# pemanggilan di main.py kini merujuk pada fetch_all_data()
