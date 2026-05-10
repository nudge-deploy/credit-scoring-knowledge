# Sistem Penilaian Kredit UMKM
### Berbasis Machine Learning & Document Extraction (Claude Vision AI)

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.2.5-lightgrey?logo=flask)
![LightGBM](https://img.shields.io/badge/Model-LightGBM-green)
![Claude Vision](https://img.shields.io/badge/AI-Claude%20Vision-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

Sistem ini mengotomatiskan proses seleksi awal pengajuan kredit UMKM menggunakan kombinasi **AI document extraction** dan **machine learning classifier**. Pengguna cukup mengunggah dokumen fisik (KTP, SKU, rekening koran, laporan keuangan), sistem akan mengekstrak data secara otomatis dan menghasilkan rekomendasi kelayakan kredit dalam hitungan detik.

---

## Daftar Isi

- [Demo & Tampilan](#demo--tampilan)
- [Fitur Utama](#fitur-utama)
- [Arsitektur Sistem](#arsitektur-sistem)
- [Struktur Folder](#struktur-folder)
- [Prasyarat](#prasyarat)
- [Instalasi & Setup](#instalasi--setup)
- [Menjalankan Aplikasi](#menjalankan-aplikasi)
- [Melatih Model ML](#melatih-model-ml)
- [Dokumentasi API](#dokumentasi-api)
- [Dokumen yang Didukung](#dokumen-yang-didukung)
- [Kategori Output Model](#kategori-output-model)
- [Fitur Model ML](#fitur-model-ml)
- [Deployment ke Render](#deployment-ke-render)
- [Troubleshooting](#troubleshooting)
- [Roadmap Production](#roadmap-production)
- [Regulasi yang Relevan](#regulasi-yang-relevan)

---

## Demo & Tampilan

Sistem terdiri dari dua layar utama:

**Tab Upload Dokumen** — pengguna drag & drop gambar dokumen, sistem langsung mengekstrak data secara real-time dan menampilkan field yang berhasil dibaca di bawah setiap kartu dokumen.

**Tab Data Manual** — untuk field yang tidak bisa diekstrak dari dokumen (kolektibilitas SLIK OJK, plafon yang diminta, tenor, dll.) pengguna mengisinya secara manual sebelum klik Analisis.

Setelah klik **Analisis Kelayakan**, panel kanan menampilkan:
- Label rekomendasi dengan warna dan ikon sesuai tingkat risiko
- Confidence score (persentase keyakinan model)
- Distribusi probabilitas untuk semua 5 kelas
- Ringkasan data yang berhasil diekstrak dari dokumen

---

## Fitur Utama

- **Document Extraction berbasis AI** — mengirim gambar dokumen ke Claude Vision API dan mengonversinya menjadi data terstruktur secara otomatis
- **Klasifikasi 5 kelas** — model mengklasifikasikan pemohon ke dalam 5 kategori kelayakan beserta probabilitas masing-masing kelas
- **UI drag & drop** — antarmuka web modern yang dapat diakses langsung dari browser tanpa instalasi tambahan
- **Preprocessing otomatis** — ordinal encoding, one-hot encoding, feature engineering (DSCR, rasio saldo, log transform), dan scaling dilakukan otomatis saat inferensi
- **Validasi NIK lokal** — memvalidasi format NIK 16 digit secara lokal (kode provinsi, tanggal lahir, jenis kelamin) tanpa memerlukan koneksi ke Dukcapil
- **Health monitoring** — endpoint `/health` untuk monitoring uptime dan status model
- **Diagnosis sistem** — script `diagnose.py` untuk memverifikasi semua komponen sebelum deployment

---

## Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (index.html)                      │
│  ┌──────────────────┐         ┌──────────────────────────┐  │
│  │  Upload Dokumen  │         │   Hasil & Probabilitas   │  │
│  │  (drag & drop)   │         │   per Kelas              │  │
│  └────────┬─────────┘         └──────────────────────────┘  │
└───────────┼──────────────────────────────────────────────────┘
            │ multipart/form-data & JSON
            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Flask API (app.py :5000)                   │
│                                                              │
│  POST /extract-and-predict                                   │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────────┐  │
│  │  extractor  │    │ preprocess() │    │  model.predict │  │
│  │    .py      │    │  + scaler    │    │   + proba      │  │
│  └──────┬──────┘    └──────┬───────┘    └────────────────┘  │
│         │                  │                                  │
└─────────┼──────────────────┼──────────────────────────────────┘
          │                  │
          ▼                  ▼
┌──────────────────┐  ┌──────────────────────────┐
│  Claude Vision   │  │    model_artifacts/       │
│  API (Anthropic) │  │  model_kredit_umkm.pkl    │
│                  │  │  scaler_kredit_umkm.pkl   │
│  Ekstrak field   │  │  model_metadata.json      │
│  dari gambar     │  └──────────────────────────┘
└──────────────────┘
```

**Alur kerja lengkap:**
1. Pengguna upload gambar dokumen (KTP, SKU, rekening koran, laporan keuangan)
2. `extractor.py` mengirim setiap gambar ke Claude Vision API dengan prompt khusus per jenis dokumen
3. Hasil ekstraksi (JSON) digabungkan dengan field manual dari pengguna
4. `preprocess()` menjalankan seluruh pipeline transformasi (encoding, feature engineering, scaling)
5. Model LightGBM menghasilkan label prediksi + probabilitas 5 kelas
6. Hasil ditampilkan di UI dengan visualisasi

---

## Struktur Folder

```
umkm-kredit/
│
├── app.py                          # Flask API server — entry point utama
├── extractor.py                    # Document extraction engine (Claude Vision)
├── nik_validator.py                # Validasi format NIK 16 digit secara lokal
├── index.html                      # Frontend — single page web application
│
├── umkm_kredit_ml.ipynb            # Jupyter notebook pipeline ML (training)
├── umkm_kredit_training_data.csv   # Dataset training (1.000 baris, 34 kolom)
│
├── diagnose.py                     # Script diagnosis & verifikasi sistem
├── requirements.txt                # Dependensi Python
├── render.yaml                     # Konfigurasi deployment Render
├── .gitignore                      # File yang dikecualikan dari Git
├── .env                            # ⚠️ JANGAN di-commit! API key di sini
│
└── model_artifacts/                # Dihasilkan otomatis oleh notebook
    ├── model_kredit_umkm.pkl       # Model LightGBM/XGBoost terlatih (~1 MB)
    ├── scaler_kredit_umkm.pkl      # StandardScaler terlatih pada training set
    └── model_metadata.json         # Nama fitur, label mapping, performa model
```

---

## Prasyarat

Pastikan semua item berikut terpenuhi sebelum mulai:

| Prasyarat | Versi | Cara Cek |
|-----------|-------|----------|
| Python | >= 3.8 (direkomendasikan 3.11) | `python --version` |
| pip | terbaru | `pip --version` |
| Git | semua versi | `git --version` |
| Jupyter | untuk menjalankan notebook | `jupyter --version` |
| Akun Anthropic | kredit aktif | [console.anthropic.com](https://console.anthropic.com) |

**Untuk mendapatkan Anthropic API Key:**
1. Daftar di [console.anthropic.com](https://console.anthropic.com)
2. Masuk ke **Settings → API Keys → Create Key**
3. Salin key — hanya ditampilkan sekali!
4. Pastikan ada kredit di **Settings → Billing** (minimum top-up $5)

---

## Instalasi & Setup

### 1. Clone repository

```bash
git clone https://github.com/aDJi2003/umkm-kredit.git
cd umkm-kredit
```

### 2. Buat virtual environment (sangat direkomendasikan)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install semua dependensi

```bash
pip install -r requirements.txt
```

Atau install manual:

```bash
pip install flask==2.2.5 flask-cors==4.0.0 pandas==2.0.3 numpy==1.24.3 \
    scikit-learn==1.3.0 xgboost==2.0.0 lightgbm==4.1.0 joblib==1.3.2 \
    anthropic==0.20.0 python-dotenv==1.0.0 gunicorn==21.2.0 pillow==10.0.0
```

> **Windows:** Jika instalasi `lightgbm` gagal, install [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) terlebih dahulu.

### 4. Konfigurasi API Key

Buat file `.env` di root folder proyek (satu level dengan `app.py`):

```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxx
```

> ⚠️ **PENTING:** File `.env` sudah ada di `.gitignore`. Jangan pernah hardcode API key langsung di kode atau push ke GitHub.

### 5. Verifikasi setup dengan diagnosis

```bash
python diagnose.py
```

Semua item harus menunjukkan ✅. Jika ada yang ❌, ikuti petunjuk yang ditampilkan script.

---

## Menjalankan Aplikasi

### Langkah 1 — Pastikan model ML sudah tersedia

Folder `model_artifacts/` harus berisi tiga file:
- `model_kredit_umkm.pkl`
- `scaler_kredit_umkm.pkl`
- `model_metadata.json`

Jika belum ada, [latih model terlebih dahulu](#melatih-model-ml).

### Langkah 2 — Jalankan API server

```bash
python app.py
```

Output yang diharapkan:

```
✅  Model dimuat: LightGBM  |  F1: 0.9123
════════════════════════════════════════════════════
  API Kredit UMKM  →  http://localhost:5000
  Environment      :  Local (development)
════════════════════════════════════════════════════
```

### Langkah 3 — Buka antarmuka web

Buka file `index.html` di browser (klik dua kali, atau klik kanan → Open with → Chrome/Edge).

Status di pojok kanan atas header akan berubah menjadi **hijau** bertuliskan `API online · LightGBM`.

### Langkah 4 — Coba dengan dokumen sample

Dokumen dummy untuk testing tersedia di folder `sample_docs/`:
- `ktp_budi_santoso.png`
- `sku_toko_sembako.png`
- `rekening_koran_bri.png`
- `laporan_keuangan_sembako.png`

Upload dokumen-dokumen tersebut ke masing-masing slot di UI, lalu klik **Analisis Kelayakan**.

> **Catatan:** Proses ekstraksi memakan waktu 5–15 detik per dokumen tergantung ukuran gambar dan kecepatan koneksi.

---

## Melatih Model ML

Model ML dibuat menggunakan Jupyter notebook. Ikuti langkah berikut:

### 1. Jalankan Jupyter

```bash
jupyter notebook
# atau
jupyter lab
```

### 2. Buka `umkm_kredit_ml.ipynb`

### 3. Jalankan semua cell secara berurutan

Notebook terdiri dari **12 cell** dengan urutan:

| Cell | Fase | Isi |
|------|------|-----|
| 0 | Setup | Import semua library yang dibutuhkan |
| 1 | Load | Baca file `umkm_kredit_training_data.csv` |
| 2–3 | EDA | Distribusi label, korelasi antar fitur, statistik deskriptif |
| 4–5 | Cleaning | Handle missing values, duplikat, cap outlier (IQR), konversi tipe |
| 6–9 | Engineering | Ordinal encoding, one-hot, fitur turunan (DSCR, rasio saldo, margin laba, flag risiko), log transform, label encoding |
| 10 | Split | Stratified split 70-15-15 + StandardScaler (fit HANYA pada train) |
| 11–12 | Training | 6 kandidat model + 5-fold cross-validation, visualisasi perbandingan |
| 13–14 | Evaluasi | Accuracy, F1-macro, confusion matrix, classification report per kelas |
| 15 | Tuning | RandomizedSearchCV hyperparameter tuning model terbaik |
| 16 | SHAP | Feature importance plot (top 20 fitur berpengaruh) |
| 17 | Test | Evaluasi final pada test set (dibuka hanya sekali) |
| 18–19 | Packaging | Simpan model, scaler, dan metadata ke `model_artifacts/` |

> ⚠️ **Data leakage warning:** `StandardScaler` di-fit **hanya** pada training set. Jangan pernah fit scaler pada seluruh data sebelum split — ini akan menyebabkan evaluasi tidak valid karena statistik test set "bocor" ke proses training.

### 4. Verifikasi hasil training

Setelah cell terakhir selesai, pastikan tiga file berikut ada:

```bash
ls model_artifacts/
# model_kredit_umkm.pkl
# model_kredit_umkm.pkl
# model_metadata.json
```

### Tentang Dataset Training

Dataset `umkm_kredit_training_data.csv` berisi **1.000 baris data sintetis** yang dibuat secara terprogram dengan distribusi seimbang (200 baris per kelas). Dataset ini dibuat khusus untuk keperluan prototype dan pengembangan.

> ⚠️ **PENTING untuk production:** Dataset dummy tidak mencerminkan pola kredit nyata. Sebelum deploy ke production, **ganti dengan data historis kredit yang sesungguhnya** sebagai ground truth untuk melatih ulang model.

**Ringkasan kolom dataset:**

| Kelompok | Jumlah Kolom | Contoh |
|----------|-------------|--------|
| Identitas usaha | 6 | `skala_usaha`, `lama_usaha_bulan`, `kbli_kode` |
| Pengajuan kredit | 2 | `plafon_diajukan`, `tenor_bulan` |
| Keuangan usaha | 5 | `total_pendapatan_bulanan`, `rata_laba_bersih_bulanan` |
| Rekening & arus kas | 3 | `rata_saldo_harian`, `total_kredit_3bln` |
| Riwayat kredit SLIK | 5 | `kolektibilitas_slik`, `status_blacklist` |
| Dokumen & agunan | 6 | `ada_npwp`, `jenis_agunan`, `rasio_agunan_terhadap_plafon` |
| Derived / computed | 6 | `dti_ratio`, `rasio_agunan_terhadap_plafon` |
| **Target** | **1** | **`label_kelayakan`** |

---

## Dokumentasi API

Base URL lokal: `http://localhost:5000`

### `GET /`
Mengembalikan halaman `index.html` (antarmuka web).

---

### `GET /health`
Health check — verifikasi model dan API berjalan.

**Respons sukses:**
```json
{
  "status": "ok",
  "model": "LightGBM",
  "f1_macro": 0.9123,
  "n_features": 42
}
```

---

### `GET /fields`
Mengembalikan definisi semua field form (digunakan frontend untuk membangun form secara dinamis).

**Respons:**
```json
[
  {
    "group": "Identitas Usaha",
    "key": "skala_usaha",
    "label": "Skala usaha",
    "type": "select",
    "options": ["mikro", "kecil", "menengah"],
    "default": "kecil"
  },
  ...
]
```

---

### `POST /predict`
Inferensi dari data JSON (tanpa upload dokumen).

**Request body (contoh sebagian):**
```json
{
  "kolektibilitas_slik": 1,
  "status_blacklist": "Tidak",
  "dti_ratio": 0.26,
  "plafon_diajukan": 200000000,
  "tenor_bulan": 36,
  "skala_usaha": "kecil",
  "jenis_kur": "kecil",
  "lama_usaha_bulan": 42,
  "rata_laba_bersih_bulanan": 23000000,
  "rata_saldo_harian": 18000000,
  "ada_agunan": "Ya",
  "jenis_agunan": "SHM",
  "nilai_agunan": 400000000
}
```

**Respons:**
```json
{
  "label_kode": 4,
  "label": "Disetujui langsung",
  "warna": "#1D9E75",
  "ikon": "✓✓",
  "probabilitas": {
    "Disetujui langsung": 0.8234,
    "Disetujui dengan syarat tambahan": 0.1102,
    "Perlu tinjauan komite": 0.0421,
    "Perlu perbaikan profil": 0.0198,
    "Ditolak otomatis": 0.0045
  },
  "fitur_count": 42
}
```

---

### `POST /extract`
Ekstraksi satu dokumen. Kirim sebagai `multipart/form-data`.

**Form fields:**
| Field | Tipe | Wajib | Keterangan |
|-------|------|-------|------------|
| `file` | File (PNG/JPG/WEBP/GIF) | Ya | Gambar dokumen |
| `doc_type` | String | Ya | `ktp` / `sku` / `rekening_koran` / `laporan_keuangan` |

**Respons sukses:**
```json
{
  "success": true,
  "doc_type": "ktp",
  "data": {
    "nik": "3171052503850001",
    "nama_lengkap": "Budi Santoso",
    "tempat_lahir": "Jakarta",
    "tanggal_lahir": "25-03-1985",
    "jenis_kelamin": "LAKI-LAKI",
    "alamat_ktp": "Jl. Kebon Jeruk No. 12",
    "status_perkawinan": "KAWIN",
    "pekerjaan": "WIRASWASTA"
  },
  "ml_fields": {
    "nik": "3171052503850001",
    "kota": "Jakarta"
  },
  "raw": "{ ...respons mentah Claude... }"
}
```

---

### `POST /extract-and-predict`
**Endpoint utama yang digunakan UI.** Upload beberapa dokumen sekaligus, sistem mengekstrak semua data, menggabungkannya dengan field manual, lalu langsung menjalankan prediksi.

**Form fields (`multipart/form-data`):**
| Field | Tipe | Wajib | Keterangan |
|-------|------|-------|------------|
| `ktp` | File gambar | Opsional | Gambar KTP |
| `sku` | File gambar | Opsional | Gambar SKU/NIB |
| `rekening_koran` | File gambar | Opsional | Gambar rekening koran |
| `laporan_keuangan` | File gambar | Opsional | Gambar laporan keuangan |
| `manual_fields` | JSON string | Opsional | Field tambahan yang tidak ada di dokumen |

Minimal salah satu dari field di atas harus diisi.

**Contoh `manual_fields`:**
```json
{
  "kolektibilitas_slik": 1,
  "plafon_diajukan": 200000000,
  "tenor_bulan": 36,
  "status_blacklist": "Tidak",
  "skala_usaha": "kecil",
  "jenis_kur": "kecil"
}
```

**Respons:**
```json
{
  "success": true,
  "extractions": {
    "ktp": { "success": true, "data": { "nik": "...", "nama_lengkap": "..." } },
    "rekening_koran": { "success": true, "data": { "total_kredit": "240000000", ... } }
  },
  "ml_fields": { "...semua field yang digunakan model..." },
  "prediction": {
    "label_kode": 3,
    "label": "Disetujui dengan syarat tambahan",
    "probabilitas": { "...distribusi per kelas..." }
  },
  "errors": []
}
```

---

### `POST /verify-nik` *(opsional)*
Validasi format NIK secara lokal (tidak memerlukan koneksi ke Dukcapil).

**Request body:**
```json
{
  "nik": "3171052503850001",
  "nama": "Budi Santoso",
  "tanggal_lahir": "25-03-1985"
}
```

**Respons:**
```json
{
  "mode": "identity_verification",
  "result": {
    "status": "SESUAI",
    "kesesuaian": true,
    "layer": "mock_dukcapil",
    "penjelasan": "⚠️ Ini adalah simulasi untuk development.",
    "decoded_nik": {
      "nama_provinsi": "DKI Jakarta",
      "tanggal_lahir": "25/03/1985",
      "jenis_kelamin": "LAKI-LAKI",
      "estimasi_umur": 41
    }
  }
}
```

---

## Dokumen yang Didukung

### KTP (e-KTP)
Field yang diekstrak: NIK, nama lengkap, tempat lahir, tanggal lahir, jenis kelamin, alamat, kelurahan, kecamatan, kota/kabupaten, provinsi, agama, status perkawinan, pekerjaan, berlaku hingga.

### SKU / NIB Usaha
Field yang diekstrak: nomor SKU, nama pemilik, nama usaha, jenis/bidang usaha, alamat usaha, tanggal terbit, penerbit (kelurahan/kecamatan), modal usaha, tanggal berdiri.

### Rekening Koran (min. 3 bulan)
Field yang diekstrak: nama nasabah, nomor rekening, nama bank, periode awal-akhir, total kredit (masuk) 3 bulan, total debit (keluar) 3 bulan, rata-rata saldo harian, saldo akhir, jumlah transaksi.

### Laporan Keuangan (Laba-Rugi)
Field yang diekstrak: nama usaha, periode laporan, rata-rata pendapatan bulanan, HPP per bulan, laba kotor per bulan, biaya operasional per bulan, rata-rata laba bersih per bulan.

**Format gambar yang didukung:** PNG, JPG/JPEG, WEBP, GIF

> **Tips kualitas ekstraksi:** Gunakan gambar dengan resolusi minimal 300 DPI, pencahayaan merata, dan teks yang tidak buram. Semakin jelas gambar, semakin akurat hasil ekstraksi.

---

## Kategori Output Model

Model menghasilkan salah satu dari 5 label berikut:

| Kode | Label | Warna | Profil Tipikal Pemohon |
|------|-------|-------|------------------------|
| 0 | **Ditolak Otomatis** | 🔴 Merah | Kolektibilitas >= 4 atau masuk blacklist. DTI sangat tinggi (> 0.70). Pengajuan ditutup otomatis. |
| 1 | **Perlu Perbaikan Profil** | 🟠 Amber | Usaha sangat baru (< 2 tahun), tidak ada NPWP/BPJS, DTI 0.50–0.90. Pemohon perlu perbaikan sebelum mengajukan kembali. |
| 2 | **Perlu Tinjauan Komite** | ⚫ Abu-abu | Kolektibilitas 2–3, DTI 0.35–0.55, ada kredit aktif signifikan. Memerlukan evaluasi analis dan komite kredit. |
| 3 | **Disetujui dengan Syarat Tambahan** | 🟢 Teal | Profil cukup baik namun ada kekurangan minor (agunan kurang, DTI 0.25–0.42). Bisa diproses dengan agunan tambahan atau penjamin. |
| 4 | **Disetujui Langsung** | 🟢 Hijau | Kolektibilitas 1, DTI <= 0.30, saldo sehat, lama usaha >= 3 tahun. Proses verifikasi dipercepat ke tahap pencairan. |

> **Catatan penting:** Output model adalah **rekomendasi seleksi awal**, bukan keputusan kredit final. Keputusan final tetap berada di tangan analis dan komite kredit manusia.

---

## Fitur Model ML

Berikut fitur-fitur yang paling berpengaruh terhadap prediksi model berdasarkan analisis SHAP:

| Fitur | Keterangan | Bobot Relatif |
|-------|------------|---------------|
| `kolektibilitas_slik` | Status kredit SLIK OJK (1=Lancar s.d. 5=Macet) | ⭐⭐⭐⭐⭐ |
| `status_blacklist` | Masuk daftar hitam perbankan (0/1) | ⭐⭐⭐⭐⭐ |
| `dti_ratio` | Debt-to-Income Ratio: cicilan / laba bersih | ⭐⭐⭐⭐ |
| `dscr` | Debt Service Coverage Ratio (fitur turunan) | ⭐⭐⭐⭐ |
| `rasio_saldo_plafon` | Rata-rata saldo harian / plafon diajukan | ⭐⭐⭐⭐ |
| `log_rata_laba_bersih_bulanan` | Log transform laba bersih bulanan | ⭐⭐⭐ |
| `lama_usaha_bulan` | Berapa bulan usaha sudah berjalan | ⭐⭐⭐ |
| `rasio_agunan_terhadap_plafon` | Coverage agunan terhadap plafon pinjaman | ⭐⭐⭐ |
| `kredit_lunas_sebelumnya` | Track record pelunasan kredit sebelumnya | ⭐⭐ |
| `skala_usaha_enc` | Skala usaha (mikro=1, kecil=2, menengah=3) | ⭐⭐ |
| `flag_high_risk` | Flag risiko tinggi: kol >= 3 atau blacklist (derived) | ⭐⭐ |
| `laba_margin_pct` | Margin laba bersih terhadap pendapatan (derived) | ⭐ |

**Fitur turunan** yang dibuat saat preprocessing:
```python
cicilan_estimasi    = plafon_diajukan / tenor_bulan * 1.05
dscr                = rata_laba_bersih_bulanan / cicilan_estimasi
rasio_saldo_plafon  = rata_saldo_harian / plafon_diajukan
laba_margin_pct     = rata_laba_bersih_bulanan / total_pendapatan_bulanan * 100
flag_high_risk      = 1 if (kolektibilitas_slik >= 3 or status_blacklist == 1) else 0
log_[kolom]         = log1p(nilai_kolom)  # untuk semua kolom monetari
```

---

## Deployment ke Render

### Persiapan sebelum deploy

**1. Ubah URL API di `index.html`**

Cari baris ini:
```javascript
const API = 'http://localhost:5000';
```
Ubah menjadi:
```javascript
const API = '';
```
Ini memastikan request dari browser diarahkan ke domain Render yang sama, bukan ke localhost.

**2. Pastikan file berikut ada di repository:**
- `app.py` (versi yang sudah diupdate dengan route `/` dan port dinamis)
- `requirements.txt`
- `render.yaml`
- `.gitignore` (pastikan `.env` dan `model_artifacts/` **tidak** dimasukkan)

> ⚠️ **Masalah ukuran file:** File `model_kredit_umkm.pkl` berukuran ~1 MB. GitHub memiliki batas 100 MB per file, jadi ini masih aman. Namun jika model semakin besar di masa depan, pertimbangkan Git LFS atau simpan model di cloud storage (S3/GCS) dan download saat startup.

### Langkah deploy

**1. Push ke GitHub**
```bash
git init
git add .
git commit -m "Initial commit: UMKM kredit ML system"
git remote add origin https://github.com/aDJi2003/umkm-kredit.git
git branch -M main
git push -u origin main
```

**2. Buat Web Service di Render**
- Buka [dashboard.render.com](https://dashboard.render.com) → **New → Web Service**
- Connect ke GitHub repository
- Isi konfigurasi:

| Setting | Nilai |
|---------|-------|
| Name | `umkm-kredit` |
| Region | Singapore (terdekat dari Indonesia) |
| Runtime | Python 3 |
| Branch | `main` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120` |
| Instance Type | Free |

**3. Tambahkan Environment Variables**

| Key | Value |
|-----|-------|
| `ANTHROPIC_API_KEY` | `sk-ant-api03-xxxxxxxxxx` |
| `PYTHON_VERSION` | `3.11.0` |

**4. Deploy**

Klik **Create Web Service**. Proses build pertama memakan waktu 5–10 menit. Setelah selesai, URL aplikasi tersedia di format: `https://umkm-kredit.onrender.com`

### Mencegah sleep di free tier

Free tier Render mematikan service setelah 15 menit tidak ada request. Gunakan [UptimeRobot](https://uptimerobot.com) (gratis) untuk ping otomatis setiap 5 menit:

1. Daftar di uptimerobot.com
2. **Add New Monitor → HTTP(s)**
3. URL: `https://umkm-kredit.onrender.com/health`
4. Monitoring interval: **5 minutes**
5. Klik **Create Monitor**

### Perbandingan deployment options

| Platform | Biaya | Kelebihan | Kekurangan |
|----------|-------|-----------|------------|
| Render (free) | Gratis | Mudah setup, auto-deploy dari GitHub | Sleep setelah 15 menit idle, RAM terbatas |
| Render (starter) | $7/bulan | Tidak sleep, performa lebih baik | Berbayar |
| VPS Nevacloud | Rp 84.000/bulan | Server Indonesia, kontrol penuh | Perlu setup manual Nginx, Gunicorn, SSL |

---

## Troubleshooting

### Jalankan diagnosis terlebih dahulu

Sebelum mencari masalah secara manual, selalu jalankan:
```bash
python diagnose.py
```
Script ini mengecek 8 komponen sekaligus dan menunjukkan persis di mana masalahnya.

---

### Status API merah / "API offline" di UI

| Penyebab | Solusi |
|----------|--------|
| `app.py` belum dijalankan | Buka terminal di folder proyek, jalankan `python app.py` |
| Port 5000 sudah dipakai | Di Windows: `netstat -ano \| findstr :5000`, lalu tutup prosesnya |
| Virtual environment tidak aktif | Aktifkan dulu: `venv\Scripts\activate` (Windows) atau `source venv/bin/activate` (Mac/Linux) |

---

### Ekstraksi dokumen gagal

| Error | Penyebab | Solusi |
|-------|----------|--------|
| `credit balance is too low` | Saldo Anthropic habis | Top up di [console.anthropic.com → Billing → Buy Credits](https://console.anthropic.com) |
| `AuthenticationError` | API key salah atau tidak ada | Cek file `.env`, pastikan key dimulai dengan `sk-ant-` tanpa spasi |
| `Gagal` tanpa detail | .env tidak terbaca | Jalankan `python diagnose.py` untuk cek detail error di terminal `app.py` |
| Hasil ekstraksi tidak akurat | Kualitas gambar rendah | Gunakan foto yang terang, tidak buram, min 300 DPI |
| Format tidak didukung | File bukan gambar | Konversi ke PNG/JPG/WEBP terlebih dahulu |

---

### Model tidak termuat saat `app.py` dijalankan

| Penyebab | Solusi |
|----------|--------|
| `model_artifacts/` tidak ada | Jalankan semua cell di `umkm_kredit_ml.ipynb` |
| Versi `scikit-learn` berbeda dari saat training | `pip install scikit-learn==1.3.0` |
| File `.pkl` corrupt | Hapus folder `model_artifacts/` dan latih ulang dari notebook |

---

### Error instalasi library

| Error | Solusi |
|-------|--------|
| `lightgbm` gagal install di Windows | Install [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) |
| Konflik versi antar library | Gunakan virtual environment yang bersih |
| `xgboost` error di Python 3.12 | Coba `pip install xgboost --pre` atau downgrade ke Python 3.11 |

---

### Deployment ke Render gagal

| Error di log Render | Solusi |
|--------------------|--------|
| `ModuleNotFoundError` | Pastikan semua library ada di `requirements.txt` |
| `Model tidak termuat` | File `model_artifacts/*.pkl` harus ada di repository (tidak di `.gitignore`) |
| `Port already in use` | Pastikan start command menggunakan `$PORT`: `gunicorn app:app --bind 0.0.0.0:$PORT` |
| Build timeout | Tambah `--timeout 120` ke start command gunicorn |

---

## Roadmap Production

Sistem saat ini adalah **prototype fungsional**. Berikut yang perlu dilakukan untuk membawanya ke production nyata:

### Fase 1 — Infrastruktur & Keamanan 🔴 *Prioritas tinggi*
- [ ] Deploy ke cloud server dengan HTTPS (SSL certificate via Let's Encrypt)
- [ ] Tambahkan database PostgreSQL untuk menyimpan setiap pengajuan, ekstraksi, dan prediksi
- [ ] Implementasi autentikasi JWT dengan role: pemohon, analis, komite, admin
- [ ] Enkripsi data sensitif (NIK, nama, data keuangan) sesuai **UU PDP No. 27 Tahun 2022**
- [ ] Pindahkan penyimpanan gambar dokumen ke object storage (S3/GCS) dengan akses terbatas
- [ ] Implementasi audit trail: setiap prediksi dicatat dengan timestamp, input features, dan output

### Fase 2 — Peningkatan Model ML 🟡 *Prioritas sedang*
- [ ] Ganti 1.000 baris data dummy dengan data historis kredit nyata
- [ ] Setup retraining pipeline otomatis bulanan dengan MLflow untuk experiment tracking
- [ ] Monitoring model drift menggunakan Evidently AI atau WhyLogs
- [ ] Audit bias model: pastikan tidak diskriminatif berdasarkan wilayah atau demografi
- [ ] Tambahkan SHAP explanation per pengajuan individual untuk transparansi kepada pemohon
- [ ] A/B testing sebelum deploy model baru ke seluruh traffic

### Fase 3 — Integrasi Layanan Eksternal 🟡 *Prioritas sedang*
- [ ] **Integrasi API SLIK OJK** — pull kolektibilitas otomatis (saat ini masih input manual)
- [ ] **e-KYC via API Dukcapil** — verifikasi NIK + nama + tanggal lahir secara real-time
  > Memerlukan MoU dengan Kemendagri + izin OJK + jaringan leased line TELKOM
  > Referensi: Permendagri No. 102 Tahun 2019
- [ ] Validasi NIB ke sistem OSS Kemenko Perekonomian
- [ ] Verifikasi NPWP ke Ditjen Pajak (DJP Online) via PKS
- [ ] Notifikasi pemohon via SMS/WhatsApp/email otomatis (Twilio/Vonage)
- [ ] Integrasi core banking untuk trigger pencairan otomatis setelah persetujuan

### Fase 4 — Skalabilitas 🟢 *Prioritas rendah*
- [ ] Pindahkan ekstraksi dokumen ke background job (Celery + Redis) agar UI tidak blocking
- [ ] Pisahkan ML inference ke dedicated service (FastAPI) yang bisa di-scale horizontal
- [ ] Caching hasil ekstraksi dokumen yang sama di Redis (hemat biaya Anthropic API)
- [ ] CI/CD pipeline dengan GitHub Actions untuk deployment otomatis

---

## Regulasi yang Relevan

Sistem ini dirancang dengan mempertimbangkan regulasi keuangan Indonesia berikut:

| Regulasi | Relevansi |
|----------|-----------|
| **UU No. 10 Tahun 1998** tentang Perbankan | Dasar hukum perkreditan perbankan |
| **UU No. 4 Tahun 2023** (UU P2SK) | Pengembangan dan penguatan sektor keuangan |
| **UU No. 27 Tahun 2022** (UU PDP) | Perlindungan data pribadi — wajib dipatuhi untuk NIK dan data keuangan |
| **POJK No. 19 Tahun 2025** | Kemudahan akses pembiayaan UMKM |
| **POJK No. 22 Tahun 2023** | Perlindungan konsumen sektor jasa keuangan |
| **POJK No. 40/POJK.03/2019** | Penilaian kualitas aset bank umum (dasar kolektibilitas 1–5) |
| **Permendagri No. 102 Tahun 2019** | Syarat akses data Dukcapil untuk lembaga keuangan |
| **Permenko Perekonomian No. 2 Tahun 2021** | Ketentuan Kredit Usaha Rakyat (KUR) |

---

## Tautan Penting

| Layanan | URL | Keterangan |
|---------|-----|------------|
| Anthropic Console | [console.anthropic.com](https://console.anthropic.com) | Kelola API key, monitor penggunaan, top up kredit |
| Anthropic Docs | [docs.anthropic.com](https://docs.anthropic.com) | Dokumentasi Claude API dan Vision API |
| Render Dashboard | [dashboard.render.com](https://dashboard.render.com) | Deploy dan monitor aplikasi |
| UptimeRobot | [uptimerobot.com](https://uptimerobot.com) | Monitoring uptime gratis, cegah sleep Render |
| SLIK OJK | [konsumen.ojk.go.id](https://konsumen.ojk.go.id) | Portal SLIK OJK |
| OSS Indonesia | [oss.go.id](https://oss.go.id) | Verifikasi NIB usaha |

---

## Lisensi

Proyek ini dilisensikan di bawah [MIT License](LICENSE).
