# Railway Deployment - Step by Step

## 🚀 DEPLOY YOUR BOOKING AUTOMATION ON RAILWAY

### Step 1: Go to Railway
- Visit: **railway.app**
- Click **"Start a New Project"** or **"Deploy Now"**
- Sign up with GitHub (recommended) or email

### Step 2: Choose Deployment Method

**Option A: GitHub (Recommended)**
1. Push your project to GitHub first
2. Connect Railway to your GitHub repo
3. Auto-deploys on every code change

**Option B: Direct Upload**
1. Click **"Deploy from local directory"**
2. Upload your entire project folder
3. Manual deployments

### Step 3: Railway Auto-Configuration
Railway will automatically:
- ✅ Detect Python project
- ✅ Read `railway.json` configuration
- ✅ Install dependencies from `pyproject.toml`
- ✅ Use `python3 main.py` as start command
- ✅ Set up health checks at `/health`
- ✅ Assign a `.railway.app` domain

### Step 4: Environment Variables (Important!)
After deployment, add these secrets:
- **GOOGLE_SHEETS_CREDENTIALS**: Your service account JSON
- **BOOKING_URL**: Your LeadConnector booking URL
- Any other API keys you need

### Step 5: Your App Will Be Live!
- Railway gives you a live URL like: `https://your-app-name.railway.app`
- Dashboard accessible immediately
- Ready for real booking automation

## 📁 Files Ready for Railway:
✅ `main.py` - Entry point  
✅ `railway.json` - Railway configuration  
✅ `pyproject.toml` - Dependencies  
✅ `Procfile` - Backup server config  
✅ All your Flask app files  
✅ Health endpoint at `/health`  

## ⚡ Expected Timeline:
- Upload: 2 minutes
- Build & Deploy: 3-5 minutes
- **Total: Under 10 minutes to live app**

Railway is extremely reliable and handles Python apps perfectly. Your booking automation will be production-ready immediately!