"""
Google Sheets client for reading and updating spreadsheet data.
"""

import os
import gspread
import requests
import csv
import io
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict, Optional
from logger_config import setup_logger
from config import Config

class GoogleSheetsClient:
    """Handles Google Sheets operations."""
    
    def __init__(self, config=None):
        self.logger = setup_logger('sheets')
        self.config = config or Config()
        self.client = None
        self.worksheet = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Google Sheets client."""
        try:
            # Define the scope
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Get credentials
            creds_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
            if creds_json:
                # If credentials are provided as JSON string
                import json
                creds_dict = json.loads(creds_json)
                creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            else:
                # Fallback to service account file if available
                creds_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json')
                if os.path.exists(creds_file):
                    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
                else:
                    # For public sheets, try without authentication
                    self.logger.info("No credentials found, will attempt to access public sheet via CSV export")
                    self.client = None
                    self._open_worksheet()
                    return
            
            # Authorize and create client
            self.client = gspread.authorize(creds)
            self._open_worksheet()
            
            self.logger.info("Google Sheets client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing Google Sheets client: {str(e)}")
            raise
    
    def _open_worksheet(self):
        """Open the specified worksheet."""
        try:
            sheet_url = self.config.GOOGLE_SHEET_URL
            if not sheet_url:
                raise ValueError("Google Sheet URL not provided")
            
            # Extract sheet ID from URL
            if '/d/' in sheet_url:
                sheet_id = sheet_url.split('/d/')[1].split('/')[0]
            else:
                sheet_id = sheet_url
            
            if self.client:
                # Use authenticated client
                spreadsheet = self.client.open_by_key(sheet_id)
                self.worksheet = spreadsheet.sheet1
                self.logger.info(f"Opened worksheet: {spreadsheet.title}")
            else:
                # For public sheets, we'll use CSV export method
                self.sheet_id = sheet_id
                self.logger.info(f"Will access public sheet via CSV export: {sheet_id}")
            
        except Exception as e:
            self.logger.error(f"Error opening worksheet: {str(e)}")
            raise
    
    def get_all_rows(self) -> List[Dict]:
        """Get all rows from the worksheet."""
        try:
            if self.client and self.worksheet:
                # Use authenticated access
                records = self.worksheet.get_all_records()
                
                # Convert to our expected format
                formatted_records = []
                for record in records:
                    # Assuming columns are: Name (A), Email (B), Company (C), Status (D)
                    formatted_record = {
                        'name': str(record.get('Name', record.get('name', ''))).strip(),
                        'email': str(record.get('Email', record.get('email', ''))).strip(),
                        'company': str(record.get('Company', record.get('company', ''))).strip(),
                        'status': str(record.get('Status', record.get('status', ''))).strip()
                    }
                    formatted_records.append(formatted_record)
                
                self.logger.info(f"Retrieved {len(formatted_records)} rows from Google Sheet")
                return formatted_records
            
            elif hasattr(self, 'sheet_id'):
                # Use public CSV export method
                return self._get_public_sheet_data()
            
            else:
                raise Exception("Neither authenticated client nor sheet ID available")
            
        except Exception as e:
            self.logger.error(f"Error getting all rows: {str(e)}")
            return []
    
    def _get_public_sheet_data(self) -> List[Dict]:
        """Get data from public Google Sheet using CSV export."""
        try:
            # Try multiple CSV export URLs
            csv_urls = [
                f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/export?format=csv&gid=0",
                f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/export?format=csv",
                f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/gviz/tq?tqx=out:csv&sheet=Sheet1"
            ]
            
            response = None
            for csv_url in csv_urls:
                try:
                    self.logger.info(f"Trying CSV URL: {csv_url}")
                    response = requests.get(csv_url, timeout=30)
                    
                    # Check if response is valid CSV (not HTML error page)
                    if response.status_code == 200 and response.text and not response.text.strip().startswith('<!DOCTYPE'):
                        break
                    else:
                        self.logger.warning(f"Invalid response from {csv_url}: Status {response.status_code}")
                        
                except Exception as e:
                    self.logger.warning(f"Failed to access {csv_url}: {e}")
                    continue
            
            if not response or response.status_code != 200 or not response.text or response.text.strip().startswith('<!DOCTYPE'):
                raise Exception(f"""Unable to access your Google Sheet. Please check:
