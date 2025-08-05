"""
Working browser automation using Playwright for LeadConnector bookings.
This uses real browser interaction instead of HTTP requests.
"""

import asyncio
import logging
from datetime import datetime
from playwright.async_api import async_playwright
from sheets_client import GoogleSheetsClient
from email_client import EmailNotificationClient
from config import Config

class WorkingBrowserAutomation:
    """Browser automation that actually works with LeadConnector widgets."""
    
    def __init__(self, config: Config):
        self.config = config
        self.sheets_client = GoogleSheetsClient(config)
        self.email_client = EmailNotificationClient(config)
        self.booking_url = "https://api.leadconnectorhq.com/widget/booking/vggoBfO4Zr1RTp4M4h8m"
        
        # Setup logging
        self.logger = logging.getLogger('working_automation')
        self.logger.setLevel(logging.INFO)
        
        # Statistics
        self.stats = {
            'successful_bookings': 0,
            'failed_bookings': 0,
            'start_time': datetime.now()
        }
    
    async def run(self):
        """Run the working browser automation."""
        self.logger.info("🚀 Starting working browser automation with real Playwright interaction")
        
        async with async_playwright() as p:
            # Launch browser in visible mode for debugging
            browser = await p.chromium.launch(
                headless=self.config.HEADLESS_MODE,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            try:
                # Get booking data
                rows = self.sheets_client.get_all_rows()
                pending_rows = []
                
                for i, row in enumerate(rows, start=2):
                    if row.get('status', '').lower() != 'done':
                        name = row.get('name', '') or row.get('company', '')
                        email = row.get('email', '')
                        company = row.get('company', '') or name
                        
                        if email and '@' in email and name:
                            pending_rows.append({
                                'row_number': i,
                                'name': name,
                                'email': email,
                                'company': company
                            })
                
                self.logger.info(f"📋 Found {len(pending_rows)} bookings to process")
                
                # Process each booking
                for booking_info in pending_rows:
                    await self.process_single_booking(browser, booking_info)
                    
                    # Wait between bookings
                    if len(pending_rows) > 1:
                        await asyncio.sleep(self.config.DELAY_BETWEEN_BOOKINGS)
                
            finally:
                await browser.close()
        
        # Send summary
        duration = datetime.now() - self.stats['start_time']
        self.logger.info(f"✅ Automation completed: {self.stats['successful_bookings']} successful, {self.stats['failed_bookings']} failed")
        
        return self.stats
    
    async def process_single_booking(self, browser, booking_info):
        """Process a single booking with real browser interaction."""
        name = booking_info['name']
        email = booking_info['email']
        company = booking_info['company']
        row_number = booking_info['row_number']
        
        self.logger.info(f"🎯 Processing booking for {name} ({email})")
        
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate to booking page
            self.logger.info(f"🌐 Loading booking page: {self.booking_url}")
            await page.goto(self.booking_url, wait_until='networkidle', timeout=30000)
            
            # Wait for page to load
            await page.wait_for_timeout(3000)
            
            # Take screenshot for debugging
            await page.screenshot(path=f"booking_page_{row_number}.png")
            
            # Look for available dates - try multiple selectors
            date_clicked = await self.click_available_date(page)
            if not date_clicked:
                self.logger.error(f"❌ Could not find available date for {name}")
                self.stats['failed_bookings'] += 1
                return False
            
            # Wait for time slots to load
            await page.wait_for_timeout(2000)
            
            # Look for available times
            time_clicked = await self.click_available_time(page)
            if not time_clicked:
                self.logger.error(f"❌ Could not find available time for {name}")
                self.stats['failed_bookings'] += 1
                return False
            
            # Wait for form to appear
            await page.wait_for_timeout(2000)
            
            # Fill the booking form
            form_filled = await self.fill_booking_form(page, name, email, company)
            if not form_filled:
                self.logger.error(f"❌ Could not fill form for {name}")
                self.stats['failed_bookings'] += 1
                return False
            
            # Submit the form
            form_submitted = await self.submit_booking_form(page)
            if not form_submitted:
                self.logger.error(f"❌ Could not submit form for {name}")
                self.stats['failed_bookings'] += 1
                return False
            
            # Wait for confirmation
            await page.wait_for_timeout(3000)
            
            # Check for success
            success = await self.check_booking_success(page)
            if success:
                self.logger.info(f"✅ Successfully booked appointment for {name}")
                
                # Mark as done in sheets
                self.sheets_client.update_cell(row_number, 4, 'done')
                
                # Send success email
                try:
                    self.email_client.send_booking_success_notification(booking_info, row_number)
                except Exception as e:
                    self.logger.warning(f"Email notification failed: {e}")
                
                self.stats['successful_bookings'] += 1
                return True
            else:
                self.logger.error(f"❌ Booking confirmation not detected for {name}")
                self.stats['failed_bookings'] += 1
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error processing booking for {name}: {e}")
            self.stats['failed_bookings'] += 1
            return False
            
        finally:
            await context.close()
    
    async def click_available_date(self, page):
        """Click on the first available date."""
        date_selectors = [
            # Modern selectors for LeadConnector
            'button[data-testid*="date"]:not([disabled])',
            'button[aria-label*="date"]:not([disabled])',
            '[role="button"]:not([disabled]):not([aria-disabled="true"])',
            
            # General calendar selectors
            '.calendar-date:not(.disabled):not(.booked)',
            '.available-date button',
            '.date-picker button:not([disabled])',
            '.day:not(.disabled):not(.booked)',
            '.calendar-day.available',
            
            # Fallback selectors
            'button:not([disabled])',
            '[data-date]:not([disabled])'
        ]
        
        for selector in date_selectors:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                elements = await page.query_selector_all(selector)
                
                for element in elements:
                    is_visible = await element.is_visible()
                    is_enabled = await element.is_enabled()
                    
                    if is_visible and is_enabled:
                        # Get element text for logging
                        text = await element.inner_text()
                        await element.click()
                        self.logger.info(f"📅 Clicked date: {text} using selector: {selector}")
                        return True
                        
            except Exception as e:
                self.logger.debug(f"Date selector {selector} failed: {e}")
                continue
        
        return False
    
    async def click_available_time(self, page):
        """Click on the first available time slot."""
        time_selectors = [
            # Modern selectors for LeadConnector
            'button[data-testid*="time"]:not([disabled])',
            'button[aria-label*="time"]:not([disabled])',
            'button[data-time]:not([disabled])',
            
            # General time slot selectors
            '.time-slot button:not([disabled])',
            '.available-time button',
            '.time-picker button:not([disabled])',
            '.time:not(.disabled):not(.booked)',
            '.time-slot.available',
            
            # Fallback selectors that might contain time
            'button:not([disabled])[aria-label*="AM"]',
            'button:not([disabled])[aria-label*="PM"]',
            'button:not([disabled])[title*=":"]'
        ]
        
        for selector in time_selectors:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                elements = await page.query_selector_all(selector)
                
                for element in elements:
                    is_visible = await element.is_visible()
                    is_enabled = await element.is_enabled()
                    
                    if is_visible and is_enabled:
                        # Get element text for logging
                        text = await element.inner_text()
                        await element.click()
                        self.logger.info(f"🕐 Clicked time: {text} using selector: {selector}")
                        return True
                        
            except Exception as e:
                self.logger.debug(f"Time selector {selector} failed: {e}")
                continue
        
        return False
    
    async def fill_booking_form(self, page, name, email, company):
        """Fill the booking form with customer information."""
        try:
            # Get all input fields
            inputs = await page.query_selector_all('input, textarea, select')
            
            filled_count = 0
            
            for input_elem in inputs:
                try:
                    input_type = await input_elem.get_attribute('type') or 'text'
                    input_name = (await input_elem.get_attribute('name') or '').lower()
                    input_placeholder = (await input_elem.get_attribute('placeholder') or '').lower()
                    input_id = (await input_elem.get_attribute('id') or '').lower()
                    
                    # Combine attributes for field detection
                    field_info = f"{input_name} {input_placeholder} {input_id}"
                    
                    # Fill name field
                    if any(keyword in field_info for keyword in ['name', 'full', 'contact', 'first']):
                        await input_elem.fill(name)
                        self.logger.info(f"📝 Filled name field: {name}")
                        filled_count += 1
                    
                    # Fill email field
                    elif input_type == 'email' or any(keyword in field_info for keyword in ['email', 'mail']):
                        await input_elem.fill(email)
                        self.logger.info(f"📧 Filled email field: {email}")
                        filled_count += 1
                    
                    # Fill company field
                    elif any(keyword in field_info for keyword in ['company', 'organization', 'business']):
                        await input_elem.fill(company)
                        self.logger.info(f"🏢 Filled company field: {company}")
                        filled_count += 1
                    
                    # Fill phone field with placeholder
                    elif input_type in ['tel', 'phone'] or any(keyword in field_info for keyword in ['phone', 'tel', 'mobile']):
                        await input_elem.fill('555-0123')
                        self.logger.info("📞 Filled phone field")
                        filled_count += 1
                        
                except Exception as e:
                    continue
            
            self.logger.info(f"📝 Filled {filled_count} form fields")
            return filled_count > 0
            
        except Exception as e:
            self.logger.error(f"Error filling form: {e}")
            return False
    
    async def submit_booking_form(self, page):
        """Submit the booking form."""
        submit_selectors = [
            # Modern submit selectors
            'button[data-testid*="submit"]:not([disabled])',
            'button[data-testid*="book"]:not([disabled])',
            'button[data-testid*="confirm"]:not([disabled])',
            
            # Standard submit selectors
            'button[type="submit"]:not([disabled])',
            'input[type="submit"]:not([disabled])',
            
            # Class-based selectors
            '.submit-btn:not([disabled])',
            '.book-btn:not([disabled])',
            '.confirm-btn:not([disabled])',
            '.booking-submit:not([disabled])',
            
            # Aria label selectors
            'button[aria-label*="book"]:not([disabled])',
            'button[aria-label*="submit"]:not([disabled])',
            'button[aria-label*="confirm"]:not([disabled])',
            
            # Text-based fallback
            'button:not([disabled])'
        ]
        
        for selector in submit_selectors:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                elements = await page.query_selector_all(selector)
                
                for element in elements:
                    is_visible = await element.is_visible()
                    is_enabled = await element.is_enabled()
                    
                    if is_visible and is_enabled:
                        # Check if button text suggests it's a submit button
                        text = (await element.inner_text()).lower()
                        if any(keyword in text for keyword in ['book', 'submit', 'confirm', 'schedule', 'continue']):
                            await element.scroll_into_view_if_needed()
                            await element.click()
                            self.logger.info(f"📤 Clicked submit button: {text}")
                            return True
                        
            except Exception as e:
                self.logger.debug(f"Submit selector {selector} failed: {e}")
                continue
        
        return False
    
    async def check_booking_success(self, page):
        """Check if the booking was successful."""
        try:
            # Wait a bit for any redirects or confirmations
            await page.wait_for_timeout(3000)
            
            # Check page content for success indicators
            page_content = await page.content()
            page_text = page_content.lower()
            
            success_indicators = [
                'confirmation', 'success', 'booked', 'scheduled',
                'thank you', 'confirmed', 'appointment', 'booking confirmed'
            ]
            
            for indicator in success_indicators:
                if indicator in page_text:
                    self.logger.info(f"✅ Success indicator found: '{indicator}'")
                    return True
            
            # Check URL for success patterns
            current_url = page.url.lower()
            if any(indicator in current_url for indicator in ['success', 'confirmation', 'thank', 'booked']):
                self.logger.info("✅ Success detected from URL")
                return True
            
            # Look for success elements
            success_selectors = [
                '[data-testid*="success"]',
                '[data-testid*="confirmation"]',
                '.success',
                '.confirmation',
                '.booking-success'
            ]
            
            for selector in success_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        self.logger.info(f"✅ Success element found: {selector}")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking success: {e}")
            return False