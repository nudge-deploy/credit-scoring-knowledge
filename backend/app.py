from dotenv import load_dotenv
load_dotenv()

"""
app.py — API Kredit UMKM dengan Document Extraction
====================================================
Endpoint:
  GET  /              serve index.html (halaman utama)
  GET  /health        health check API
  GET  /version       app version & status info
  POST /predict       inferensi dari field JSON
  GET  /fields        definisi field form
  POST /extract       ekstrak dokumen (multipart image upload)
  POST /extract-and-predict   upload semua dokumen → langsung predict
"""

import json, os, sys, warnings
import joblib, numpy as np, pandas as pd
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extractor import extract_document

warnings.filterwarnings("ignore")

app = Flask(__name__)
CORS(app)

# ── Load artefak ─────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS = os.path.join(BASE_DIR, "model_artifacts")

# ── Load version ──────────────────────────────────────────────────
try:
    with open(os.path.join(BASE_DIR, "VERSION")) as f:
        APP_VERSION = f.read().strip()
except Exception as e:
    APP_VERSION = "unknown"
    print(f"⚠️  Versi tidak ditemukan: {e}")

try:
    model  = joblib.load(os.path.join(ARTIFACTS, "model_kredit_umkm.pkl"))
    scaler = joblib.load(os.path.join(ARTIFACTS, "scaler_kredit_umkm.pkl"))
    with open(os.path.join(ARTIFACTS, "model_metadata.json")) as f:
        metadata = json.load(f)
    print(f"✅  Model dimuat: {metadata['model_name']}  |  F1: {metadata['test_f1_macro']}")
except Exception as e:
    print(f"❌  Gagal memuat model: {e}")
    model = scaler = metadata = None

# ── Konstanta transformasi ────────────────────────────────────────
SKALA_MAP   = {"mikro": 1, "kecil": 2, "menengah": 3}
BINARY_COLS = ["ada_npwp", "ada_bpjs_tk", "status_blacklist", "ada_agunan"]
LOG_COLS    = [
    "plafon_diajukan", "modal_usaha", "total_pendapatan_bulanan",
    "rata_laba_bersih_bulanan", "rata_saldo_harian",
    "total_kredit_aktif_slik", "nilai_agunan",
    "total_kredit_3bln", "total_debit_3bln", "cicilan_estimasi",
]
SEKTOR_MAP  = {
    "01111": "pertanian", "10311": "industri", "14111": "industri",
    "43211": "jasa",      "47211": "perdagangan", "47711": "perdagangan",
    "49431": "jasa",      "56101": "perdagangan", "62011": "jasa", "96011": "jasa",
}
LABEL_META  = {
    0: {"warna": "#E24B4A", "ikon": "✕"},
    1: {"warna": "#EF9F27", "ikon": "⚠"},
    2: {"warna": "#888780", "ikon": "◎"},
    3: {"warna": "#5DCAA5", "ikon": "✓"},
    4: {"warna": "#1D9E75", "ikon": "✓✓"},
}

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"}


# ── Preprocessing ─────────────────────────────────────────────────
def preprocess(raw: dict) -> pd.DataFrame:
    row = pd.DataFrame([raw])
    for col in BINARY_COLS:
        if col in row.columns:
            val = str(row[col].iloc[0]).strip().lower()
            row[col] = 1 if val in ("ya", "yes", "1", "true") else 0
    row["skala_usaha_enc"] = (
        row["skala_usaha"].map(SKALA_MAP).fillna(1).astype(int)
        if "skala_usaha" in row.columns else 1
    )
    for cat in ["super_mikro", "mikro", "kecil", "khusus"]:
        row[f"kur_{cat}"] = int(
            str(row.get("jenis_kur", pd.Series(["mikro"])).iloc[0]) == cat)
    for cat in ["SHM", "SHGB", "BPKB", "Tidak ada"]:
        cn = f"agunan_{cat.lower().replace(' ', '_')}"
        row[cn] = int(
            str(row.get("jenis_agunan", pd.Series(["Tidak ada"])).iloc[0]) == cat)
    kbli   = str(row.get("kbli_kode", pd.Series(["47211"])).iloc[0])
    sektor = SEKTOR_MAP.get(kbli, "lainnya")
    for s in ["pertanian", "industri", "jasa", "perdagangan", "lainnya"]:
        row[f"sektor_{s}"] = int(sektor == s)

    plafon     = float(row.get("plafon_diajukan",          pd.Series([1])).iloc[0])
    tenor      = float(row.get("tenor_bulan",              pd.Series([12])).iloc[0])
    laba       = float(row.get("rata_laba_bersih_bulanan", pd.Series([0])).iloc[0])
    saldo      = float(row.get("rata_saldo_harian",        pd.Series([0])).iloc[0])
    pendapatan = float(row.get("total_pendapatan_bulanan", pd.Series([1])).iloc[0])
    kol        = int(row.get("kolektibilitas_slik",        pd.Series([1])).iloc[0])
    blacklist  = int(row.get("status_blacklist",           pd.Series([0])).iloc[0])

    cicilan = plafon / max(tenor, 1) * 1.05
    row["cicilan_estimasi"]   = cicilan
    row["dscr"]               = round(laba / max(cicilan, 1), 4)
    row["rasio_saldo_plafon"] = round(saldo / max(plafon, 1), 4)
    row["laba_margin_pct"]    = round(laba / max(pendapatan, 1) * 100, 2)
    row["flag_high_risk"]     = int(kol >= 3 or blacklist == 1)
    for col in LOG_COLS:
        val = float(row[col].iloc[0]) if col in row.columns else 0
        row[f"log_{col}"] = np.log1p(max(val, 0))

    feat = metadata["feature_names"]
    for col in feat:
        if col not in row.columns:
            row[col] = 0
    return row[feat].fillna(0)


