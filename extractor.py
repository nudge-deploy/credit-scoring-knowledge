"""
extractor.py — Document Extraction Engine
==========================================
Menggunakan Claude Vision API untuk mengekstrak data terstruktur
dari gambar dokumen UMKM (KTP, SKU/NIB, Rekening Koran, Laporan Keuangan).

Cara pakai:
    from extractor import extract_document
    result = extract_document(image_bytes, doc_type='ktp')
    # result = { 'success': True, 'data': {...}, 'raw': '...' }
"""

import base64
import json
import re
import anthropic

# Inisialisasi client (ambil ANTHROPIC_API_KEY dari environment)
_client = None

def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


# ── Prompt templates per jenis dokumen ──────────────────────────

PROMPTS = {

    "ktp": """Kamu adalah sistem ekstraksi data KTP Indonesia.
Analisis gambar KTP ini dan ekstrak SEMUA field yang terlihat.
Kembalikan HANYA JSON valid, tanpa teks lain, dengan struktur persis:
{
  "nik": "16 digit NIK",
  "nama_lengkap": "nama sesuai KTP",
  "tempat_lahir": "kota tempat lahir",
  "tanggal_lahir": "DD-MM-YYYY",
  "jenis_kelamin": "LAKI-LAKI atau PEREMPUAN",
  "alamat_ktp": "alamat lengkap",
  "kelurahan": "nama kelurahan",
  "kecamatan": "nama kecamatan",
  "kota_kab": "kota atau kabupaten",
  "provinsi": "nama provinsi",
  "agama": "agama",
  "status_perkawinan": "BELUM KAWIN / KAWIN / CERAI HIDUP / CERAI MATI",
  "pekerjaan": "pekerjaan",
  "berlaku_hingga": "tanggal atau SEUMUR HIDUP"
}
Jika field tidak terbaca atau tidak ada, isi dengan string kosong "".
""",

    "sku": """Kamu adalah sistem ekstraksi Surat Keterangan Usaha (SKU) Indonesia.
Analisis gambar dokumen SKU/NIB ini dan ekstrak semua informasi usaha.
Kembalikan HANYA JSON valid, tanpa teks lain:
{
  "nomor_sku": "nomor surat",
  "nama_pemilik": "nama pemilik usaha",
  "nama_usaha": "nama usaha",
  "jenis_usaha": "jenis / bidang usaha",
  "alamat_usaha": "alamat lengkap usaha",
  "tanggal_terbit": "tanggal penerbitan DD/MM/YYYY",
  "penerbit": "kelurahan/kecamatan penerbit",
  "modal_usaha": "angka modal (tanpa Rp dan titik/koma)",
  "berdiri_sejak": "tanggal usaha berdiri"
}
Untuk modal_usaha: ekstrak HANYA angkanya, contoh: jika tertulis 'Rp 150.000.000' maka isi '150000000'.
Jika field tidak ada, isi "".
""",

    "rekening_koran": """Kamu adalah sistem ekstraksi Rekening Koran bank Indonesia.
Analisis gambar rekening koran ini dan ekstrak informasi keuangan kunci.
Kembalikan HANYA JSON valid, tanpa teks lain:
{
  "nama_nasabah": "nama pemilik rekening",
  "nomor_rekening": "nomor rekening",
  "nama_bank": "nama bank",
  "periode_awal": "tanggal awal periode (DD/MM/YYYY)",
  "periode_akhir": "tanggal akhir periode (DD/MM/YYYY)",
  "total_kredit": "total transaksi masuk dalam periode (angka saja tanpa titik/koma)",
  "total_debit": "total transaksi keluar dalam periode (angka saja)",
  "rata_saldo_harian": "rata-rata saldo harian (angka saja)",
  "saldo_akhir": "saldo terakhir yang tertera (angka saja)",
  "jumlah_transaksi": "jumlah baris transaksi yang terlihat"
}
Untuk semua nilai rupiah: ekstrak HANYA angkanya tanpa 'Rp', titik, atau koma.
Contoh: 'Rp 24.500.000' → '24500000'
Jika ada ringkasan/summary di bawah tabel, gunakan itu untuk total_kredit, total_debit, rata_saldo.
""",

    "laporan_keuangan": """Kamu adalah sistem ekstraksi Laporan Keuangan / Laporan Laba Rugi UMKM Indonesia.
Analisis gambar laporan keuangan ini dan ekstrak angka-angka keuangan.
Kembalikan HANYA JSON valid, tanpa teks lain:
{
  "nama_usaha": "nama usaha",
  "nama_pemilik": "nama pemilik jika ada",
  "periode": "periode laporan (misal: Agustus - Oktober 2024)",
  "total_pendapatan_bulanan": "rata-rata pendapatan per bulan (angka saja)",
  "hpp_bulanan": "rata-rata HPP / harga pokok per bulan (angka saja)",
  "laba_kotor_bulanan": "rata-rata laba kotor per bulan (angka saja)",
  "biaya_operasional_bulanan": "rata-rata biaya operasional per bulan (angka saja)",
  "rata_laba_bersih_bulanan": "rata-rata laba bersih per bulan (angka saja)",
  "bulan_data": "jumlah bulan data yang ada dalam laporan"
}
Catatan penting:
- Jika laporan menampilkan data per bulan, hitung rata-ratanya.
- Semua nilai rupiah: HANYA angkanya, tanpa 'Rp', titik, atau koma.
- Jika ada baris 'Rata-rata' langsung gunakan nilai tersebut.
"""
}