1. Sheet is set to 'Anyone with the link can view'
2. Share settings allow public access
3. URL is correct: {self.config.GOOGLE_SHEET_URL}

To fix: Go to your sheet → Share → Change to 'Anyone with the link can view'""")
            
            # Parse CSV data
            csv_data = csv.reader(io.StringIO(response.text))
            rows = list(csv_data)
            
            if not rows:
                self.logger.warning("No data found in public sheet")
                return []
            
            # Get headers (first row)
            headers = [header.strip() for header in rows[0]]
            self.logger.info(f"Found headers: {headers}")
            
            # Process data rows
            formatted_records = []
            for row in rows[1:]:  # Skip header row
                if len(row) < len(headers):
                    # Pad row with empty strings if necessary
                    row.extend([''] * (len(headers) - len(row)))
                
                # Create record dictionary
                record = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        record[header] = row[i].strip()
                    else:
                        record[header] = ''
                
                # Convert to our expected format
                formatted_record = {
                    'name': str(record.get('Name', record.get('name', ''))).strip(),
                    'email': str(record.get('Email', record.get('email', ''))).strip(),
                    'company': str(record.get('Company', record.get('company', ''))).strip(),
                    'status': str(record.get('Status', record.get('status', ''))).strip()
                }
                formatted_records.append(formatted_record)
            
            self.logger.info(f"Retrieved {len(formatted_records)} rows from public Google Sheet")
            return formatted_records
            
        except Exception as e:
            self.logger.error(f"Error accessing public sheet: {str(e)}")
            return []
    
    def update_cell(self, row_index: int, column_index: int, value: str):
        """Update a specific cell in the Google Sheet."""
        try:
            if self.client and self.worksheet:
                # Use authenticated access to update cell
                self.worksheet.update_cell(row_index, column_index, value)
                self.logger.info(f"Updated cell ({row_index}, {column_index}) to '{value}'")
            else:
                # For public sheets, we can't update cells
                self.logger.warning(f"Cannot update cell ({row_index}, {column_index}) - using public access mode")
                
        except Exception as e:
            self.logger.error(f"Error updating cell ({row_index}, {column_index}): {str(e)}")
            raise
    
    def update_cell(self, row: int, col: int, value: str):
        """Update a specific cell in the worksheet."""
        try:
            if self.client and self.worksheet:
                self.worksheet.update_cell(row, col, value)
                self.logger.info(f"Updated cell ({row}, {col}) with value: {value}")
            else:
                # For public sheets, we can't update - just log the attempt
                self.logger.warning(f"Cannot update cell ({row}, {col}) in public sheet. Would set to: {value}")
                self.logger.info("Note: Public Google Sheets are read-only. To update status, use a private sheet with credentials.")
            
        except Exception as e:
            self.logger.error(f"Error updating cell ({row}, {col}): {str(e)}")
            raise
    
    def get_row_data(self, row: int) -> Optional[Dict]:
        """Get data from a specific row."""
        try:
            if not self.worksheet:
                raise Exception("Worksheet not initialized")
            
            row_values = self.worksheet.row_values(row)
            
            if len(row_values) >= 4:
                return {
                    'name': row_values[0].strip() if len(row_values) > 0 else '',
                    'email': row_values[1].strip() if len(row_values) > 1 else '',
                    'company': row_values[2].strip() if len(row_values) > 2 else '',
                    'status': row_values[3].strip() if len(row_values) > 3 else ''
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting row {row} data: {str(e)}")
            return None