def run_predict(payload: dict) -> dict:
    if model is None:
        return {"error": "Model tidak tersedia"}
    X    = preprocess(payload)
    X_sc = scaler.transform(X)
    pred = int(model.predict(X_sc)[0])
    proba = model.predict_proba(X_sc)[0]
    label_names = {int(k): v for k, v in metadata["label_names"].items()}
    proba_sorted = dict(sorted(
        {label_names[i]: round(float(p), 4) for i, p in enumerate(proba)}.items(),
        key=lambda x: -x[1]
    ))
    return {
        "label_kode"  : pred,
        "label"       : label_names[pred],
        "warna"       : LABEL_META[pred]["warna"],
        "ikon"        : LABEL_META[pred]["ikon"],
        "probabilitas": proba_sorted,
        "fitur_count" : len(metadata["feature_names"]),
    }


# ─────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────

# ── Serve halaman utama ───────────────────────────────────────────
@app.route("/")
def serve_index():
    """Serve index.html langsung dari root folder."""
    return send_from_directory(BASE_DIR, "index.html")


# ── Health check (pindah ke /health agar "/" bebas untuk HTML) ───
@app.route("/health", methods=["GET"])
def health():
    if model is None:
        return jsonify({"status": "error", "pesan": "Model tidak termuat"}), 500
    return jsonify({
        "status"    : "ok",
        "model"     : metadata["model_name"],
        "f1_macro"  : metadata["test_f1_macro"],
        "n_features": metadata["n_features"],
    })


# ── Version check ─────────────────────────────────────────────────
@app.route("/version", methods=["GET"])
def version():
    return jsonify({
        "app_version": APP_VERSION,
        "model_name": metadata["model_name"] if metadata else "unknown",
        "environment": "production" if os.environ.get("VERCEL") else "development",
        "api_ready": model is not None,
    })


@app.route("/fields", methods=["GET"])
def fields():
    return jsonify(FORM_FIELDS)


@app.route("/predict", methods=["POST"])
def predict():
    if model is None:
        return jsonify({"error": "Model tidak tersedia"}), 503
    body = request.get_json(force=True)
    if not body:
        return jsonify({"error": "Body JSON kosong"}), 400
    try:
        result = run_predict(body)
        if "error" in result:
            return jsonify(result), 503
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/extract", methods=["POST"])
def extract():
    if "file" not in request.files:
        return jsonify({"error": "Tidak ada file yang diupload"}), 400
    f        = request.files["file"]
    doc_type = request.form.get("doc_type", "").strip().lower()
    if not doc_type:
        return jsonify({"error": "Parameter doc_type wajib diisi"}), 400
    media_type = f.content_type or "image/png"
    if media_type not in ALLOWED_TYPES:
        return jsonify({"error": f"Format file tidak didukung: {media_type}"}), 400
    image_bytes = f.read()
    result = extract_document(image_bytes, doc_type, media_type)
    return jsonify(result)


