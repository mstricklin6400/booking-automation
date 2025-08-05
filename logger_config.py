"""
Logging configuration for the booking automation application.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from config import Config

def setup_logger(name: str, config: Config = None) -> logging.Logger:
    """Set up and configure logger for the application."""
    
    if config is None:
        config = Config()
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Set log level
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(levelname)s: %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler for general logs
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            config.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not create file handler for {config.LOG_FILE}: {e}")
    
    # Error file handler
    try:
        error_handler = logging.handlers.RotatingFileHandler(
            config.ERROR_LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)
    except Exception as e:
        logger.warning(f"Could not create error handler for {config.ERROR_LOG_FILE}: {e}")
    
    return logger

class AutomationLogger:
    """Specialized logger for automation operations."""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.logger = setup_logger('automation', self.config)
        self.start_time = None
        self.operation_count = 0
        self.success_count = 0
        self.error_count = 0
    
    def start_operation(self, operation_name: str):
        """Log the start of an operation."""
        self.start_time = datetime.now()
        self.operation_count = 0
        self.success_count = 0
        self.error_count = 0
        self.logger.info(f"Starting {operation_name}")
        self.logger.info("-" * 50)
    
    def log_row_processing(self, row_index: int, name: str, action: str):
        """Log row processing."""
        self.operation_count += 1
        self.logger.info(f"Row {row_index}: {action} for '{name}'")
    
    def log_success(self, row_index: int, name: str, message: str = ""):
        """Log successful operation."""
        self.success_count += 1
        msg = f"Row {row_index}: SUCCESS - {name}"
        if message:
            msg += f" - {message}"
        self.logger.info(msg)
    
    def log_error(self, row_index: int, name: str, error: str):
        """Log error in operation."""
        self.error_count += 1
        self.logger.error(f"Row {row_index}: ERROR - {name} - {error}")
    
    def log_skip(self, row_index: int, name: str, reason: str):
        """Log skipped operation."""
        self.logger.info(f"Row {row_index}: SKIPPED - {name} - {reason}")
    
    def end_operation(self, operation_name: str):
        """Log the end of an operation with summary."""
        if self.start_time:
            duration = datetime.now() - self.start_time
            self.logger.info("-" * 50)
            self.logger.info(f"Completed {operation_name}")
            self.logger.info(f"Duration: {duration}")
            self.logger.info(f"Total rows processed: {self.operation_count}")
            self.logger.info(f"Successful operations: {self.success_count}")
            self.logger.info(f"Failed operations: {self.error_count}")
            if self.operation_count > 0:
                success_rate = (self.success_count / self.operation_count) * 100
                self.logger.info(f"Success rate: {success_rate:.1f}%")
    
    def log_config(self):
        """Log current configuration (excluding sensitive data)."""
        self.logger.info("Configuration loaded:")
        self.logger.info(f"  Google Sheet URL: {self.config.GOOGLE_SHEET_URL}")
        self.logger.info(f"  Booking URL: {self.config.BOOKING_URL}")
        self.logger.info(f"  Headless mode: {self.config.HEADLESS_MODE}")
        self.logger.info(f"  Delay between bookings: {self.config.DELAY_BETWEEN_BOOKINGS}s")
        self.logger.info(f"  Max retries: {self.config.MAX_RETRIES}")

def log_environment_info():
    """Log information about the environment."""
    logger = setup_logger('environment')
    
    logger.info("Environment Information:")
    import sys
    logger.info(f"  Python version: {sys.version}")
    logger.info(f"  Working directory: {os.getcwd()}")
    logger.info(f"  Environment variables:")
    
    env_vars = [
        'GOOGLE_SHEET_URL',
        'GOOGLE_SHEETS_CREDENTIALS',
        'GOOGLE_APPLICATION_CREDENTIALS',
        'HEADLESS_MODE',
        'DELAY_BETWEEN_BOOKINGS',
        'LOG_LEVEL'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if 'credential' in var.lower():
                logger.info(f"    {var}: [SET]")
            else:
                logger.info(f"    {var}: {value}")
        else:
            logger.info(f"    {var}: [NOT SET]")
