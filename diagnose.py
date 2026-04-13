"""
diagnose.py — Script Diagnosis Sistem Kredit UMKM
==================================================
Jalankan di folder proyek Anda:
    python diagnose.py

Script ini akan mengecek:
  1. Versi Python
  2. Semua library yang diperlukan
  3. Keberadaan model_artifacts/
  4. ANTHROPIC_API_KEY (environment variable & .env file)
  5. Konektivitas ke Anthropic API (text)
  6. Konektivitas ke Anthropic API (vision/image)
  7. Struktur folder sample_docs/
"""

import os, sys, json, base64, traceback

SEP  = "─" * 55
OK   = "  ✅"
FAIL = "  ❌"
WARN = "  ⚠️ "
INFO = "  ℹ️ "

def section(title):
    print(f"\n{'═'*55}")
    print(f"  {title}")
    print('═'*55)

def ok(msg):   print(f"{OK}  {msg}")
def fail(msg): print(f"{FAIL}  {msg}")
def warn(msg): print(f"{WARN}  {msg}")
def info(msg): print(f"{INFO}  {msg}")


# ── 1. Python version ────────────────────────────────────────────
section("1. Versi Python")
pv = sys.version_info
if pv >= (3, 8):
    ok(f"Python {pv.major}.{pv.minor}.{pv.micro}")
else:
    fail(f"Python {pv.major}.{pv.minor} — perlu minimal Python 3.8")

# ── 2. Library check ─────────────────────────────────────────────
section("2. Library yang diperlukan")
REQUIRED = {
    "flask"       : "Flask",
    "flask_cors"  : "flask-cors",
    "pandas"      : "pandas",
    "numpy"       : "numpy",
    "sklearn"     : "scikit-learn",
    "joblib"      : "joblib",
    "anthropic"   : "anthropic",
    "PIL"         : "Pillow (opsional, untuk generate dokumen dummy)",
}
missing = []
for module, pkg in REQUIRED.items():
    try:
        m = __import__(module)
        ver = getattr(m, "__version__", "?")
        ok(f"{pkg} ({ver})")
    except ImportError:
        fail(f"{pkg} — BELUM TERINSTALL")
        if module != "PIL":
            missing.append(pkg)

if missing:
    print(f"\n  Jalankan perintah ini untuk install yang kurang:")
    print(f"  pip install {' '.join(missing)}")

# ── 3. Model artifacts ───────────────────────────────────────────
section("3. File model ML")
ARTIFACTS = [
    "model_artifacts/model_kredit_umkm.pkl",
    "model_artifacts/scaler_kredit_umkm.pkl",
    "model_artifacts/model_metadata.json",
]
all_artifacts_ok = True
for path in ARTIFACTS:
    if os.path.exists(path):
        size = os.path.getsize(path) / 1024
        ok(f"{path} ({size:.1f} KB)")
    else:
        fail(f"{path} — TIDAK DITEMUKAN")
        all_artifacts_ok = False

if not all_artifacts_ok:
    warn("Jalankan semua cell di notebook umkm_kredit_ml.ipynb terlebih dahulu.")

# ── 4. API Key ───────────────────────────────────────────────────
section("4. Anthropic API Key")

api_key = None

# 4a. Cek environment variable
env_key = os.environ.get("ANTHROPIC_API_KEY", "")
if env_key:
    if env_key.startswith("sk-ant-"):
        masked = env_key[:14] + "..." + env_key[-4:]
        ok(f"Environment variable ditemukan: {masked}")
        api_key = env_key
    else:
        fail(f"Key ditemukan tapi formatnya salah (harus diawali sk-ant-)")
        fail(f"Nilai saat ini: '{env_key[:20]}...'")
else:
    fail("ANTHROPIC_API_KEY tidak ditemukan di environment variable")
    info("Di PowerShell jalankan: $env:ANTHROPIC_API_KEY='sk-ant-...'")
    info("Di CMD jalankan       : set ANTHROPIC_API_KEY=sk-ant-...")

# 4b. Cek .env file
env_file_key = None
if os.path.exists(".env"):
    ok(".env file ditemukan")
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if line.startswith("ANTHROPIC_API_KEY"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    env_file_key = parts[1].strip().strip('"').strip("'")
                    if env_file_key.startswith("sk-ant-"):
                        masked = env_file_key[:14] + "..." + env_file_key[-4:]
                        ok(f"Key di .env file: {masked}")
                        if not api_key:
                            api_key = env_file_key
                            # Load it into environment
                            os.environ["ANTHROPIC_API_KEY"] = api_key
                            info("Key dari .env file dimuat ke environment.")
                    else:
                        fail(f"Key di .env formatnya salah: '{env_file_key[:20]}'")
    if not env_file_key:
        warn(".env ada tapi tidak ada baris ANTHROPIC_API_KEY=...")
else:
    warn(".env file tidak ditemukan (opsional, tapi direkomendasikan)")
    info("Buat file .env di folder ini dengan isi:")
    info("  ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx")

if not api_key:
    fail("Tidak ada API key yang valid ditemukan. Lewati test koneksi.")
    print()

# ── 5. Test koneksi API (text) ───────────────────────────────────
section("5. Test koneksi Anthropic API (text)")
if not api_key:
    warn("Dilewati — tidak ada API key.")
else:
    try:
        import anthropic as ac
        client = ac.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=30,
            messages=[{"role":"user","content":"Balas hanya dengan: OK"}]
        )
        reply = msg.content[0].text.strip()
        ok(f"API text berhasil. Respons: '{reply}'")
        ok(f"Model: claude-haiku-4-5-20251001")
        info(f"Input tokens: {msg.usage.input_tokens} | Output tokens: {msg.usage.output_tokens}")
    except ac.AuthenticationError:
        fail("AuthenticationError — API key salah atau tidak aktif")
        fail("Cek kembali key di: console.anthropic.com/settings/keys")
    except ac.PermissionDeniedError:
        fail("PermissionDeniedError — akun belum punya akses atau kredit habis")
        fail("Cek billing di: console.anthropic.com/settings/billing")
    except ac.APIConnectionError as e:
        fail(f"APIConnectionError — tidak bisa terhubung ke internet")
        fail(f"Detail: {e}")
    except ac.RateLimitError:
        warn("RateLimitError — terlalu banyak request. Tunggu sebentar dan coba lagi.")
    except Exception as e:
        fail(f"Error tidak terduga: {type(e).__name__}: {e}")
        traceback.print_exc()

