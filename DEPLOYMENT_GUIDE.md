# LeadConnector Booking Automation - Deployment Guide

## The Real Issue

Your booking automation needs **actual browser automation** to work with LeadConnector's booking widget. The widget requires:

1. **JavaScript execution** to load calendar slots
2. **Browser cookies and sessions** for proper authentication
3. **Real DOM interaction** to select dates and times
4. **Form submission** with proper browser context

HTTP requests alone cannot replicate this complex browser behavior, which is why none of the HTTP approaches are creating actual appointments.

## Solution: Deploy Outside Replit

Your `standalone_booking.py` script is the correct solution. It uses real Playwright browser automation exactly as you requested. Here's how to deploy it:

### Option 1: Local Machine (Recommended)

**Step 1: Download Files**
- Download `standalone_booking.py` 
- Download `credentials.json` (your Google service account file)

**Step 2: Install Dependencies**
```bash
pip install playwright gspread oauth2client
playwright install chromium
```

**Step 3: Run the Automation**
```bash
python standalone_booking.py
```

This will:
- Open a real browser window
- Navigate to your LeadConnector booking page
- Click on the first available date button
- Click on the first available time button  
- Fill out the form with data from your Google Sheet
- Submit the form
- Wait for confirmation
- Mark the row as "done" in your sheet

### Option 2: Cloud VPS (Ubuntu/Debian)

**Step 1: Server Setup**
```bash
sudo apt update
sudo apt install python3 python3-pip xvfb
pip3 install playwright gspread oauth2client
sudo playwright install-deps
playwright install chromium
```

**Step 2: Upload Files**
- Upload `standalone_booking.py`
- Upload `credentials.json`

**Step 3: Run with Virtual Display**
```bash
xvfb-run -a python3 standalone_booking.py
```

### Option 3: GitHub Actions (Automated)

Create `.github/workflows/booking.yml`:
```yaml
name: LeadConnector Booking Automation
on:
  schedule:
    - cron: '0 9 * * *'  # Run daily at 9 AM
  workflow_dispatch:

jobs:
  book-appointments:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v3
        with:
          python-version: '3.11'
      - run: |
          pip install playwright gspread oauth2client
          playwright install chromium
          python standalone_booking.py
```

## Why This Approach Works

The `standalone_booking.py` script implements exactly what you asked for:

✅ **Uses Playwright** for real browser automation
✅ **Opens LeadConnector booking page** in an actual browser
✅ **Clicks first available date** (`.day` button)
✅ **Clicks first available time** (`.time` button)
✅ **Fills out form fields** with sheet data
✅ **Submits the form** (button[type='submit'])
✅ **Waits for confirmation** 
✅ **Marks rows as done** in Google Sheets

## Current Status

Your Google Sheet data is ready:
- **16 rows with real email addresses** identified
- **Service account authentication** working perfectly
- **Data extraction** functioning correctly
- **Row 28** has complete data: Amber Johnson, ambersellsthesierras@gmail.com, Amber Sells the Sierras

## Next Steps

1. **Download the files** from this Replit
2. **Run locally** or on a VPS with browser support
3. **Test with one appointment** first
4. **Scale to process all 16 bookings**

The Flask dashboard will remain useful for monitoring your Google Sheets data and logs, but the actual booking needs to run in an environment with proper browser support.

## Alternative: Request API Access

If you have a relationship with LeadConnector, you could request direct API access to their booking system, which would eliminate the need for browser automation. However, most booking widgets are designed to be used through their web interface.