@app.route("/extract-and-predict", methods=["POST"])
def extract_and_predict():
    doc_keys    = ["ktp", "sku", "rekening_koran", "laporan_keuangan"]
    extractions = {}
    ml_combined = {}
    errors      = []

    for dk in doc_keys:
        if dk not in request.files:
            continue
        f          = request.files[dk]
        media_type = f.content_type or "image/png"
        if media_type not in ALLOWED_TYPES:
            errors.append(f"{dk}: format tidak didukung ({media_type})")
            continue
        image_bytes = f.read()
        result = extract_document(image_bytes, dk, media_type)
        extractions[dk] = result
        if result.get("success"):
            ml_combined.update(result.get("ml_fields", {}))
        else:
            errors.append(f"{dk}: {result.get('error', 'gagal')}")

    manual_raw = request.form.get("manual_fields", "{}")
    try:
        manual = json.loads(manual_raw)
        ml_combined.update(manual)
    except json.JSONDecodeError:
        errors.append("manual_fields bukan JSON valid, diabaikan.")

    if not ml_combined:
        return jsonify({
            "success": False,
            "error"  : "Tidak ada data yang berhasil diekstrak atau diinput.",
            "errors" : errors,
        }), 400

    defaults = {
        "skala_usaha": "kecil", "jenis_kur": "kecil", "kbli_kode": "47211",
        "lama_usaha_bulan": 24, "modal_usaha": 500_000_000,
        "plafon_diajukan": 200_000_000, "tenor_bulan": 36,
        "jumlah_tanggungan": 2, "ada_npwp": "Ya", "ada_bpjs_tk": "Tidak",
        "total_pendapatan_bulanan": 60_000_000, "hpp_bulanan": 35_000_000,
        "laba_kotor_bulanan": 25_000_000, "biaya_operasional_bulanan": 10_000_000,
        "rata_laba_bersih_bulanan": 15_000_000, "rata_saldo_harian": 10_000_000,
        "total_kredit_3bln": 180_000_000, "total_debit_3bln": 150_000_000,
        "kolektibilitas_slik": 1, "total_kredit_aktif_slik": 0,
        "jumlah_fasilitas_slik": 0, "status_blacklist": "Tidak",
        "kredit_lunas_sebelumnya": 0, "ada_agunan": "Ya", "jenis_agunan": "SHM",
        "nilai_agunan": 300_000_000, "rasio_agunan_terhadap_plafon": 1.5,
        "dti_ratio": 0.3,
    }
    for k, v in defaults.items():
        if k not in ml_combined:
            ml_combined[k] = v

    try:
        prediction = run_predict(ml_combined)
        return jsonify({
            "success"    : True,
            "extractions": {k: {"success": v.get("success"), "data": v.get("data")}
                            for k, v in extractions.items()},
            "ml_fields"  : ml_combined,
            "prediction" : prediction,
            "errors"     : errors,
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error"  : str(e),
            "errors" : errors,
        }), 500


