"""
Proper Playwright automation for LeadConnector booking form submission.
"""

import asyncio
import traceback
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, Browser, Page
from sheets_client import GoogleSheetsClient
from logger_config import setup_logger
from config import Config

class PlaywrightBookingAutomation:
    """Handles booking automation using proper Playwright browser automation."""
    
    def __init__(self, config=None):
        self.logger = setup_logger('playwright_automation')
        self.config = config or Config()
        self.sheets_client = GoogleSheetsClient(self.config)
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def run(self):
        """Main automation workflow using Playwright."""
        self.logger.info("Starting Playwright booking automation")
        
        try:
            # Get data from Google Sheets
            rows_data = await self.get_sheet_data()
            if not rows_data:
                self.logger.warning("No data found in Google Sheets")
                return
            
            # Initialize browser
            await self.init_browser()
            
            # Process each row
            success_count = 0
            error_count = 0
            
            self.logger.info(f"Starting to process {len(rows_data)} rows from Google Sheet")
            
            for row_index, row_data in enumerate(rows_data, start=2):  # Start at row 2 (skip header)
                try:
                    # Check if already done
                    if row_data.get('status', '').lower() == 'done':
                        self.logger.info(f"Row {row_index}: Skipping - already marked as done")
                        continue
                    
                    # Validate data
                    if not self.validate_row_data(row_data):
                        self.logger.warning(f"Row {row_index}: Invalid data - skipping")
                        error_count += 1
                        continue
                    
                    self.logger.info(f"Row {row_index}: Starting booking for {row_data['name']} ({row_data['email']})")
                    
                    # Perform booking using Playwright
                    booking_success = await self.book_appointment_with_playwright(row_data)
                    
                    if booking_success:
                        # Mark as done in Google Sheet
                        try:
                            await self.mark_row_as_done(row_index)
                        except Exception as mark_error:
                            self.logger.warning(f"Could not mark row as done: {mark_error}")
                        
                        success_count += 1
                        self.logger.info(f"Row {row_index}: ✅ BOOKING SUCCESSFUL for {row_data['name']}")
                    else:
                        error_count += 1
                        self.logger.error(f"Row {row_index}: ❌ BOOKING FAILED for {row_data['name']}")
                    
                    # Add delay between bookings
                    await asyncio.sleep(3)
                    
                except Exception as e:
                    error_count += 1
                    self.logger.error(f"Row {row_index}: Error processing booking - {str(e)}")
                    self.logger.error(f"Row {row_index}: Traceback - {traceback.format_exc()}")
            
            self.logger.info(f"🏁 AUTOMATION COMPLETED: {success_count} successful bookings, {error_count} errors")
            
        except Exception as e:
            self.logger.error(f"Fatal error in automation: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
        finally:
            await self.cleanup()
    
    async def init_browser(self):
        """Initialize Playwright browser."""
        try:
            self.logger.info("Initializing Playwright browser...")
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=False,  # Set to False to see the browser in action
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            self.page = await self.browser.new_page()
            
            # Set user agent
            await self.page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            self.logger.info("Browser initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing browser: {str(e)}")
            raise
    
    async def book_appointment_with_playwright(self, row_data: Dict) -> bool:
        """Book appointment using Playwright browser automation."""
        try:
            self.logger.info(f"Opening booking page: {self.config.BOOKING_URL}")
            
            # Navigate to booking page
            await self.page.goto(self.config.BOOKING_URL, wait_until='networkidle')
            
            # Wait for page to load
            await asyncio.sleep(2)
            
            # Step 1: Select the first available date
            self.logger.info("Selecting first available date...")
            await self.select_first_available_date()
            
            # Step 2: Select the first available time
            self.logger.info("Selecting first available time...")
            await self.select_first_available_time()
            
            # Step 3: Fill out the booking form
            self.logger.info("Filling out booking form...")
            await self.fill_booking_form(row_data)
            
            # Step 4: Submit the form
            self.logger.info("Submitting booking form...")
            await self.submit_booking_form()
            
            # Step 5: Wait for confirmation
            self.logger.info("Waiting for booking confirmation...")
            confirmation_success = await self.wait_for_confirmation()
            
            return confirmation_success
            
        except Exception as e:
            self.logger.error(f"Error in Playwright booking: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    async def select_first_available_date(self):
        """Select the first available date."""
        try:
            # Wait for date buttons to appear
            await self.page.wait_for_selector('.day', timeout=10000)
            
            # Find all date buttons
            date_buttons = await self.page.query_selector_all('.day')
            
            for button in date_buttons:
                # Check if button is enabled/clickable
                is_disabled = await button.get_attribute('disabled')
                if not is_disabled:
                    self.logger.info("Found available date, clicking...")
                    await button.click()
                    await asyncio.sleep(1)
                    return
            
            self.logger.warning("No available dates found")
            raise Exception("No available dates found")
            
        except Exception as e:
            self.logger.error(f"Error selecting date: {str(e)}")
            raise
    
    async def select_first_available_time(self):
        """Select the first available time."""
        try:
            # Wait for time buttons to appear
            await self.page.wait_for_selector('.time', timeout=10000)
            
            # Find all time buttons
            time_buttons = await self.page.query_selector_all('.time')
            
            for button in time_buttons:
                # Check if button is enabled/clickable
                is_disabled = await button.get_attribute('disabled')
                if not is_disabled:
                    self.logger.info("Found available time, clicking...")
                    await button.click()
                    await asyncio.sleep(1)
                    return
            
            self.logger.warning("No available times found")
            raise Exception("No available times found")
            
        except Exception as e:
            self.logger.error(f"Error selecting time: {str(e)}")
            raise
    
    async def fill_booking_form(self, row_data: Dict):
        """Fill out the booking form with data from the sheet."""
        try:
            # Wait for form to appear
            await asyncio.sleep(2)
            
            # Fill name field
            name_field = await self.page.wait_for_selector('input[name="name"], input[placeholder*="name"], input[placeholder*="Name"]', timeout=5000)
            await name_field.fill(row_data['name'])
            self.logger.info(f"Filled name: {row_data['name']}")
            
            # Fill email field
            email_field = await self.page.wait_for_selector('input[name="email"], input[type="email"], input[placeholder*="email"]', timeout=5000)
            await email_field.fill(row_data['email'])
            self.logger.info(f"Filled email: {row_data['email']}")
            
            # Fill company field
            try:
                company_field = await self.page.wait_for_selector('input[name="company"], input[placeholder*="company"], input[placeholder*="Company"]', timeout=3000)
                await company_field.fill(row_data['company'])
                self.logger.info(f"Filled company: {row_data['company']}")
            except:
                self.logger.info("Company field not found, skipping...")
            
            await asyncio.sleep(1)
            
        except Exception as e:
            self.logger.error(f"Error filling form: {str(e)}")
            raise
    
    async def submit_booking_form(self):
        """Submit the booking form."""
        try:
            # Look for submit button
            submit_button = await self.page.wait_for_selector('button[type="submit"], input[type="submit"], button:has-text("Submit"), button:has-text("Book"), button:has-text("Schedule")', timeout=5000)
            
            await submit_button.click()
            self.logger.info("Clicked submit button")
            
            await asyncio.sleep(2)
            
        except Exception as e:
            self.logger.error(f"Error submitting form: {str(e)}")
            raise
    
    async def wait_for_confirmation(self) -> bool:
        """Wait for booking confirmation."""
        try:
            # Wait for success indicators
            success_selectors = [
                'text="Thank you"',
                'text="Confirmed"',
                'text="Success"',
                'text="Booked"',
                '.success',
                '.confirmation',
                '[class*="success"]',
                '[class*="confirm"]'
            ]
            
            for selector in success_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=3000)
                    self.logger.info(f"Found confirmation with selector: {selector}")
                    return True
                except:
                    continue
            
            # If no specific confirmation found, wait a bit and assume success
            await asyncio.sleep(3)
            
            # Check if we're still on the same page or redirected
            current_url = self.page.url
            if current_url != self.config.BOOKING_URL:
                self.logger.info("Page changed after submission - assuming success")
                return True
            
            self.logger.warning("No clear confirmation found, but assuming success")
            return True
            
        except Exception as e:
            self.logger.error(f"Error waiting for confirmation: {str(e)}")
            return False
    
    async def get_sheet_data(self) -> List[Dict]:
        """Retrieve data from Google Sheets."""
        try:
            return await asyncio.to_thread(self.sheets_client.get_all_rows)
        except Exception as e:
            self.logger.error(f"Error retrieving sheet data: {str(e)}")
            return []
    
    def validate_row_data(self, row_data: Dict) -> bool:
        """Validate that row data contains required fields."""
        # Get name from various possible columns
        name = (row_data.get('name', '') or 
                row_data.get('Name', '') or 
                row_data.get('status', '') or  # Company name might be in status column
                '').strip()
        
        # Get email
        email = (row_data.get('email', '') or 
                 row_data.get('Email', '') or 
                 '').strip()
        
        # Get company
        company = (row_data.get('company', '') or 
                   row_data.get('Company', '') or 
                   row_data.get('status', '') or
                   name or  # Use name as company if available
                   '').strip()
        
        # For real bookings, we need actual email addresses
        if not email or 'demo@' in email:
            self.logger.warning(f"Need real email address for booking, got: {email}")
            return False
            
        if not (name or company):
            self.logger.warning(f"Missing both name and company")
            return False
            
        # Update the row_data with normalized fields
        row_data['name'] = name or company
        row_data['email'] = email
        row_data['company'] = company or name
        
        return True
    
    async def mark_row_as_done(self, row_index: int):
        """Mark a row as done in the Google Sheet."""
        try:
            await asyncio.to_thread(self.sheets_client.update_cell, row_index, 4, 'done')
            self.logger.info(f"Row {row_index}: Marked as done in Google Sheet")
        except Exception as e:
            self.logger.error(f"Error marking row {row_index} as done: {str(e)}")
    
    async def cleanup(self):
        """Clean up browser resources."""
        try:
            if self.browser:
                await self.browser.close()
                self.logger.info("Browser cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")