# How to Use the Booking Automation App

## Step 1: Prepare Your Google Sheet

Create a Google Sheet with these columns:
- **Column A**: Name (e.g., "John Doe")
- **Column B**: Email (e.g., "john@example.com") 
- **Column C**: Company (e.g., "Acme Corp")
- **Column D**: Status (leave empty initially)

Make sure your sheet is either:
- **Public**: Anyone with the link can view
- **Private**: You have Google Service Account credentials set up

## Step 2: Configure the Application

1. Open the web dashboard (already running at http://localhost:5000)
2. Click on the **Configuration** tab
3. Enter your Google Sheet URL
4. Adjust settings as needed:
   - **Headless Mode**: Keep checked for background automation
   - **Delay Between Bookings**: Recommended 5-10 seconds to avoid rate limits

## Step 3: Preview Your Data

1. Click on **Data Preview** tab
2. Click **Load Data** to see your Google Sheet data
3. Verify that names, emails, and companies are showing correctly
4. Check that rows marked "done" are identified

## Step 4: Start the Automation

1. Go back to **Dashboard** tab
2. Click **Start Automation**
3. Watch the real-time status updates
4. Monitor progress through the **Logs** tab

## Step 5: Monitor Results

- The automation will process each row that doesn't have "done" in the Status column
- Successful bookings will be marked as "done" in your Google Sheet
- Failed attempts will be logged with error details
- You can see a summary of successes/failures in the logs

## What Happens During Automation

For each customer row:
1. Opens LeadConnector booking page: https://api.leadconnectorhq.com/widget/booking/vggoBfO4Zr1RTp4M4h8m
2. Clicks the first available day
3. Clicks the first available time slot
4. Fills in the customer's name, email, and company
5. Submits the booking form
6. Updates the Google Sheet with "done" status

## Troubleshooting Tips

- **"No data found"**: Check your Google Sheet URL and make sure it's accessible
- **Booking fails**: The LeadConnector site structure may have changed, check logs for details
- **Google Sheets access denied**: For private sheets, you'll need to set up service account credentials

Your automation app is ready to use! Just prepare your Google Sheet and start the process.