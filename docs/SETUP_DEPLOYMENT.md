# Setup & Deployment Guide

## Quick Start (Local)

### Prerequisites
- Python 3.8+
- Git
- Terminal/Command Line

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/umkm-kredit.git
cd umkm-kredit
```

### 2. Create Environment Variables

Create `.env` file at root:

```bash
echo "ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE" > .env
```

Get Anthropic API key from: https://console.anthropic.com/settings/keys

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Or with virtual environment (recommended):

```bash
# Create venv
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Install
pip install -r requirements.txt
```

### 4. Run Application

```bash
python app.py
```

Or specify port:

```bash
PORT=8080 python app.py
```

Application will be available at: **http://localhost:5000** (or your port)

### 5. Test API

```bash
# Health check
curl http://localhost:5000/health

# Version info
curl http://localhost:5000/version
```

---

## Application Structure

```
umkm-kredit/
├── app.py                    ← Flask API server (main entry point)
├── extractor.py              ← Document extraction with Claude Vision
├── index.html                ← Web UI (served from Flask)
├── requirements.txt          ← Python dependencies
├── VERSION                   ← App version (1.0.0)
│
├── model_artifacts/          ← Pre-trained ML models
│   ├── model_kredit_umkm.pkl       (1MB)
│   ├── scaler_kredit_umkm.pkl      (2KB)
│   └── model_metadata.json         (1KB)
│
├── vercel.json               ← Vercel deployment config
├── .vercelignore             ← Files to ignore in Vercel build
│
├── VERCEL_DEPLOYMENT.md      ← Detailed Vercel setup
├── SETUP_DEPLOYMENT.md       ← This file
└── README.md                 ← Project overview
```

---

## API Endpoints

### GET `/` 
Serves the main web application (index.html)

### GET `/health`
Health check endpoint
```json
{
  "status": "ok",
  "model": "Random Forest",
  "f1_macro": 0.9529,
  "n_features": 31
}
```

### GET `/version`
App & environment info
```json
{
  "app_version": "1.0.0",
  "model_name": "Random Forest",
  "environment": "development",
  "api_ready": true
}
```

### POST `/predict`
Predict from JSON data
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "plafon_diajukan": 50000000,
    "tenor_bulan": 12,
    "kolektibilitas_slik": 1,
    "status_blacklist": 0,
    ...
  }'
```

### POST `/extract`
Extract data from document image
```bash
curl -X POST http://localhost:5000/extract \
  -F "file=@ktp.jpg" \
  -F "doc_type=ktp"
```

### POST `/extract-and-predict`
Upload documents & get prediction in one call
```bash
curl -X POST http://localhost:5000/extract-and-predict \
  -F "ktp=@ktp.jpg" \
  -F "sku=@sku.jpg" \
  -F "rekening_koran=@rekening.jpg" \
  -F "laporan_keuangan=@laporan.jpg"
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | ✅ Yes | Claude Vision API key from console.anthropic.com |
| `PORT` | ❌ Optional | Server port (default: 5000) |
| `FLASK_ENV` | ❌ Optional | `development` or `production` |

---

## Troubleshooting

### ❌ "Module not found" Error

**Solution:**
```bash
pip install -r requirements.txt
# or individual package
pip install flask flask-cors
```

### ❌ "Port already in use"

**Solution:**
```bash
# Use different port
PORT=8080 python app.py

# Or kill process on port 5000 (macOS/Linux)
lsof -ti:5000 | xargs kill -9
```

### ❌ "ANTHROPIC_API_KEY not found"

**Solution:**
1. Check `.env` file exists in root folder
2. Format: `ANTHROPIC_API_KEY=sk-ant-...` (no quotes)
3. Make sure `.env` is in `.gitignore` (don't commit!)
4. Reload app

### ❌ "Model loading timeout"

**Solution:**
- Model files are ~1MB - should load instantly
- If timeout occurs, check disk space
- Verify model files exist: `ls model_artifacts/`

### ❌ "Extract API returns 401 error"

**Solution:**
- API key is invalid
- Go to console.anthropic.com/settings/keys
- Create new key if needed
- Update `.env` file
- Restart app

---

## Development Tips

### Auto-reload on Code Changes

Flask debug mode automatically reloads:

```bash
FLASK_ENV=development python app.py
```

### Run Tests/Diagnostics

```bash
python diagnose.py
```

This checks:
- Python version
- All dependencies installed
- Model artifacts present
- API key validity
- Network connectivity

### Add New Features

1. **New API endpoint:** Add route in `app.py`
2. **UI changes:** Edit `index.html` (CSS + JS)
3. **ML preprocessing:** Modify `preprocess()` function
4. **Document extraction:** Update prompts in `extractor.py`

### Local ML Testing

```python
from app import run_predict

