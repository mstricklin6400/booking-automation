# Email Notifications Setup Guide

Your booking automation now includes comprehensive email notifications! Here's how to set them up:

## What You Get

### 📧 Email Types

1. **✅ Success Notifications**
   - Sent when a booking is successfully submitted to LeadConnector
   - Includes booking details: name, email, company, and timestamp
   - Professional HTML email template with booking confirmation

2. **❌ Failure Notifications**
   - Sent when a booking attempt fails
   - Includes error details and troubleshooting suggestions
   - Helps you quickly identify and resolve issues

3. **📊 Summary Reports**
   - Sent after each automation run completes
   - Shows total successful/failed bookings
   - Lists all processed bookings with details
   - Includes run duration and statistics

## Setup Instructions

### For Gmail (Recommended)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Create an App Password**:
   - Go to Google Account settings → Security
   - Under "2-Step Verification", click "App passwords"
   - Generate a password for "Mail" application
   - Copy the 16-character password

3. **Configure in the Web Interface**:
   - Go to the "Email Notifications" tab
   - Enter your Gmail address
   - Paste the 16-character App Password
   - Add recipient email addresses (comma-separated)
   - Click "Save Configuration"
   - Click "Send Test Email" to verify

### For Other Email Providers

The system supports any SMTP server:

- **Outlook/Hotmail**: `smtp-mail.outlook.com:587`
- **Yahoo**: `smtp.mail.yahoo.com:587`
- **Custom SMTP**: Enter your server details

## Configuration Options

### Environment Variables (Alternative Setup)

You can also configure email via environment variables:

```bash
export EMAIL_USER="your-email@gmail.com"
export EMAIL_PASSWORD="your-app-password"
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export NOTIFICATION_RECIPIENTS="recipient1@example.com,recipient2@example.com"
```

### Web Interface

The Flask dashboard includes a complete email configuration interface:

- Real-time configuration status
- Test email functionality
- Professional email templates preview
- Easy recipient management

## Email Templates

### Success Email Features:
- ✅ Professional design with success styling
- 📋 Complete booking details
- 🕒 Timestamp information
- 📧 Clear confirmation message

### Failure Email Features:
- ❌ Alert styling for immediate attention
- 🔍 Detailed error information
- 💡 Troubleshooting suggestions
- 📞 Action items for manual resolution

### Summary Report Features:
- 📊 Visual statistics (successful vs failed)
- 📝 Complete booking lists
- ⏱️ Run duration and performance metrics
- 📈 Process insights

## Testing

1. **Configuration Test**: Use "Send Test Email" button
2. **Integration Test**: Run a single booking and verify notifications
3. **Full Test**: Run complete automation and check summary email

## Troubleshooting

### Common Issues:

1. **"Authentication failed"**
   - Verify App Password is correct (not regular password)
   - Ensure 2FA is enabled on Gmail

2. **"Email not configured"**
   - Check all required fields are filled
   - Verify recipient email format

3. **"Test email failed"**
   - Check SMTP server and port settings
   - Verify network connectivity
   - Try different email provider

### Debug Steps:

1. Check automation logs for email errors
2. Verify SMTP settings match your provider
3. Test with a simple recipient list first
4. Contact support if issues persist

## Security Notes

- App Passwords are safer than regular passwords
- Passwords are not stored in logs or displayed in UI
- Use environment variables for production deployments
- Recipients list can include multiple stakeholders

## Integration with Automation

Email notifications are automatically integrated with your booking automation:

- **No additional code changes needed**
- **Runs alongside existing automation**
- **Graceful fallback if email fails**
- **Does not stop automation if email issues occur**

Your automation will now provide complete visibility into the booking process with professional email notifications!