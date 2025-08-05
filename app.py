"""
Flask web interface for triggering the booking automation.
"""

import asyncio
import threading
from datetime import datetime
from threading import Thread
from flask import Flask, render_template, jsonify, request
from automation import BookingAutomation
from playwright_automation import PlaywrightBookingAutomation
from sheets_client import GoogleSheetsClient
from logger_config import setup_logger
from config import Config
from email_client import EmailNotificationClient

app = Flask(__name__)
logger = setup_logger('flask')
config = Config()

# Global variable to track automation status
automation_status = {
    'running': False,
    'last_run': None,
    'message': 'Ready to start automation'
}

@app.route('/')
def index():
    """Main page with automation controls."""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Simple health check endpoint for deployment monitoring."""
    return jsonify({
        'status': 'healthy',
        'service': 'booking-automation',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/status')
def get_status():
    """Get current automation status."""
    return jsonify(automation_status)

@app.route('/api/start', methods=['POST'])
def start_automation():
    """Start the booking automation."""
    global automation_status
    
    if automation_status['running']:
        return jsonify({'error': 'Automation is already running'}), 400
    
    try:
        # Update status
        automation_status['running'] = True
        automation_status['message'] = 'Starting automation...'
        
        # Start automation in a separate thread
        thread = threading.Thread(target=run_automation_thread)
        thread.daemon = True
        thread.start()
        
        return jsonify({'message': 'Automation started successfully'})
        
    except Exception as e:
        automation_status['running'] = False
        automation_status['message'] = f'Error starting automation: {str(e)}'
        logger.error(f"Error starting automation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/preview')
def preview_data():
    """Preview data from Google Sheets."""
    try:
        # Create a new sheets client with updated config
        from sheets_client import GoogleSheetsClient
        sheets_client = GoogleSheetsClient(config)
        rows = sheets_client.get_all_rows()
        
        # Return first 10 rows for preview
        preview_rows = rows[:10]
        
        return jsonify({
            'total_rows': len(rows),
            'preview_rows': preview_rows
        })
        
    except Exception as e:
        logger.error(f"Error previewing data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """Get or update configuration."""
    if request.method == 'GET':
        return jsonify({
            'google_sheet_url': config.GOOGLE_SHEET_URL,
            'booking_url': config.BOOKING_URL,
            'headless_mode': config.HEADLESS_MODE,
            'delay_between_bookings': config.DELAY_BETWEEN_BOOKINGS
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Update configuration (in a real app, you'd save this to a file or database)
            if 'google_sheet_url' in data:
                config.GOOGLE_SHEET_URL = data['google_sheet_url']
                logger.info(f"Updated Google Sheet URL to: {config.GOOGLE_SHEET_URL}")
            if 'headless_mode' in data:
                config.HEADLESS_MODE = data['headless_mode']
            if 'delay_between_bookings' in data:
                config.DELAY_BETWEEN_BOOKINGS = data['delay_between_bookings']
            
            return jsonify({'message': 'Configuration updated successfully'})
            
        except Exception as e:
            logger.error(f"Error updating config: {str(e)}")
            return jsonify({'error': str(e)}), 500

@app.route('/api/email/test', methods=['POST'])
def test_email():
    """Test email configuration."""
    try:
        email_client = EmailNotificationClient(config)
        result = email_client.test_email_configuration()
        
        if result['success']:
            return jsonify({'message': result['message']})
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Error testing email: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/email/config', methods=['GET'])
def get_email_config():
    """Get current email configuration status."""
    try:
        email_client = EmailNotificationClient(config)
        
        return jsonify({
            'configured': email_client._is_configured(),
            'email_user': config.EMAIL_USER or 'Not set',
            'smtp_server': config.SMTP_SERVER,
            'smtp_port': config.SMTP_PORT,
            'recipients': config.NOTIFICATION_RECIPIENTS
        })
        
    except Exception as e:
        logger.error(f"Error getting email config: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/email/config', methods=['POST'])
def update_email_config():
    """Update email configuration."""
    try:
        data = request.get_json()
        
        if 'email_user' in data:
            config.EMAIL_USER = data['email_user']
        if 'email_password' in data:
            config.EMAIL_PASSWORD = data['email_password']
        if 'smtp_server' in data:
            config.SMTP_SERVER = data['smtp_server']
        if 'smtp_port' in data:
            config.SMTP_PORT = int(data['smtp_port'])
        if 'notification_recipients' in data:
            # Handle both string and list formats
            recipients = data['notification_recipients']
            if isinstance(recipients, str):
                config.NOTIFICATION_RECIPIENTS = [email.strip() for email in recipients.split(',') if email.strip()]
            else:
                config.NOTIFICATION_RECIPIENTS = recipients
        
        return jsonify({'message': 'Email configuration updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating email config: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/enhanced/start', methods=['POST'])
def start_enhanced_automation():
    """Start enhanced Playwright automation with advanced options."""
    global automation_status
    
    if automation_status['running']:
        return jsonify({'error': 'Automation is already running'}), 400
    
    try:
        data = request.get_json() or {}
        
        # Enhanced automation options
        browser_type = data.get('browser_type', 'chromium')  # chromium, firefox, webkit
        headless = data.get('headless', True)
        concurrent = data.get('concurrent', False)
        
        # Update status
        automation_status['running'] = True
        automation_status['message'] = f'Starting enhanced automation with {browser_type}...'
        
        # Start enhanced automation in background thread
        def run_enhanced():
            try:
                import asyncio
                from enhanced_playwright_automation import EnhancedPlaywrightAutomation
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                enhanced_automation = EnhancedPlaywrightAutomation(config)
                stats = loop.run_until_complete(
                    enhanced_automation.run_automation(
                        browser_type=browser_type,
                        headless=headless,
                        concurrent=concurrent
                    )
                )
                
                automation_status['message'] = f"Enhanced automation completed: {stats['successful_bookings']} successful, {stats['failed_bookings']} failed"
                logger.info(f"Enhanced automation completed: {stats}")
                
            except Exception as e:
                automation_status['message'] = f'Enhanced automation failed: {str(e)}'
                logger.error(f"Enhanced automation failed: {str(e)}")
            finally:
                automation_status['running'] = False
                automation_status['last_run'] = datetime.now().isoformat()
        
        Thread(target=run_enhanced, daemon=True).start()
        
        return jsonify({
            'message': f'Enhanced automation started with {browser_type} browser',
            'options': {
                'browser_type': browser_type,
                'headless': headless,
                'concurrent': concurrent
            }
        })
        
    except Exception as e:
        automation_status['running'] = False
        logger.error(f"Error starting enhanced automation: {str(e)}")
        return jsonify({'error': str(e)}), 500

def run_automation_thread():
    """Run automation in a separate thread."""
    global automation_status
    
    try:
        import datetime
        automation_status['message'] = 'Automation running...'
        automation_status['last_run'] = datetime.datetime.now().isoformat()
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Log current config for debugging
        logger.info(f"Starting automation with Google Sheet URL: {config.GOOGLE_SHEET_URL}")
        
               # Use HTTP-based automation (no browser required)
        from automation import BookingAutomation
        booking_automation = BookingAutomation(config)
        stats = loop.run_until_complete(booking_automation.run())
        automation_status['message'] = 'Automation completed successfully'
        logger.info("Automation completed successfully")
        
    except Exception as e:
        automation_status['message'] = f'Automation failed: {str(e)}'
        logger.error(f"Automation failed: {str(e)}")
    
    finally:
        automation_status['running'] = False

if __name__ == '__main__':
    logger.info("Starting Flask application")
    logger.info(f"Flask configuration - Host: {config.FLASK_HOST}, Port: {config.FLASK_PORT}, Debug: {config.FLASK_DEBUG}")
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )
