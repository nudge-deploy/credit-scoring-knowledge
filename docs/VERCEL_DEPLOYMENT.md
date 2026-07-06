# Deploy ke Vercel

## Opsi Deployment

Aplikasi ini bisa di-deploy ke Vercel dengan beberapa pilihan:

### **Opsi 1: Full Stack di Vercel (Recommended)**
Flask API + Frontend di Vercel sebagai serverless functions

**Keuntungan:**
- ✅ Semua di satu platform (mudah manage)
- ✅ Auto-scaling
- ✅ HTTPS otomatis
- ✅ CDN global

**Requirements:**
- Vercel account (gratis)
- Anthropic API Key
- Model artifacts sudah tersedia

### **Opsi 2: Backend di Vercel + Frontend di Vercel Pages**
Terpisah tapi tetap Vercel

### **Opsi 3: Backend di Render/Railway + Frontend di Vercel**
Untuk traffic tinggi

---

## Langkah Deploy ke Vercel (Opsi 1)

### 1. **Siapkan Repository GitHub**

```bash
git init
git add .
git commit -m "Initial commit - Kredit UMKM ML System"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/umkm-kredit.git
git push -u origin main
```

### 2. **Login ke Vercel & Connect Repository**

- Buka https://vercel.com
- Klik "New Project"
- Pilih GitHub repository Anda
- Klik "Import"

### 3. **Setup Environment Variables**

Di Vercel Project Settings → Environment Variables, tambahkan:

```
ANTHROPIC_API_KEY = sk-ant-api03-xxxxx
```

![Vercel Environment Variables](https://docs.vercel.com/docs/projects/environment-variables/images/add-environment-variable.png)

### 4. **Deploy**

```bash
# Vercel akan auto-detect dan deploy
# Atau gunakan Vercel CLI:
npm i -g vercel
vercel
```

---

## Vercel Configuration Explained

File `vercel.json` yang sudah kami buat:

```json
{
  "version": 2,
  "env": {
    "ANTHROPIC_API_KEY": "@anthropic-api-key"  // Reference env variable
  },
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python",  // Use Vercel's Python runtime
      "config": {
        "maxLambdaSize": "15mb",
        "runtime": "python3.11"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",  // All routes → app.py
      "dest": "app.py"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "*" },
        { "key": "Access-Control-Allow-Methods", "value": "GET,POST,PUT,DELETE,OPTIONS" },
        { "key": "Access-Control-Allow-Headers", "value": "Content-Type" }
      ]
    }
  ]
}
```

**Note:** CORS headers sudah ada di Flask (`flask-cors`), tapi ini menambahan layer security di Vercel level.

---

## Troubleshooting

### ❌ "Module not found" error

**Cause:** Dependencies belum terinstall saat build

**Fix:**
```bash
# Pastikan requirements.txt ada
pip freeze > requirements.txt
```

Atau edit `requirements.txt` manual:

```
flask==3.1.3
flask-cors==6.0.2
pandas==3.0.3
numpy==2.4.6
scikit-learn==1.8.0
joblib==1.5.3
anthropic==0.104.1
python-dotenv==1.2.2
xgboost==3.2.0
lightgbm==4.6.0
pillow==12.2.0
gunicorn==26.0.0
```

### ❌ "ANTHROPIC_API_KEY not found"

**Cause:** Environment variable belum di-set

**Fix:**
1. Buka Vercel Project → Settings → Environment Variables
2. Tambah `ANTHROPIC_API_KEY`
3. Redeploy

### ❌ "Model loading timeout"

**Cause:** Model files terlalu besar (> 50MB) atau network lambat

**Fix:**
- Upload model artifacts ke AWS S3
- Load dari S3 di startup
- Atau gunakan model yang lebih kecil

---

## Monitoring & Analytics

Setelah deploy:

1. **Vercel Dashboard** → Project → Deployments
   - Lihat status build & logs
   - Monitor performance

2. **Analytics** → Tab Functions
   - CPU/Memory usage
   - Invocation count
   - Response time

3. **Logs** → Real-time logs
   ```bash
   vercel logs your-project.vercel.app
   ```

---

## Cost Estimation

Vercel Pricing (per month):

| Plan | Price | Requests | Functions |
|------|-------|----------|-----------|
| Free | $0 | 100,000/mo | 12 seconds timeout |
| Pro | $20 | Unlimited | 60 seconds timeout |
| Enterprise | Custom | Custom SLA | Custom |

**Estimasi untuk aplikasi ini:**
- ~50 predictions/hari = ~1,500/bulan
- Model loading: ~500MB disk
- **Total:** Estimated $0 - $20/bulan (bisa gratis jika traffic rendah)

---

## Domain Custom

Setelah deploy:

1. Beli domain di Namecheap/GoDaddy
2. Di Vercel: Settings → Domains → Add
3. Ikuti instruksi DNS
4. ~10-20 menit HTTPS auto-provision

---

## CI/CD Pipeline

Vercel auto-deploy setiap `git push` ke branch `main`.

Untuk preview deployment (sebelum merge):
- Push ke branch baru (e.g., `feature/new-model`)
- Vercel auto-create preview URL
- Test di staging
- Merge ke `main` → production deploy

---

## Local Testing Before Deploy

```bash
# Test app lokal
PORT=8000 python3 app.py

# Test dengan Vercel CLI
npm install -g vercel
vercel dev  # Simulate Vercel environment locally
```

---

## Backup & Disaster Recovery

Model files crucial! Backup:

```bash
# Create backup
tar -czf model_artifacts_backup.tar.gz model_artifacts/

# Upload ke GitHub (besar files) atau S3
git lfs track "*.pkl"  # Git LFS untuk large files
```

---

## Next Steps

1. ✅ Prepare GitHub repo
2. ✅ Get Anthropic API key  
3. ✅ Connect Vercel
4. ✅ Deploy
5. ✅ Test API endpoints
6. ✅ Monitor & optimize

**Questions?** Check Vercel docs: https://vercel.com/docs
