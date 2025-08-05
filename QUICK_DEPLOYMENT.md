# 🚀 Quick Deployment Guide

## Download & Setup (5 Minutes)

### Step 1: Download Files
1. Click "Download as ZIP" in Replit or clone this repository
2. Extract to a folder on your computer

### Step 2: Install Dependencies
```bash
# Install Python packages
pip install flask playwright gspread oauth2client

# Install Playwright browsers
playwright install
```

### Step 3: Run the Application
```bash
python app.py
```

### Step 4: Access Dashboard
Open browser to: `http://localhost:5000`

## What Happens Next

1. **Real Browser Opens**: You'll see Chrome/Firefox launch automatically
2. **Navigate to Calendar**: Goes to your LeadConnector booking widget
3. **Click Available Dates/Times**: Selects first available slots
4. **Fill Customer Forms**: Uses data from Google Sheets
5. **Submit Bookings**: Creates actual appointments
6. **Update Google Sheets**: Marks customers as "done"
7. **Send Email Notifications**: Confirms successful bookings

## Your System Includes

- Professional web dashboard with real-time progress
- Multi-browser support (Chrome, Firefox, Safari)
- Email notification system
- Google Sheets integration
- Advanced error handling and retries
- CAPTCHA detection and skipping
- Concurrent processing options

Ready to create real bookings in your LeadConnector calendar!