# ── Mapping doc_type → field kredit ML ──────────────────────────

def map_to_ml_fields(doc_type: str, extracted: dict) -> dict:
    """
    Konversi hasil ekstraksi dokumen ke field yang dibutuhkan
    model ML kredit UMKM.
    """
    ml = {}

    if doc_type == "ktp":
        ml["status_perkawinan_raw"] = extracted.get("status_perkawinan", "")
        ml["kota"] = extracted.get("kota_kab", "")
        ml["nama_lengkap"] = extracted.get("nama_lengkap", "")
        ml["nik"] = extracted.get("nik", "")

    elif doc_type == "sku":
        ml["nama_usaha"] = extracted.get("nama_usaha", "")
        modal_raw = extracted.get("modal_usaha", "0")
        try:
            ml["modal_usaha"] = int(re.sub(r'[^\d]', '', str(modal_raw)) or 0)
        except:
            ml["modal_usaha"] = 0

    elif doc_type == "rekening_koran":
        def parse_int(v):
            try: return int(re.sub(r'[^\d]', '', str(v)) or 0)
            except: return 0

        ml["total_kredit_3bln"]   = parse_int(extracted.get("total_kredit", 0))
        ml["total_debit_3bln"]    = parse_int(extracted.get("total_debit", 0))
        ml["rata_saldo_harian"]   = parse_int(extracted.get("rata_saldo_harian", 0))

    elif doc_type == "laporan_keuangan":
        def parse_int(v):
            try: return int(re.sub(r'[^\d]', '', str(v)) or 0)
            except: return 0

        ml["total_pendapatan_bulanan"]  = parse_int(extracted.get("total_pendapatan_bulanan", 0))
        ml["hpp_bulanan"]               = parse_int(extracted.get("hpp_bulanan", 0))
        ml["laba_kotor_bulanan"]        = parse_int(extracted.get("laba_kotor_bulanan", 0))
        ml["biaya_operasional_bulanan"] = parse_int(extracted.get("biaya_operasional_bulanan", 0))
        ml["rata_laba_bersih_bulanan"]  = parse_int(extracted.get("rata_laba_bersih_bulanan", 0))

    return ml


# ── Main extraction function ─────────────────────────────────────

def extract_document(image_bytes: bytes, doc_type: str,
                     media_type: str = "image/png") -> dict:
    """
    Ekstrak data dari gambar dokumen menggunakan Claude Vision.

    Args:
        image_bytes : bytes gambar (PNG/JPG/PDF page)
        doc_type    : 'ktp' | 'sku' | 'rekening_koran' | 'laporan_keuangan'
        media_type  : MIME type gambar

    Returns:
        {
          'success'  : bool,
          'doc_type' : str,
          'data'     : dict,   # field-field dokumen yang diekstrak
          'ml_fields': dict,   # field yang langsung bisa dipakai model ML
          'raw'      : str,    # respons mentah dari Claude
          'error'    : str     # jika gagal
        }
    """
    if doc_type not in PROMPTS:
        return {
            "success": False,
            "error": f"Jenis dokumen tidak dikenal: {doc_type}. "
                     f"Pilih dari: {list(PROMPTS.keys())}"
        }

    prompt = PROMPTS[doc_type]
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    try:
        response = get_client().messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": prompt}
                ],
            }]
        )

        raw = response.content[0].text.strip()

        # Clean potential markdown fences
        clean = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
        clean = re.sub(r'\s*```$', '', clean, flags=re.MULTILINE).strip()

        extracted = json.loads(clean)
        ml_fields = map_to_ml_fields(doc_type, extracted)

        return {
            "success"  : True,
            "doc_type" : doc_type,
            "data"     : extracted,
            "ml_fields": ml_fields,
            "raw"      : raw,
        }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "doc_type": doc_type,
            "error": f"Gagal parse JSON dari respons Claude: {e}",
            "raw": raw if 'raw' in locals() else ""
        }
    except Exception as e:
        return {
            "success": False,
            "doc_type": doc_type,
            "error": str(e),
        }