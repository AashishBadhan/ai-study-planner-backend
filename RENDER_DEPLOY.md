# Render Deployment Guide

## Quick Deploy Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Render deployment ready"
git push
```

### 2. Render Dashboard Setup
1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select the backend folder

### 3. Configuration

**Build Command:**
```bash
pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
```

**Start Command:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Environment Variables:**
Add these in Render dashboard:

```
DATABASE_URL=mongodb+srv://your-atlas-url
DATABASE_NAME=ai_study_planner
SECRET_KEY=your-super-secret-key-here
DEBUG=False
CORS_ORIGINS=["https://your-frontend.onrender.com","http://localhost:3000"]
MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
DEVICE=cpu
```

### 4. MongoDB Atlas Setup (Free)
1. Go to https://cloud.mongodb.com
2. Create free cluster
3. Get connection string
4. Add to DATABASE_URL

### 5. Important Notes

- ✅ OCR features (Tesseract) are **disabled** for Render (not available)
- ✅ Only text-based PDFs will work
- ✅ PyTorch CPU version will be installed
- ✅ First deployment takes 10-15 minutes (model download)
- ✅ Free tier has 512MB RAM limit

### 6. Testing Deployment

After deployment, test:
```bash
curl https://your-app.onrender.com/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "ml_model_loaded": true
}
```

### Troubleshooting

**Build fails:**
- Check Python version (3.11.7 in runtime.txt)
- Verify all dependencies in requirements.txt

**Memory issues:**
- Upgrade to paid plan ($7/month for more RAM)
- Or use lighter ML model

**Database connection:**
- Check MongoDB Atlas IP whitelist (allow all: 0.0.0.0/0)
- Verify connection string

### Files Created for Deployment:
- ✅ requirements.txt (updated with CPU PyTorch)
- ✅ Procfile
- ✅ runtime.txt (Python 3.11.7)
- ✅ render.yaml (optional config)
