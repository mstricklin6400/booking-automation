"""
Main automation logic for booking appointments using Playwright and Google Sheets.
"""

import asyncio
import time
import traceback
from typing import List, Dict, Optional
from sheets_client import GoogleSheetsClient
from logger_config import setup_logger
from config import Config
from booking_client import LeadConnectorBookingClient

class BookingAutomation:
    """Handles the automation of booking appointments."""
    
    def __init__(self, config=None):
        self.logger = setup_logger('automation')
        self.config = config or Config()
        self.sheets_client = GoogleSheetsClient(self.config)
        self.booking_client = None
        
    async def run(self):
        """Main automation workflow."""
        self.logger.info("Starting booking automation")
        
        try:
            # Get data from Google Sheets
            rows_data = await self.get_sheet_data()
            if not rows_data:
                self.logger.warning("No data found in Google Sheets")
                return
            
            # Initialize booking client
            self.logger.info("Initializing HTTP-based booking client...")
            self.booking_client = LeadConnectorBookingClient(self.config)
            
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
                        self.logger.info(f"Row {row_index}: ✅ BOOKING SUCCESSFUL for {row_data['name']}")
                    else:
                        error_count += 1
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
        required_fields = ['name', 'email', 'company']
        for field in required_fields:
            if not row_data.get(field, '').strip():
                self.logger.warning(f"Missing or empty required field: {field}")
                return False
        return True
    

    
