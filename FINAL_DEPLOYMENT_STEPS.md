# Final Deployment Steps - Ready to Deploy

## STEP 1: Download Project from Replit
1. In Replit file explorer, click **3 dots menu** (⋮)
2. Click **"Download as ZIP"**
3. Extract folder on your computer
4. **IMPORTANT**: Delete `credentials.json` from extracted folder (keep sensitive data separate)

## STEP 2: Upload to GitHub
1. Go to **github.com** and sign in with Google
2. Click **"New repository"**
3. Name: `booking-automation`
4. Click **"Create repository"**
5. Click **"uploading an existing file"**
6. Drag ALL files from extracted folder (except credentials.json)
7. Click **"Commit changes"**

## STEP 3: Deploy on Render
1. Go to **render.com** and sign in with Google
2. Click **"New +"** → **"Web Service"**
3. Click **"Build and deploy from a Git repository"**
4. Connect GitHub and select your `booking-automation` repository
5. Settings will auto-fill:
   - Build Command: `pip install flask gunicorn playwright gspread oauth2client requests beautifulsoup4`
   - Start Command: `python3 main.py`
6. Click **"Create Web Service"**

## STEP 4: Add Secure Environment Variables
After deployment, in Render dashboard:
1. Click **"Environment"** tab
2. Add these variables:
   - **GOOGLE_SHEETS_CREDENTIALS**: Paste content from your credentials.json file
   - **BOOKING_URL**: Your LeadConnector booking URL
   - **PORT**: 5000

## STEP 5: Access Your Live App
Render will provide URL like: `https://booking-automation.onrender.com`

Your professional booking automation dashboard will be live and ready to create real appointments!