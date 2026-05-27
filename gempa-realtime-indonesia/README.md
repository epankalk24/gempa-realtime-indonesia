# 🌏 Sistem Pemantauan Gempa Bumi Real-Time Indonesia

[![Pipeline Status](https://github.com/USERNAME/gempa-realtime-indonesia/actions/workflows/fetch_bmkg.yml/badge.svg)](https://github.com/USERNAME/gempa-realtime-indonesia/actions/workflows/fetch_bmkg.yml)

Proyek portofolio data engineering yang membangun sistem pemantauan gempa bumi Indonesia secara otomatis menggunakan data resmi BMKG, pipeline Python, dan visualisasi web interaktif.

> **Aplikasi web aktif:** [Klik di sini untuk membuka peta gempa real-time](https://share.streamlit.io) *(link akan diperbarui setelah deployment)*

---

## Gambaran Sistem

Data gempa diambil otomatis setiap jam dari API resmi BMKG (Tsunami Early Warning System), disimpan ke Google Sheets sebagai database, dan divisualisasikan melalui aplikasi web Streamlit yang dapat diakses publik.

```
API BMKG TEWS → GitHub Actions (setiap jam) → Google Sheets → Streamlit Web App
```

---

## Struktur Proyek

```
gempa-realtime-indonesia/
├── .github/workflows/    # Konfigurasi otomatisasi GitHub Actions
├── pipeline/             # Skrip Python: fetch, preprocess, push to Sheets
├── app/                  # Aplikasi web Streamlit
├── analysis/             # Notebook analisis bulanan (Colab)
└── assets/               # Screenshot dan media dokumentasi
```

---

## Cara Menjalankan Lokal

```bash
# Clone repositori
git clone https://github.com/USERNAME/gempa-realtime-indonesia.git
cd gempa-realtime-indonesia

# Install dependensi
pip install -r requirements.txt

# Pastikan file credentials.json ada di root folder
# Jalankan pipeline sekali
python main.py
```

---

## Laporan Analisis Bulanan

| Bulan | Periode | Status | Link |
|-------|---------|--------|------|
| Bulan 1 | - | Menunggu | - |
| Bulan 2 | - | Menunggu | - |
| Bulan 3 | - | Menunggu | - |

---

## Sumber Data

Data gempa diambil dari dua endpoint resmi **BMKG TEWS (Tsunami Early Warning System)**:
- Gempa terkini M ≥ 5.0: `https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json`
- Gempa yang dirasakan: `https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.json`

---

*Proyek ini dibuat sebagai bagian dari portofolio Spatial Data Engineering — dikerjakan selama 3 bulan (2026).*