# ── Form field definitions ────────────────────────────────────────
FORM_FIELDS = [
    {"group": "Identitas Usaha", "key": "skala_usaha",        "label": "Skala usaha",             "type": "select", "options": ["mikro","kecil","menengah"], "default": "kecil"},
    {"group": "Identitas Usaha", "key": "jenis_kur",           "label": "Jenis KUR",                "type": "select", "options": ["super_mikro","mikro","kecil","khusus"], "default": "kecil"},
    {"group": "Identitas Usaha", "key": "kbli_kode",           "label": "Kode KBLI",                "type": "select", "options": ["47211","56101","14111","47711","10311","01111","43211","62011","49431","96011"], "default": "47211"},
    {"group": "Identitas Usaha", "key": "lama_usaha_bulan",    "label": "Lama usaha (bulan)",        "type": "number", "min": 1,   "max": 360,  "default": 36},
    {"group": "Identitas Usaha", "key": "modal_usaha",         "label": "Modal usaha (Rp)",          "type": "number", "min": 0,   "max": None, "default": 500000000},
    {"group": "Identitas Usaha", "key": "jumlah_tanggungan",   "label": "Jumlah tanggungan",         "type": "number", "min": 0,   "max": 10,   "default": 2},
    {"group": "Pengajuan Kredit","key": "plafon_diajukan",     "label": "Plafon diajukan (Rp)",      "type": "number", "min": 1000000, "max": None, "default": 200000000},
    {"group": "Pengajuan Kredit","key": "tenor_bulan",         "label": "Tenor (bulan)",             "type": "select", "options": [12,24,36,48,60], "default": 36},
    {"group": "Keuangan Usaha",  "key": "total_pendapatan_bulanan",  "label": "Pendapatan bulanan (Rp)",   "type": "number", "min": 0, "max": None, "default": 80000000},
    {"group": "Keuangan Usaha",  "key": "hpp_bulanan",               "label": "HPP bulanan (Rp)",          "type": "number", "min": 0, "max": None, "default": 45000000},
    {"group": "Keuangan Usaha",  "key": "laba_kotor_bulanan",        "label": "Laba kotor bulanan (Rp)",   "type": "number", "min": 0, "max": None, "default": 35000000},
    {"group": "Keuangan Usaha",  "key": "biaya_operasional_bulanan", "label": "Biaya operasional (Rp)",    "type": "number", "min": 0, "max": None, "default": 12000000},
    {"group": "Keuangan Usaha",  "key": "rata_laba_bersih_bulanan",  "label": "Laba bersih rata-rata (Rp)","type": "number", "min": 0, "max": None, "default": 23000000},
    {"group": "Rekening & Arus Kas", "key": "rata_saldo_harian",   "label": "Rata-rata saldo harian (Rp)", "type": "number", "min": 0, "max": None, "default": 18000000},
    {"group": "Rekening & Arus Kas", "key": "total_kredit_3bln",   "label": "Total kredit 3 bulan (Rp)",   "type": "number", "min": 0, "max": None, "default": 240000000},
    {"group": "Rekening & Arus Kas", "key": "total_debit_3bln",    "label": "Total debit 3 bulan (Rp)",    "type": "number", "min": 0, "max": None, "default": 190000000},
    {"group": "Riwayat Kredit (SLIK OJK)", "key": "kolektibilitas_slik",     "label": "Kolektibilitas SLIK",          "type": "select", "options": [1,2,3,4,5], "default": 1},
    {"group": "Riwayat Kredit (SLIK OJK)", "key": "total_kredit_aktif_slik", "label": "Total kredit aktif SLIK (Rp)", "type": "number", "min": 0, "max": None, "default": 15000000},
    {"group": "Riwayat Kredit (SLIK OJK)", "key": "jumlah_fasilitas_slik",   "label": "Jumlah fasilitas aktif",       "type": "number", "min": 0, "max": 10,   "default": 1},
    {"group": "Riwayat Kredit (SLIK OJK)", "key": "status_blacklist",        "label": "Masuk blacklist?",             "type": "select", "options": ["Tidak","Ya"], "default": "Tidak"},
    {"group": "Riwayat Kredit (SLIK OJK)", "key": "kredit_lunas_sebelumnya", "label": "Kredit lunas sebelumnya",      "type": "number", "min": 0, "max": 10,   "default": 1},
    {"group": "Dokumen & Agunan", "key": "ada_npwp",    "label": "Memiliki NPWP?",    "type": "select", "options": ["Ya","Tidak"], "default": "Ya"},
    {"group": "Dokumen & Agunan", "key": "ada_bpjs_tk", "label": "Memiliki BPJS TK?", "type": "select", "options": ["Ya","Tidak"], "default": "Ya"},
    {"group": "Dokumen & Agunan", "key": "ada_agunan",  "label": "Ada agunan?",        "type": "select", "options": ["Ya","Tidak"], "default": "Ya"},
    {"group": "Dokumen & Agunan", "key": "jenis_agunan","label": "Jenis agunan",       "type": "select", "options": ["SHM","SHGB","BPKB","Tidak ada"], "default": "SHM"},
    {"group": "Dokumen & Agunan", "key": "nilai_agunan","label": "Nilai agunan (Rp)",  "type": "number", "min": 0, "max": None, "default": 400000000},
    {"group": "Dokumen & Agunan", "key": "rasio_agunan_terhadap_plafon", "label": "Rasio agunan / plafon", "type": "number", "min": 0, "max": 5, "default": 1.6},
    {"group": "Dokumen & Agunan", "key": "dti_ratio",   "label": "DTI ratio (0–2)",   "type": "number", "min": 0, "max": 3,   "default": 0.26},
]


if __name__ == "__main__":
    # Render menyediakan PORT via environment variable
    # Locally tetap jalan di 5000
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("RENDER") is None  # debug=False di Render
    print(f"\n{'═'*52}")
    print(f"  API Kredit UMKM  →  http://localhost:{port}")
    print(f"  Environment      :  {'Render (production)' if not debug else 'Local (development)'}")
    print(f"{'═'*52}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)