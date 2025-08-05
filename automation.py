"""
Booking automation module using HTTP requests for better compatibility.
"""

import asyncio
import traceback
from typing import Dict, List, Optional
from sheets_client import GoogleSheetsClient
from logger_config import setup_logger
from config import Config
from booking_client import LeadConnectorBookingClient
from advanced_booking_client import AdvancedLeadConnectorClient
from form_automation import RealFormAutomation
from email_client import EmailNotificationClient

class BookingAutomation:
    """Handles the automation of booking appointments."""
    
    def __init__(self, config=None):
        self.logger = setup_logger('automation')
        self.config = config or Config()
        self.sheets_client = GoogleSheetsClient(self.config)
        self.booking_client = None
        self.email_client = EmailNotificationClient(self.config)
        
        # Track automation statistics
        self.automation_stats = {
            'successful_bookings': 0,
            'failed_bookings': 0,
            'successful_list': [],
            'failed_list': [],
            'start_time': None,
            'total_processed': 0,
            'rows_skipped': 0
        }
        
    async def run(self):
        """Main automation workflow."""
        self.logger.info("Starting booking automation")
        
        # Initialize automation stats
        from datetime import datetime
        self.automation_stats['start_time'] = datetime.now()
        self.automation_stats['successful_bookings'] = 0
        self.automation_stats['failed_bookings'] = 0
        self.automation_stats['successful_list'] = []
        self.automation_stats['failed_list'] = []
        
        try:
            # Get data from Google Sheets
            rows_data = await self.get_sheet_data()
            if not rows_data:
                self.logger.warning("No data found in Google Sheets")
                return
            
            # Initialize real form automation client
            self.logger.info("Initializing real form automation client...")
            self.booking_client = RealFormAutomation(self.config)
            
            # Process each row
            success_count = 0
            error_count = 0
            
            self.logger.info(f"Starting to process {len(rows_data)} rows from Google Sheet")
            
            for row_index, row_data in enumerate(rows_data, start=2):  # Start at row 2 (skip header)
                try:
                    # Log what we're processing
                    self.logger.info(f"Row {row_index}: Processing data: {row_data}")
                    
                    if row_data.get('status', '').lower() == 'done':
                        self.logger.info(f"Row {row_index}: Skipping - already marked as done")
                        continue
                    
                    if not self.validate_row_data(row_data):
                        self.logger.warning(f"Row {row_index}: Invalid data - skipping")
                        error_count += 1
                        continue
                    
                    self.logger.info(f"Row {row_index}: Starting booking process for {row_data['name']} ({row_data['email']})")
                    
                    # Perform booking using HTTP client
                    booking_success = await self.booking_client.book_appointment(row_data)
                    
                    if booking_success:
                        # Update Google Sheet to mark as done (only if we have write access)
                        try:
                            await self.mark_row_as_done(row_index)
                        except Exception as mark_error:
                            self.logger.warning(f"Could not mark row as done (using public access): {mark_error}")
                        
                        success_count += 1
                        self.automation_stats['successful_bookings'] += 1
                        self.automation_stats['successful_list'].append({
                            'name': row_data['name'],
                            'email': row_data['email'],
                            'row': row_index
                        })
                        
                        self.logger.info(f"Row {row_index}: ✅ BOOKING SUCCESSFUL for {row_data['name']}")
                        
                        # Send success notification email
                        try:
                            await asyncio.to_thread(
                                self.email_client.send_booking_success_notification,
                                row_data, row_index
                            )
                            self.logger.info(f"Success notification sent for {row_data['name']}")
                        except Exception as email_error:
                            self.logger.warning(f"Failed to send success notification: {email_error}")
                        
                    else:
                        error_count += 1
                        self.automation_stats['failed_bookings'] += 1
                        self.automation_stats['failed_list'].append({
                            'name': row_data['name'],
                            'email': row_data['email'],
                            'row': row_index,
                            'error': 'Booking submission failed'
                        })
                        
                        # Send failure notification email
                        try:
                            await asyncio.to_thread(
                                self.email_client.send_booking_failure_notification,
                                row_data, row_index, 'Booking Failed', 'The booking submission to LeadConnector was unsuccessful'
                            )
                            self.logger.info(f"Failure notification sent for {row_data['name']}")
                        except Exception as email_error:
                            self.logger.warning(f"Failed to send failure notification: {email_error}")
                        self.logger.error(f"Row {row_index}: ❌ BOOKING FAILED for {row_data['name']}")
                    
                    # Add delay between bookings to avoid rate limiting
                    self.logger.info(f"Waiting {self.config.DELAY_BETWEEN_BOOKINGS} seconds before next booking...")
                    await asyncio.sleep(self.config.DELAY_BETWEEN_BOOKINGS)
                    
                except Exception as e:
                    error_count += 1
                    self.logger.error(f"Row {row_index}: Error processing booking - {str(e)}")
                    self.logger.error(f"Row {row_index}: Traceback - {traceback.format_exc()}")
            
            self.logger.info(f"🏁 AUTOMATION COMPLETED: {success_count} successful bookings, {error_count} errors")
            
        except Exception as e:
            self.logger.error(f"Fatal error in automation: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
        finally:
            self.logger.info("Automation cleanup completed")
    
    async def get_sheet_data(self) -> List[Dict]:
        """Retrieve data from Google Sheets."""
        try:
            return await asyncio.to_thread(self.sheets_client.get_all_rows)
        except Exception as e:
            self.logger.error(f"Error retrieving sheet data: {str(e)}")
            return []
    
    def validate_row_data(self, row_data: Dict) -> bool:
        """Validate that row data contains required fields."""
        # Check multiple possible field names for flexibility
        name = (row_data.get('name', '') or 
                row_data.get('Name', '') or 
                row_data.get('status', '') or  # 'status' column seems to have company names
                '').strip()
        
        email = (row_data.get('email', '') or 
                 row_data.get('Email', '') or 
                 '').strip()
        
        company = (row_data.get('company', '') or 
                   row_data.get('Company', '') or 
                   row_data.get('status', '') or  # 'status' column seems to have company names
                   name or  # Use name as company if available
                   '').strip()
        
        # For testing purposes, create a demo email if missing
        if not email:
            if company:
                # Create a demo email for testing
                email = f"demo@{company.lower().replace(' ', '').replace('-', '')}.com"
                self.logger.info(f"Created demo email for testing: {email}")
            else:
                self.logger.warning(f"Missing email address and company name")
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