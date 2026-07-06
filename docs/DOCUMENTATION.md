# 📚 Documentation Guide

## Where to Start

Choose your path based on what you need:

---

## 🚀 **I want to deploy to Vercel NOW**

**Start here:** [`QUICK_START.md`](./QUICK_START.md) (5 min read)

Then follow: [`VERCEL_DEPLOYMENT.md`](./VERCEL_DEPLOYMENT.md) (10 min read)

**What you'll do:**
1. Push code to GitHub
2. Connect Vercel
3. Set API key
4. Deploy & test

---

## 🏠 **I want to run locally first**

**Start here:** [`SETUP_DEPLOYMENT.md`](./SETUP_DEPLOYMENT.md) → Quick Start section

**What you'll need:**
- Python 3.8+
- Git
- Anthropic API key

**Time:** 15 minutes

---

## 📖 **I want to understand everything**

**Read in order:**
1. [`README.md`](./README.md) — Project overview
2. [`SETUP_DEPLOYMENT.md`](./SETUP_DEPLOYMENT.md) — Full setup guide
3. [`VERCEL_DEPLOYMENT.md`](./VERCEL_DEPLOYMENT.md) — Deployment guide
4. [`QUICK_START.md`](./QUICK_START.md) — Checklist & next steps
5. [`SETUP_SUMMARY.md`](./SETUP_SUMMARY.md) — What was built

**Time:** 30-45 minutes

---

## 🔍 **I want to troubleshoot**

**Go to:** 
- `SETUP_DEPLOYMENT.md` → Troubleshooting section
- `VERCEL_DEPLOYMENT.md` → Troubleshooting section
- Run: `python diagnose.py`

---

## 📋 **Documentation Files**

### Core Documentation

| File | Purpose | Read Time | Best For |
|------|---------|-----------|----------|
| **README.md** | Project overview, features, architecture | 10 min | Understanding the system |
| **QUICK_START.md** | Checklist & next steps | 5 min | Getting started quickly |
| **SETUP_DEPLOYMENT.md** | Complete setup guide | 20 min | Local development & deployment |
| **VERCEL_DEPLOYMENT.md** | Vercel-specific guide | 15 min | Deploying to Vercel |
| **SETUP_SUMMARY.md** | What was built summary | 10 min | Understanding recent changes |

### Configuration Files

| File | Purpose |
|------|---------|
| **VERSION** | Current app version (1.0.0) |
| **vercel.json** | Vercel deployment configuration |
| **.vercelignore** | Build optimization settings |
| **requirements.txt** | Python dependencies |
| **.env** | Environment variables (API key) |
| **.gitignore** | Files to ignore in git |

### Source Code

| File | Purpose |
|------|---------|
| **app.py** | Flask API server (main backend) |
| **extractor.py** | Document extraction engine |
| **index.html** | Web UI (frontend) |
| **diagnose.py** | System diagnostics script |

### Data & Models

