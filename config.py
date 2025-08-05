"""
Configuration settings for the booking automation application.
"""

import os

class Config:
    """Application configuration class."""
    
    def __init__(self):
        # Google Sheets configuration
        self.GOOGLE_SHEET_URL = os.getenv('GOOGLE_SHEET_URL', '')
        
        # LeadConnector booking URL
        self.BOOKING_URL = 'https://api.leadconnectorhq.com/widget/booking/vggoBfO4Zr1RTp4M4h8m'
        
        # Playwright configuration
        self.HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'true').lower() == 'true'
        
        # Automation settings
        self.DELAY_BETWEEN_BOOKINGS = int(os.getenv('DELAY_BETWEEN_BOOKINGS', '5'))
        self.MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
        self.RETRY_DELAY = int(os.getenv('RETRY_DELAY', '2'))
        
        # Logging configuration
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE = os.getenv('LOG_FILE', 'automation.log')
        self.ERROR_LOG_FILE = os.getenv('ERROR_LOG_FILE', 'errors.log')
        
        # Flask configuration
        self.FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
        self.FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
        self.FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
        
        # Google API credentials
        self.GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', './credentials.json')
        self.GOOGLE_SHEETS_CREDENTIALS = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
        self.GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        # Email notification settings
        self.EMAIL_USER = os.getenv('EMAIL_USER', None)
        self.EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', None)
        self.SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        
        # Parse notification recipients from comma-separated string
        recipients_str = os.getenv('NOTIFICATION_RECIPIENTS', '')
        self.NOTIFICATION_RECIPIENTS = [email.strip() for email in recipients_str.split(',') if email.strip()]
    
    def validate(self):
        """Validate configuration settings."""
        errors = []
        
        if not self.GOOGLE_SHEET_URL:
            errors.append("GOOGLE_SHEET_URL is required")
        
        if not self.BOOKING_URL:
            errors.append("BOOKING_URL is required")
        
        if self.DELAY_BETWEEN_BOOKINGS < 1:
            errors.append("DELAY_BETWEEN_BOOKINGS must be at least 1 second")
        
        if self.MAX_RETRIES < 0:
            errors.append("MAX_RETRIES must be non-negative")
        
        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))
        
        return True
    
    def __str__(self):
        """String representation of configuration (excluding sensitive data)."""
        config_items = []
        for key, value in self.__dict__.items():
            if 'credential' in key.lower() or 'password' in key.lower():
                value = '***' if value else None
            config_items.append(f"{key}: {value}")
        
        return "Configuration:\n" + "\n".join(f"  {item}" for item in config_items)
