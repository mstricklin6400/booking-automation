"""
Enhanced Playwright booking automation with multi-browser support, 
concurrent booking, detailed logging, and retry mechanisms.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from sheets_client import GoogleSheetsClient
from email_client import EmailNotificationClient
from config import Config

class EnhancedPlaywrightAutomation:
    """Enhanced Playwright automation with advanced features."""
    
    def __init__(self, config: Config):
        self.config = config
        self.setup_logging()
        self.sheets_client = GoogleSheetsClient(config)
        self.email_client = EmailNotificationClient(config)
        
        # Performance settings
        self.max_concurrent_bookings = 3  # Adjust based on your needs
        self.retry_attempts = 3
        self.retry_delay = 5
        
        # Statistics tracking
        self.stats = {
            'successful_bookings': 0,
            'failed_bookings': 0,
            'skipped_rows': 0,
            'captcha_detected': 0,
            'retry_attempts': 0,
            'start_time': None,
            'end_time': None
        }
        
    def setup_logging(self):
        """Setup detailed logging with multiple handlers."""
        # Create logger
        self.logger = logging.getLogger('enhanced_automation')
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers = []
        
        # File handler for detailed logs
        file_handler = logging.FileHandler('enhanced_booking.log')
        file_handler.setLevel(logging.INFO)
        
        # Console handler for real-time feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    async def run_automation(self, browser_type: str = 'chromium', 
                           headless: bool = False, 
                           concurrent: bool = False) -> Dict:
        """
        Run the enhanced automation with specified browser and options.
        
        Args:
            browser_type: 'chromium', 'firefox', or 'webkit'
            headless: Whether to run in headless mode
            concurrent: Whether to process bookings concurrently
        """
        self.stats['start_time'] = datetime.now()
        self.logger.info(f"Starting enhanced automation with {browser_type} browser")
        self.logger.info(f"Settings: headless={headless}, concurrent={concurrent}")
        
        async with async_playwright() as playwright:
            # Launch browser based on type
            browser = await self.launch_browser(playwright, browser_type, headless)
            
            try:
                # Get booking data from sheets
                booking_data = await self.get_booking_data()
                
                if not booking_data:
                    self.logger.warning("No booking data found")
                    return self.get_final_stats()
                
                self.logger.info(f"Found {len(booking_data)} rows to process")
                
                # Process bookings
                if concurrent:
                    await self.process_concurrent_bookings(browser, booking_data)
                else:
                    await self.process_sequential_bookings(browser, booking_data)
                
            finally:
                await browser.close()
                
        self.stats['end_time'] = datetime.now()
        final_stats = self.get_final_stats()
        
        # Send summary email
        await self.send_summary_notification(final_stats)
        
        self.logger.info("Enhanced automation completed")
        return final_stats
    
    async def launch_browser(self, playwright, browser_type: str, headless: bool) -> Browser:
        """Launch browser with enhanced options."""
        browser_options = {
            'headless': headless,
            'args': [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--disable-dev-shm-usage'
            ]
        }
        
        if browser_type == 'firefox':
            browser = await playwright.firefox.launch(**browser_options)
            self.logger.info("🦊 Launched Firefox browser")
        elif browser_type == 'webkit':
            browser = await playwright.webkit.launch(**browser_options)
            self.logger.info("🧭 Launched WebKit (Safari-like) browser")
        else:  # chromium (default)
            browser = await playwright.chromium.launch(**browser_options)
            self.logger.info("🌐 Launched Chromium browser")
            
        return browser
    
    async def get_booking_data(self) -> List[Dict]:
        """Get booking data from Google Sheets."""
        try:
            rows = await asyncio.to_thread(self.sheets_client.get_all_rows)
            
            # Filter out completed rows and validate data
            valid_rows = []
            for i, row in enumerate(rows, start=2):  # Start at row 2 (skip header)
                if row.get('status', '').lower() == 'done':
                    continue
                    
                if self.validate_booking_data(row):
                    row['row_number'] = i
                    valid_rows.append(row)
                else:
                    self.stats['skipped_rows'] += 1
                    
            return valid_rows
            
        except Exception as e:
            self.logger.error(f"Error getting booking data: {e}")
            return []
    
    def validate_booking_data(self, row: Dict) -> bool:
        """Validate that row has required booking data."""
        name = row.get('name', '').strip()
        email = row.get('email', '').strip()
        company = row.get('company', '').strip()
        
        if not email or '@' not in email:
            self.logger.warning(f"Invalid email: {email}")
            return False
            
        if not (name or company):
            self.logger.warning(f"Missing name and company for {email}")
            return False
            
        return True
    
    async def process_concurrent_bookings(self, browser: Browser, booking_data: List[Dict]):
        """Process bookings concurrently for faster execution."""
        self.logger.info(f"Processing {len(booking_data)} bookings concurrently (max {self.max_concurrent_bookings} at once)")
        
        semaphore = asyncio.Semaphore(self.max_concurrent_bookings)
        
        async def process_with_semaphore(booking_info):
            async with semaphore:
                return await self.process_single_booking(browser, booking_info)
        
        # Create tasks for all bookings
        tasks = [process_with_semaphore(booking) for booking in booking_data]
        
        # Process with progress tracking
        completed = 0
        for task in asyncio.as_completed(tasks):
            await task
            completed += 1
            self.logger.info(f"Progress: {completed}/{len(booking_data)} bookings processed")
    
    async def process_sequential_bookings(self, browser: Browser, booking_data: List[Dict]):
        """Process bookings one by one for more stability."""
        self.logger.info(f"Processing {len(booking_data)} bookings sequentially")
        
        for i, booking_info in enumerate(booking_data, 1):
            self.logger.info(f"Processing booking {i}/{len(booking_data)}")
            await self.process_single_booking(browser, booking_info)
            
            # Add delay between bookings to avoid rate limiting
            if i < len(booking_data):
                delay = self.config.DELAY_BETWEEN_BOOKINGS
                self.logger.info(f"Waiting {delay} seconds before next booking...")
                await asyncio.sleep(delay)
    
    async def process_single_booking(self, browser: Browser, booking_info: Dict) -> bool:
        """Process a single booking with retry logic and error handling."""
        name = booking_info.get('name', '') or booking_info.get('company', '')
        email = booking_info['email']
        row_number = booking_info['row_number']
        
        self.logger.info(f"🎯 Starting booking for {name} ({email}) - Row {row_number}")
        
        for attempt in range(self.retry_attempts):
            try:
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                page = await context.new_page()
                
                # Attempt booking
                success = await self.perform_booking(page, booking_info)
                
                await context.close()
                
                if success:
                    self.stats['successful_bookings'] += 1
                    self.logger.info(f"✅ Successfully booked appointment for {name}")
                    
                    # Mark as done in Google Sheets
                    await self.mark_as_completed(row_number)
                    
                    # Send success notification
                    await self.send_success_notification(booking_info)
                    
                    return True
                else:
                    if attempt < self.retry_attempts - 1:
                        self.stats['retry_attempts'] += 1
                        self.logger.warning(f"⚠️ Booking failed for {name}, retrying in {self.retry_delay} seconds... (attempt {attempt + 1}/{self.retry_attempts})")
                        await asyncio.sleep(self.retry_delay)
                    else:
                        self.stats['failed_bookings'] += 1
                        self.logger.error(f"❌ Booking failed for {name} after {self.retry_attempts} attempts")
                        
                        # Send failure notification
                        await self.send_failure_notification(booking_info, "Booking failed after multiple attempts")
                        
                        return False
                        
            except Exception as e:
                self.logger.error(f"Error during booking attempt {attempt + 1} for {name}: {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    self.stats['failed_bookings'] += 1
                    await self.send_failure_notification(booking_info, f"Technical error: {str(e)}")
                    return False
        
        return False
    
    async def perform_booking(self, page: Page, booking_info: Dict) -> bool:
        """Perform the actual booking on the LeadConnector page using real widget interaction."""
        try:
            name = booking_info.get('name', '') or booking_info.get('company', '')
            email = booking_info['email']
            company = booking_info.get('company', '')
            
            # Use the working LeadConnector booking URL
            booking_url = "https://api.leadconnectorhq.com/widget/booking/vggoBfO4Zr1RTp4M4h8m"
            self.logger.info(f"🌐 Loading booking page: {booking_url}")
            
            # Navigate to booking page with timeout
            await page.goto(booking_url, wait_until='networkidle', timeout=30000)
            
            # Check for CAPTCHA
            if await self.detect_captcha(page):
                self.stats['captcha_detected'] += 1
                self.logger.warning("🔒 CAPTCHA detected, skipping this booking")
                return False
            
            # Wait for page to load and find available time slots
            self.logger.info("⏳ Waiting for calendar to load...")
            await page.wait_for_timeout(3000)
            
            # Enhanced date selection with more specific selectors for LeadConnector
            date_selectors = [
                'button[data-testid*="date"]:not([disabled])',
                '.calendar-date:not(.disabled):not(.booked)',
                '.available-date button',
                '.date-picker button:not([disabled])',
                '[role="button"]:not([disabled]):not([aria-disabled="true"])',
                '.day:not(.disabled):not(.booked)',
                '.calendar-day.available'
            ]
            
            date_clicked = False
            for selector in date_selectors:
                try:
                    # Wait for element and check if it's actually clickable
                    await page.wait_for_selector(selector, timeout=5000)
                    elements = await page.query_selector_all(selector)
                    
                    for element in elements:
                        # Check if element is visible and clickable
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()
                        
                        if is_visible and is_enabled:
                            await element.click()
                            self.logger.info(f"📅 Clicked date using selector: {selector}")
                            date_clicked = True
                            break
                    
                    if date_clicked:
                        break
                        
                except Exception as e:
                    self.logger.debug(f"Date selector {selector} failed: {e}")
                    continue
            
            if not date_clicked:
                self.logger.error("❌ Could not find available date")
                return False
            
            # Wait for time slots to load
            await page.wait_for_timeout(2000)
            
            # Enhanced time selection with more specific selectors
            time_selectors = [
                'button[data-testid*="time"]:not([disabled])',
                '.time-slot button:not([disabled])',
                '.available-time button',
                '.time-picker button:not([disabled])',
                '[role="button"][aria-label*="time"]:not([disabled])',
                '.time:not(.disabled):not(.booked)',
                '.time-slot.available'
            ]
            
            time_clicked = False
            for selector in time_selectors:
                try:
                    # Wait for time slots to be available
                    await page.wait_for_selector(selector, timeout=5000)
                    elements = await page.query_selector_all(selector)
                    
                    for element in elements:
                        # Check if element is visible and clickable
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()
                        
                        if is_visible and is_enabled:
                            await element.click()
                            self.logger.info(f"🕐 Clicked time using selector: {selector}")
                            time_clicked = True
                            break
                    
                    if time_clicked:
                        break
                        
                except Exception as e:
                    self.logger.debug(f"Time selector {selector} failed: {e}")
                    continue
            
            if not time_clicked:
                self.logger.error("❌ Could not find available time slot")
                return False
            
            # Wait for form to appear
            await page.wait_for_timeout(2000)
            
            # Fill out the booking form with dynamic field detection
            form_filled = await self.fill_booking_form(page, name, email, company)
            
            if not form_filled:
                self.logger.error("❌ Could not fill booking form")
                return False
            
            # Enhanced form submission with more specific selectors
            submit_selectors = [
                'button[data-testid*="submit"]:not([disabled])',
                'button[data-testid*="book"]:not([disabled])',
                'button[data-testid*="confirm"]:not([disabled])',
                'button[type="submit"]:not([disabled])',
                '.submit-btn:not([disabled])',
                '.book-btn:not([disabled])',
                '.confirm-btn:not([disabled])',
                '[role="button"][aria-label*="book"]:not([disabled])',
                '[role="button"][aria-label*="submit"]:not([disabled])',
                'input[type="submit"]:not([disabled])'
            ]
            
            form_submitted = False
            for selector in submit_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    elements = await page.query_selector_all(selector)
                    
                    for element in elements:
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()
                        
                        if is_visible and is_enabled:
                            # Scroll element into view before clicking
                            await element.scroll_into_view_if_needed()
                            await element.click()
                            self.logger.info(f"📤 Submitted form using selector: {selector}")
                            form_submitted = True
                            break
                    
                    if form_submitted:
                        break
                        
                except Exception as e:
                    self.logger.debug(f"Submit selector {selector} failed: {e}")
                    continue
            
            if not form_submitted:
                self.logger.error("❌ Could not find submit button")
                return False
            
            # Wait for confirmation
            await page.wait_for_timeout(3000)
            
            # Check for success indicators
            success_indicators = [
                'confirmation', 'success', 'booked', 'scheduled',
                'thank you', 'confirmed', 'appointment'
            ]
            
            page_content = await page.content()
            page_text = page_content.lower()
            
            for indicator in success_indicators:
                if indicator in page_text:
                    self.logger.info(f"✅ Success indicator found: '{indicator}'")
                    return True
            
            # Check current URL for success patterns
            current_url = page.url.lower()
            if any(indicator in current_url for indicator in ['success', 'confirmation', 'thank']):
                self.logger.info("✅ Success detected from URL")
                return True
            
            self.logger.warning("⚠️ No clear success indicator found")
            return False
            
        except Exception as e:
            self.logger.error(f"Error during booking process: {e}")
            return False
    
    async def fill_booking_form(self, page: Page, name: str, email: str, company: str) -> bool:
        """Dynamically detect and fill booking form fields."""
        try:
            self.logger.info("📝 Filling booking form...")
            
            # Get all form inputs
            inputs = await page.query_selector_all('input, textarea, select')
            
            for input_elem in inputs:
                try:
                    input_type = await input_elem.get_attribute('type') or 'text'
                    input_name = await input_elem.get_attribute('name') or ''
                    input_placeholder = await input_elem.get_attribute('placeholder') or ''
                    input_id = await input_elem.get_attribute('id') or ''
                    
                    # Combine all attributes for field detection
                    field_info = f"{input_name} {input_placeholder} {input_id}".lower()
                    
                    # Detect and fill name field
                    if any(keyword in field_info for keyword in ['name', 'full', 'contact']):
                        if name:
                            await input_elem.fill(name)
                            self.logger.info(f"📝 Filled name field: {name}")
                    
                    # Detect and fill email field
                    elif input_type == 'email' or any(keyword in field_info for keyword in ['email', 'mail']):
                        await input_elem.fill(email)
                        self.logger.info(f"📧 Filled email field: {email}")
                    
                    # Detect and fill company field
                    elif any(keyword in field_info for keyword in ['company', 'organization', 'business']):
                        if company:
                            await input_elem.fill(company)
                            self.logger.info(f"🏢 Filled company field: {company}")
                    
                    # Detect and fill phone field (optional)
                    elif input_type in ['tel', 'phone'] or any(keyword in field_info for keyword in ['phone', 'tel', 'mobile']):
                        await input_elem.fill('555-0123')  # Placeholder phone
                        self.logger.info("📞 Filled phone field with placeholder")
                        
                except Exception as e:
                    # Continue if individual field fails
                    continue
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error filling form: {e}")
            return False
    
    async def detect_captcha(self, page: Page) -> bool:
        """Detect if CAPTCHA is present on the page."""
        captcha_selectors = [
            'iframe[title*="captcha"]',
            'iframe[src*="captcha"]',
            '.captcha',
            '#captcha',
            '.g-recaptcha',
            '.h-captcha'
        ]
        
        for selector in captcha_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    return True
            except:
                continue
        
        return False
    
    async def mark_as_completed(self, row_number: int):
        """Mark booking as completed in Google Sheets."""
        try:
            await asyncio.to_thread(
                self.sheets_client.update_cell,
                row_number, 4, 'done'  # Assuming status is in column 4
            )
            self.logger.info(f"✅ Marked row {row_number} as completed in Google Sheets")
        except Exception as e:
            self.logger.error(f"Error marking row {row_number} as completed: {e}")
    
    async def send_success_notification(self, booking_info: Dict):
        """Send success notification email."""
        try:
            await asyncio.to_thread(
                self.email_client.send_booking_success_notification,
                booking_info, booking_info['row_number']
            )
        except Exception as e:
            self.logger.error(f"Error sending success notification: {e}")
    
    async def send_failure_notification(self, booking_info: Dict, error_message: str):
        """Send failure notification email."""
        try:
            await asyncio.to_thread(
                self.email_client.send_booking_failure_notification,
                booking_info, booking_info['row_number'], 
                'Booking Failed', error_message
            )
        except Exception as e:
            self.logger.error(f"Error sending failure notification: {e}")
    
    async def send_summary_notification(self, stats: Dict):
        """Send automation summary email."""
        try:
            duration = stats['duration']
            summary_data = {
                'successful_bookings': stats['successful_bookings'],
                'failed_bookings': stats['failed_bookings'],
                'duration': duration,
                'total_processed': stats['successful_bookings'] + stats['failed_bookings'],
                'rows_skipped': stats['skipped_rows'],
                'captcha_detected': stats['captcha_detected'],
                'retry_attempts': stats['retry_attempts']
            }
            
            await asyncio.to_thread(
                self.email_client.send_automation_summary,
                summary_data
            )
        except Exception as e:
            self.logger.error(f"Error sending summary notification: {e}")
    
    def get_final_stats(self) -> Dict:
        """Get final automation statistics."""
        if self.stats['start_time'] and self.stats['end_time']:
            duration = str(self.stats['end_time'] - self.stats['start_time']).split('.')[0]
        else:
            duration = 'Unknown'
        
        return {
            'successful_bookings': self.stats['successful_bookings'],
            'failed_bookings': self.stats['failed_bookings'],
            'skipped_rows': self.stats['skipped_rows'],
            'captcha_detected': self.stats['captcha_detected'],
            'retry_attempts': self.stats['retry_attempts'],
            'duration': duration,
            'total_processed': self.stats['successful_bookings'] + self.stats['failed_bookings']
        }

# Example usage and testing
async def main():
    """Example usage of enhanced automation."""
    config = Config()
    automation = EnhancedPlaywrightAutomation(config)
    
    # Run with different configurations
    
    # Option 1: Sequential processing with visible Chromium browser
    # stats = await automation.run_automation(
    #     browser_type='chromium',
    #     headless=False,
    #     concurrent=False
    # )
    
    # Option 2: Concurrent processing with headless Firefox
    stats = await automation.run_automation(
        browser_type='firefox',
        headless=True,
        concurrent=True
    )
    
    print("\n📊 Final Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(main())