| File | Purpose |
|------|---------|
| **model_artifacts/** | ML models & metadata |
| **umkm_kredit_ml.ipynb** | Training notebook |
| **umkm_kredit_training_data.csv** | Training dataset |
| **sample_docs/** | Example documents |

---

## 🎯 Quick Reference

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run app
python app.py

# Open browser
http://localhost:5000

# Test API
curl http://localhost:5000/version
```

### Deploy to Vercel

```bash
# Push to GitHub
git push origin main

# Go to https://vercel.com/new
# Import GitHub repo
# Set ANTHROPIC_API_KEY environment variable
# Click Deploy!
```

### Update Version

```bash
# Edit VERSION file
echo "1.0.1" > VERSION

# Commit & push
git add VERSION
git commit -m "Release v1.0.1"
git push origin main
```

---

## 📞 Getting Help

### For Local Setup Issues
→ See `SETUP_DEPLOYMENT.md` → Troubleshooting

### For Vercel Deployment Issues
→ See `VERCEL_DEPLOYMENT.md` → Troubleshooting

### For System Issues
→ Run `python diagnose.py`

### For General Questions
→ Check `README.md` FAQ section (if available)

---

## 🔗 External Resources

| Topic | Link |
|-------|------|
| Flask Documentation | https://flask.palletsprojects.com |
| Anthropic API Docs | https://docs.anthropic.com |
| Vercel Documentation | https://vercel.com/docs |
| Python Documentation | https://docs.python.org |
| Git/GitHub Help | https://docs.github.com |

---

## ✅ Checklist

Before deploying:

- [ ] Read QUICK_START.md
- [ ] API key obtained from console.anthropic.com
- [ ] Local app tested (http://localhost:5000)
- [ ] All files committed to Git
- [ ] Pushed to GitHub
- [ ] ANTHROPIC_API_KEY configured in Vercel
- [ ] Deployment successful
- [ ] Test production /version endpoint

---

## 📊 Document Statistics

```
Total Documentation:  ~40 KB
README:              ~15 KB
Setup Guide:         ~8.3 KB
Vercel Guide:        ~5.1 KB
Quick Start:         ~6.2 KB
Setup Summary:       ~6 KB
This Guide:          ~2 KB
```

---

## 🎓 Learning Path

### Beginner (Just want it working)
1. QUICK_START.md
2. SETUP_DEPLOYMENT.md (Quick Start section only)
3. Deploy to Vercel

### Intermediate (Want to understand)
1. README.md
2. SETUP_DEPLOYMENT.md (Full read)
3. VERCEL_DEPLOYMENT.md
4. Try local modifications

### Advanced (Want to customize)
1. All documentation
2. Read source code (app.py, extractor.py)
3. Modify preprocessing or ML model
4. Retrain or update

---

## 💾 File Structure

```
project/
├── 📚 DOCUMENTATION
│   ├── README.md                    ← Start here
│   ├── QUICK_START.md              ← Then here
│   ├── SETUP_DEPLOYMENT.md         ← For local/production
│   ├── VERCEL_DEPLOYMENT.md        ← For Vercel specific
│   ├── SETUP_SUMMARY.md            ← What was built
│   └── DOCUMENTATION.md            ← This file
│
├── ⚙️ CONFIGURATION
│   ├── VERSION                      (1.0.0)
│   ├── vercel.json
│   ├── .vercelignore
│   ├── requirements.txt
│   ├── .env                         (API key)
│   └── .gitignore
│
├── 💻 SOURCE CODE
│   ├── app.py                      (Main server)
│   ├── extractor.py                (Document extraction)
│   ├── index.html                  (Web UI)
│   └── diagnose.py                 (Diagnostics)
│
├── 📦 MODELS & DATA
│   ├── model_artifacts/            (ML models)
│   ├── umkm_kredit_ml.ipynb        (Training notebook)
│   ├── umkm_kredit_training_data.csv
│   └── sample_docs/                (Example files)
│
└── 📄 OTHER
    ├── LICENSE
    └── render.yaml                 (For Render deployment)
```

---

## 🎯 Common Tasks

### Want to change the version?
→ Edit `VERSION` file, git push

### Want to add a new feature?
→ Modify `app.py`, test locally, deploy

### Want to retrain the model?
→ Use `umkm_kredit_ml.ipynb` notebook

### Want to customize the UI?
→ Edit `index.html` (CSS + JavaScript)

### Want to improve document extraction?
→ Update prompts in `extractor.py`

---

## 🚨 Important Notes

- **Never commit `.env` file** (has API key)
- **Model files are large** (keep in .gitignore if > 50MB)
- **API key is sensitive** (rotate every 90 days)
- **Test locally before deploying** (use diagnose.py)

---

**Last Updated:** May 24, 2026  
**App Version:** 1.0.0  
**Status:** Documentation Complete ✅

---

### Quick Links

🏠 [Home](./README.md) | 🚀 [Quick Start](./QUICK_START.md) | 📖 [Setup Guide](./SETUP_DEPLOYMENT.md) | 🎯 [Vercel Deploy](./VERCEL_DEPLOYMENT.md)
