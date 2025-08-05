# Export Your Replit Project to Railway

## 📦 DOWNLOAD YOUR PROJECT FROM REPLIT

### Method 1: Download ZIP (Easiest)
1. In your Replit workspace, click the **3 dots menu** (⋮) in the file explorer
2. Click **"Download as ZIP"**
3. Save the ZIP file to your computer
4. Extract the ZIP file

### Method 2: Git Clone (If you have Git)
1. In Replit, go to **Tools > Shell**
2. Run: `git init && git add . && git commit -m "ready for railway"`
3. Push to GitHub or download via Git

## 🚂 UPLOAD TO RAILWAY

### Step 1: Go to Railway
- Visit: **https://railway.app**
- Sign in with your Google account (same as Replit)

### Step 2: Create New Project
- Click **"New Project"**
- Choose **"Deploy from local directory"** or **"Empty project"**

### Step 3: Upload Your Files
- Drag and drop your extracted project folder
- Or use **"Upload files"** and select all your project files

### Step 4: Railway Auto-Deploys
Railway will automatically:
- Detect your Python Flask app
- Read `railway.json` configuration
- Install from `pyproject.toml`
- Start with `python3 main.py`
- Create health checks

## ✅ IMPORTANT FILES TO INCLUDE:
- `app.py` (main Flask application)
- `main.py` (Railway entry point)
- `railway.json` (Railway configuration)
- `pyproject.toml` (dependencies)
- `templates/` folder (HTML files)
- `static/` folder (CSS files)
- `credentials.json` (Google Sheets access)
- All your automation Python files

## ⚡ AFTER DEPLOYMENT:
1. Railway gives you a live URL
2. Add environment variables in Railway dashboard:
   - **GOOGLE_SHEETS_CREDENTIALS**: Paste your service account JSON
   - **BOOKING_URL**: Your LeadConnector booking URL

Your booking automation will be live in 5-10 minutes!