# ── 6. Test koneksi API (vision/image) ──────────────────────────
section("6. Test Anthropic API dengan gambar (vision)")
if not api_key:
    warn("Dilewati — tidak ada API key.")
else:
    try:
        import anthropic as ac
        from PIL import Image
        import io

        # Buat gambar test 1x1 pixel putih
        img = Image.new('RGB', (100, 30), color='white')
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.text((5, 8), "TEST IMAGE", fill='black')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        img_bytes = buf.getvalue()
        img_b64 = base64.standard_b64encode(img_bytes).decode()

        client = ac.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=30,
            messages=[{
                "role": "user",
                "content": [
                    {"type":"image","source":{"type":"base64","media_type":"image/png","data":img_b64}},
                    {"type":"text","text":"Apa yang ada di gambar ini? Jawab 1 kalimat singkat."}
                ]
            }]
        )
        reply = msg.content[0].text.strip()
        ok(f"API vision berhasil.")
        ok(f"Deskripsi gambar test: '{reply[:80]}'")
    except ac.AuthenticationError:
        fail("AuthenticationError pada vision — key tidak valid")
    except Exception as e:
        fail(f"Vision test gagal: {type(e).__name__}: {e}")

# ── 7. Sample docs ───────────────────────────────────────────────
section("7. Dokumen dummy (sample_docs/)")
SAMPLE_DOCS = [
    ("sample_docs/ktp_budi_santoso.png",         "KTP"),
    ("sample_docs/sku_toko_sembako.png",          "SKU"),
    ("sample_docs/rekening_koran_bri.png",        "Rekening Koran"),
    ("sample_docs/laporan_keuangan_sembako.png",  "Laporan Keuangan"),
]
for path, label in SAMPLE_DOCS:
    if os.path.exists(path):
        size = os.path.getsize(path) / 1024
        ok(f"{label}: {path} ({size:.1f} KB)")
    else:
        warn(f"{label}: {path} tidak ditemukan — akan dibuat ulang")

# ── 8. Test extraction satu dokumen ─────────────────────────────
section("8. Test extraction dokumen KTP")
if not api_key:
    warn("Dilewati — tidak ada API key.")
elif not os.path.exists("sample_docs/ktp_budi_santoso.png"):
    warn("Dilewati — file sample KTP tidak ditemukan.")
elif not os.path.exists("extractor.py"):
    warn("Dilewati — extractor.py tidak ditemukan di folder ini.")
else:
    try:
        sys.path.insert(0, os.getcwd())
        from extractor import extract_document
        with open("sample_docs/ktp_budi_santoso.png", "rb") as f:
            img_bytes = f.read()
        info("Mengirim gambar KTP ke Claude Vision API...")
        result = extract_document(img_bytes, "ktp", "image/png")
        if result.get("success"):
            ok("Ekstraksi KTP berhasil!")
            data = result.get("data", {})
            for k, v in list(data.items())[:5]:
                info(f"  {k}: {v}")
            ok(f"ML fields yang dihasilkan: {result.get('ml_fields', {})}")
        else:
            fail(f"Ekstraksi gagal: {result.get('error','?')}")
            if result.get("raw"):
                info(f"Respons mentah Claude: {result['raw'][:200]}")
    except Exception as e:
        fail(f"Test extraction error: {type(e).__name__}: {e}")
        traceback.print_exc()

# ── Summary ──────────────────────────────────────────────────────
section("Ringkasan")
if api_key:
    ok("API key ditemukan dan valid format")
else:
    fail("API key TIDAK ditemukan — ini kemungkinan besar penyebab utama kegagalan")
    print()
    print("  SOLUSI CEPAT:")
    print("  1. Buat file bernama  .env  di folder proyek Anda")
    print("  2. Isi dengan satu baris:")
    print("     ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxx")
    print("  3. Tambahkan di baris paling atas app.py:")
    print("     from dotenv import load_dotenv")
    print("     load_dotenv()")
    print("  4. Install dotenv: pip install python-dotenv")
    print("  5. Restart app.py")
print()
print("  Jika masih gagal setelah langkah di atas, cek log terminal")
print("  tempat app.py berjalan — error detail akan muncul di sana.")
print()