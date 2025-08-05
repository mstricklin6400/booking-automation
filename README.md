# Booking Automation Application

A Python web application that automates appointment bookings by reading customer data from Google Sheets and submitting booking requests through a web interface using Playwright browser automation.

## Features

- **Web Dashboard**: Clean, responsive Flask interface with Bootstrap styling
- **Google Sheets Integration**: Reads customer data from public or private Google Sheets
- **Browser Automation**: Uses Playwright to automate booking forms on LeadConnector
- **Real-time Monitoring**: Live status updates and progress tracking
- **Error Handling**: Comprehensive logging with retry mechanisms
- **Configuration Management**: Easy setup through web interface or environment variables

## Quick Start

1. **Set up Google Sheet URL**: 
   - Go to the Configuration tab in the web interface
   - Enter your Google Sheets URL
   - Your sheet should have columns: Name (A), Email (B), Company (C), Status (D)

2. **Start the automation**:
   - Click "Start Automation" on the Dashboard
   - Monitor progress in real-time
   - Check logs for detailed information

## Google Sheets Format

Your Google Sheet should have these columns:
- **Column A**: Customer Name
- **Column B**: Email Address  
- **Column C**: Company Name
- **Column D**: Status (leave empty initially, will be marked "done" after booking)

Example:
```
Name          Email              Company        Status
John Doe      john@example.com   Acme Corp      
Jane Smith    jane@test.com      Test Inc       done
```

## Configuration Options

### Through Web Interface
- Navigate to the Configuration tab
- Adjust settings like delays between bookings
- Enable/disable headless browser mode

### Through Environment Variables
```bash
GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/your-sheet-id
HEADLESS_MODE=true
DELAY_BETWEEN_BOOKINGS=5
LOG_LEVEL=INFO
```

## Authentication

### For Public Google Sheets
No authentication required - the app will access public sheets directly.

### For Private Google Sheets
You'll need to set up Google Service Account credentials:

1. Create a Google Cloud Project
2. Enable Google Sheets API
3. Create a Service Account
4. Download the JSON credentials
5. Set the `GOOGLE_SHEETS_CREDENTIALS` environment variable with the JSON content

## How It Works

1. **Data Reading**: Connects to Google Sheets and reads customer information
2. **Row Processing**: Loops through each row, skipping any marked as "done"
3. **Browser Automation**: 
   - Opens LeadConnector booking page
   - Selects first available day and time
   - Fills in customer information
   - Submits the booking form
4. **Status Updates**: Marks successful bookings as "done" in the Google Sheet
5. **Error Handling**: Logs failures and continues with remaining rows

## API Endpoints

- `GET /` - Main dashboard interface
- `GET /api/status` - Get automation status
- `POST /api/start` - Start automation process
- `GET /api/preview` - Preview Google Sheets data
- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration

## File Structure

```
├── app.py              # Flask web application
├── automation.py       # Main automation logic
├── sheets_client.py    # Google Sheets integration
├── config.py          # Configuration management
├── logger_config.py   # Logging setup
├── main.py            # CLI entry point
├── templates/         # HTML templates
├── static/           # CSS and JS files
└── README.md         # This file
```

## Troubleshooting

### Common Issues

1. **"No data found in Google Sheets"**
   - Check if the sheet URL is correct
   - Ensure the sheet is publicly accessible or credentials are set
   - Verify the sheet has data in the expected columns

2. **Browser automation fails**
   - The booking site structure may have changed
   - Check logs for specific error messages
   - Try running in non-headless mode for debugging

3. **Google Sheets access denied**
   - For private sheets, ensure service account credentials are configured
   - Check that the service account has access to the sheet

### Logs

Monitor the application logs through:
- Web interface Logs tab
- Console output when running
- Log files: `automation.log` and `errors.log`

## Security Notes

- Keep Google Service Account credentials secure
- Use environment variables for sensitive configuration
- The application runs on localhost by default
- Browser automation runs in headless mode by default

## Support

For issues or questions:
1. Check the logs for error details
2. Review the configuration settings
3. Ensure your Google Sheet format matches the expected structure
4. Verify the LeadConnector booking URL is accessible