result = run_predict({
    "plafon_diajukan": 50000000,
    "tenor_bulan": 12,
    "kolektibilitas_slik": 1,
    ...
})
print(result)
```

---

## Production Deployment

### Option 1: Deploy to Vercel (Recommended)

See [VERCEL_DEPLOYMENT.md](./VERCEL_DEPLOYMENT.md)

### Option 2: Deploy to Render

1. Push code to GitHub
2. Go to https://render.com/dashboard
3. New → Web Service
4. Connect GitHub repo
5. Deploy using `render.yaml` config

### Option 3: Deploy to Railway

1. Install Railway CLI: `npm install -g railway`
2. Connect GitHub repo
3. Deploy: `railway up`

### Option 4: Docker (Any Cloud)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

```bash
# Build & run
docker build -t umkm-kredit .
docker run -p 5000:5000 -e ANTHROPIC_API_KEY=... umkm-kredit
```

---

## Git & Version Control

### Initial Setup

```bash
git init
git add .
git commit -m "Initial commit - UMKM Credit Scoring System"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/umkm-kredit.git
git push -u origin main
```

### Update Version

```bash
# Edit VERSION file
echo "1.0.1" > VERSION

git add VERSION
git commit -m "Release v1.0.1"
git tag v1.0.1
git push origin main --tags
```

### .gitignore Checklist

Ensure these are ignored:
```
.env              ← API keys
model_artifacts/  ← Large files (optional)
__pycache__/
*.pyc
.venv/
venv/
sample_docs/      ← Dummy data (optional)
```

---

## Performance Monitoring

### Local

```bash
# Check app memory/CPU
top -p $(pgrep -f "python app.py")
```

### Production (Vercel)

- Dashboard → Deployments → Function Logs
- Monitor invocation count, duration, memory

### Optimize API Response

1. **Cache model predictions:** Implement Redis
2. **Batch predictions:** Multiple requests in one
3. **Compress response:** Enable gzip
4. **Rate limiting:** Add per-IP limits

---

## Security Best Practices

1. ✅ **Never commit `.env`** — ensure it's in `.gitignore`
2. ✅ **Rotate API keys** — Regenerate ANTHROPIC_API_KEY every 90 days
3. ✅ **Use HTTPS only** — Production must use SSL
4. ✅ **Rate limit API** — Prevent abuse
5. ✅ **Validate input** — Sanitize user uploads
6. ✅ **CORS headers** — Already configured in Flask
7. ✅ **Error handling** — Don't expose stack traces in production

---

## Next Steps

1. **Local Testing**
   ```bash
   python app.py
   # Open http://localhost:5000
   # Upload sample documents
   ```

2. **Prepare for Production**
   - [ ] Update VERSION file
   - [ ] Test all endpoints with curl
   - [ ] Prepare GitHub repo
   - [ ] Get Anthropic API key (production)

3. **Deploy**
   - [ ] Choose platform (Vercel recommended)
   - [ ] Setup environment variables
   - [ ] Deploy & test
   - [ ] Monitor logs

4. **Monitor & Maintain**
   - [ ] Check API logs daily
   - [ ] Monitor prediction accuracy
   - [ ] Update model if needed
   - [ ] Regular backups

---

## Support & Resources

- **Anthropic API:** https://docs.anthropic.com
- **Flask Documentation:** https://flask.palletsprojects.com
- **Vercel Docs:** https://vercel.com/docs
- **Python Docs:** https://docs.python.org/3

---

**App Version:** 1.0.0  
**Last Updated:** May 24, 2026  
**Maintainer:** Your Team
