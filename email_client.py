"""
Email notification system for booking automation.
Sends notifications for successful bookings and failures.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, List, Optional
from logger_config import setup_logger

class EmailNotificationClient:
    """Handles email notifications for booking automation."""
    
    def __init__(self, config):
        self.config = config
        self.logger = setup_logger('email_notifications')
        
        # Email configuration
        self.smtp_server = getattr(config, 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(config, 'SMTP_PORT', 587)
        self.email_user = getattr(config, 'EMAIL_USER', None)
        self.email_password = getattr(config, 'EMAIL_PASSWORD', None)
        self.notification_recipients = getattr(config, 'NOTIFICATION_RECIPIENTS', [])
        
        # Email templates
        self.success_template = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background-color: #28a745; color: white; padding: 20px; text-align: center; border-radius: 5px; margin-bottom: 20px; }
        .content { line-height: 1.6; color: #333; }
        .booking-details { background-color: #f8f9fa; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }
        .success-icon { font-size: 48px; color: #28a745; text-align: center; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="success-icon">✅</div>
            <h1>Booking Confirmation</h1>
        </div>
        
        <div class="content">
            <p>Great news! A booking has been successfully submitted to LeadConnector.</p>
            
            <div class="booking-details">
                <h3>Booking Details:</h3>
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Company:</strong> {company}</p>
                <p><strong>Booking Time:</strong> {booking_time}</p>
                <p><strong>Sheet Row:</strong> {row_number}</p>
            </div>
            
            <p>The appointment has been submitted to LeadConnector and the row has been marked as "done" in your Google Sheet.</p>
            
            <p>You should receive a separate confirmation email from LeadConnector with the appointment details.</p>
        </div>
        
        <div class="footer">
            <p>This notification was sent by your LeadConnector Booking Automation system.</p>
            <p>Timestamp: {timestamp}</p>
        </div>
    </div>
</body>
</html>
        """
        
        self.failure_template = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background-color: #dc3545; color: white; padding: 20px; text-align: center; border-radius: 5px; margin-bottom: 20px; }
        .content { line-height: 1.6; color: #333; }
        .error-details { background-color: #f8d7da; padding: 15px; border-left: 4px solid #dc3545; margin: 20px 0; border-radius: 3px; }
        .booking-details { background-color: #f8f9fa; padding: 15px; border-left: 4px solid #6c757d; margin: 20px 0; border-radius: 3px; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }
        .error-icon { font-size: 48px; color: #dc3545; text-align: center; margin-bottom: 15px; }
        .action-needed { background-color: #fff3cd; padding: 15px; border: 1px solid #ffeaa7; border-radius: 3px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="error-icon">❌</div>
            <h1>Booking Failed</h1>
        </div>
        
        <div class="content">
            <p>A booking attempt has failed and requires your attention.</p>
            
            <div class="booking-details">
                <h3>Attempted Booking:</h3>
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Company:</strong> {company}</p>
                <p><strong>Sheet Row:</strong> {row_number}</p>
                <p><strong>Attempt Time:</strong> {attempt_time}</p>
            </div>
            
            <div class="error-details">
                <h3>Error Details:</h3>
                <p><strong>Error Type:</strong> {error_type}</p>
                <p><strong>Error Message:</strong> {error_message}</p>
            </div>
            
            <div class="action-needed">
                <h3>⚠️ Action Required:</h3>
                <p>Please review the error details above and take appropriate action:</p>
                <ul>
                    <li>Check if the contact information is valid</li>
                    <li>Verify the LeadConnector booking page is accessible</li>
                    <li>Review the automation logs for more details</li>
                    <li>Consider manually booking this appointment</li>
                </ul>
            </div>
            
            <p>The row has been left unchanged in your Google Sheet so you can retry or handle manually.</p>
        </div>
        
        <div class="footer">
            <p>This notification was sent by your LeadConnector Booking Automation system.</p>
            <p>Timestamp: {timestamp}</p>
            <p>Check your automation dashboard for more details.</p>
        </div>
    </div>
</body>
</html>
        """
        
        self.summary_template = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background-color: #007bff; color: white; padding: 20px; text-align: center; border-radius: 5px; margin-bottom: 20px; }
        .content { line-height: 1.6; color: #333; }
        .summary-stats { display: flex; justify-content: space-around; margin: 20px 0; }
        .stat-box { text-align: center; padding: 15px; border-radius: 5px; flex: 1; margin: 0 10px; }
        .success-stat { background-color: #d4edda; color: #155724; }
        .failure-stat { background-color: #f8d7da; color: #721c24; }
        .stat-number { font-size: 24px; font-weight: bold; }
        .booking-list { background-color: #f8f9fa; padding: 15px; border-radius: 3px; margin: 20px 0; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Automation Summary Report</h1>
            <p>Booking automation run completed</p>
        </div>
        
        <div class="content">
            <div class="summary-stats">
                <div class="stat-box success-stat">
                    <div class="stat-number">{successful_bookings}</div>
                    <div>Successful Bookings</div>
                </div>
                <div class="stat-box failure-stat">
                    <div class="stat-number">{failed_bookings}</div>
                    <div>Failed Bookings</div>
                </div>
            </div>
            
            <p><strong>Run Duration:</strong> {duration}</p>
            <p><strong>Total Rows Processed:</strong> {total_processed}</p>
            <p><strong>Rows Skipped:</strong> {rows_skipped}</p>
            
            {successful_bookings_list}
            
            {failed_bookings_list}
            
            <p>All booking attempts have been logged and the Google Sheet has been updated accordingly.</p>
        </div>
        
        <div class="footer">
            <p>This report was generated by your LeadConnector Booking Automation system.</p>
            <p>Report generated: {timestamp}</p>
        </div>
    </div>
</body>
</html>
        """
    
    def send_booking_success_notification(self, booking_data: Dict, row_number: int) -> bool:
        """Send notification for successful booking."""
        try:
            if not self._is_configured():
                self.logger.warning("Email not configured, skipping success notification")
                return False
            
            subject = f"✅ Booking Confirmed: {booking_data['name']}"
            
            html_content = self.success_template.format(
                name=booking_data['name'],
                email=booking_data['email'],
                company=booking_data.get('company', 'N/A'),
                booking_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                row_number=row_number,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            )
            
            return self._send_email(subject, html_content)
            
        except Exception as e:
            self.logger.error(f"Error sending success notification: {str(e)}")
            return False
    
    def send_booking_failure_notification(self, booking_data: Dict, row_number: int, error_type: str, error_message: str) -> bool:
        """Send notification for failed booking."""
        try:
            if not self._is_configured():
                self.logger.warning("Email not configured, skipping failure notification")
                return False
            
            subject = f"❌ Booking Failed: {booking_data['name']}"
            
            html_content = self.failure_template.format(
                name=booking_data['name'],
                email=booking_data['email'],
                company=booking_data.get('company', 'N/A'),
                row_number=row_number,
                attempt_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                error_type=error_type,
                error_message=error_message,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            )
            
            return self._send_email(subject, html_content)
            
        except Exception as e:
            self.logger.error(f"Error sending failure notification: {str(e)}")
            return False
    
    def send_automation_summary(self, summary_data: Dict) -> bool:
        """Send summary report after automation run."""
        try:
            if not self._is_configured():
                self.logger.warning("Email not configured, skipping summary notification")
                return False
            
            subject = f"📊 Automation Summary: {summary_data['successful_bookings']} successful, {summary_data['failed_bookings']} failed"
            
            # Format successful bookings list
            successful_list = ""
            if summary_data['successful_bookings'] > 0 and summary_data.get('successful_list'):
                successful_list = '<div class="booking-list"><h3>✅ Successful Bookings:</h3><ul>'
                for booking in summary_data['successful_list']:
                    successful_list += f"<li>{booking['name']} ({booking['email']}) - Row {booking['row']}</li>"
                successful_list += '</ul></div>'
            
            # Format failed bookings list
            failed_list = ""
            if summary_data['failed_bookings'] > 0 and summary_data.get('failed_list'):
                failed_list = '<div class="booking-list"><h3>❌ Failed Bookings:</h3><ul>'
                for booking in summary_data['failed_list']:
                    failed_list += f"<li>{booking['name']} ({booking['email']}) - Row {booking['row']}: {booking['error']}</li>"
                failed_list += '</ul></div>'
            
            html_content = self.summary_template.format(
                successful_bookings=summary_data['successful_bookings'],
                failed_bookings=summary_data['failed_bookings'],
                duration=summary_data.get('duration', 'N/A'),
                total_processed=summary_data.get('total_processed', 0),
                rows_skipped=summary_data.get('rows_skipped', 0),
                successful_bookings_list=successful_list,
                failed_bookings_list=failed_list,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            )
            
            return self._send_email(subject, html_content)
            
        except Exception as e:
            self.logger.error(f"Error sending summary notification: {str(e)}")
            return False
    
    def _is_configured(self) -> bool:
        """Check if email is properly configured."""
        return (self.email_user and 
                self.email_password and 
                self.notification_recipients and 
                len(self.notification_recipients) > 0)
    
    def _send_email(self, subject: str, html_content: str) -> bool:
        """Send email using SMTP."""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.email_user
            message["To"] = ", ".join(self.notification_recipients)
            
            # Add HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Create SMTP session
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_user, self.email_password)
                
                # Send email
                text = message.as_string()
                server.sendmail(self.email_user, self.notification_recipients, text)
            
            self.logger.info(f"Email sent successfully: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email: {str(e)}")
            return False
    
    def test_email_configuration(self) -> Dict:
        """Test email configuration and send a test email."""
        try:
            if not self._is_configured():
                return {
                    'success': False,
                    'error': 'Email not configured. Please set EMAIL_USER, EMAIL_PASSWORD, and NOTIFICATION_RECIPIENTS.'
                }
            
            # Send test email
            subject = "🧪 Test Email - LeadConnector Booking Automation"
            html_content = """
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745;">
                    <h2>✅ Email Configuration Test</h2>
                    <p>This is a test email from your LeadConnector Booking Automation system.</p>
                    <p>If you received this email, your email notifications are configured correctly!</p>
                    <p><strong>Configuration Details:</strong></p>
                    <ul>
                        <li>SMTP Server: {}</li>
                        <li>SMTP Port: {}</li>
                        <li>From: {}</li>
                        <li>Recipients: {}</li>
                    </ul>
                    <p>Timestamp: {}</p>
                </div>
            </body>
            </html>
            """.format(
                self.smtp_server,
                self.smtp_port,
                self.email_user,
                ", ".join(self.notification_recipients),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            )
            
            success = self._send_email(subject, html_content)
            
            if success:
                return {
                    'success': True,
                    'message': 'Test email sent successfully! Check your inbox.'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to send test email. Check your email configuration and credentials.'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Email test failed: {str(e)}'
            }