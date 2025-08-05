"""
Form automation that directly mimics browser form submission to LeadConnector.
This approach extracts the actual form structure and submits data exactly as a browser would.
"""

import requests
import json
import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
from logger_config import setup_logger
from typing import Dict, Optional, List

class RealFormAutomation:
    """Real form automation that submits to the actual LeadConnector booking form."""
    
    def __init__(self, config):
        self.config = config
        self.logger = setup_logger('form_automation')
        self.session = requests.Session()
        self.base_url = config.BOOKING_URL
        
        # Headers that exactly mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        self.form_action = None
        self.form_method = 'POST'
        self.form_fields = {}
        self.cookies = {}
        
    async def book_appointment(self, contact_data: Dict) -> bool:
        """Book appointment by extracting and submitting the real form."""
        try:
            self.logger.info(f"Starting real form automation for {contact_data['name']} ({contact_data['email']})")
            
            # Step 1: Load the booking page and extract form
            if not await self.extract_real_form():
                self.logger.error("Failed to extract real form")
                return False
            
            # Step 2: Submit form with contact data exactly as browser would
            booking_success = await self.submit_real_form(contact_data)
            
            if booking_success:
                self.logger.info(f"✅ Real form submission successful for {contact_data['name']}")
                return True
            else:
                self.logger.error(f"❌ Real form submission failed for {contact_data['name']}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in real form automation: {str(e)}")
            return False
    
    async def extract_real_form(self) -> bool:
        """Extract the actual form from the LeadConnector booking page."""
        try:
            self.logger.info("Loading booking page to extract real form...")
            
            # Get the booking page
            response = self.session.get(self.base_url)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to load booking page: {response.status_code}")
                return False
            
            # Store cookies
            self.cookies = response.cookies
            
            # Parse HTML to find forms
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for forms on the page
            forms = soup.find_all('form')
            
            if not forms:
                self.logger.warning("No forms found on page, looking for embedded JavaScript form handlers...")
                return await self.extract_js_form_handler(response.text)
            
            # Use the first form found
            form = forms[0]
            
            # Extract form attributes
            self.form_action = form.get('action', '')
            self.form_method = form.get('method', 'POST').upper()
            
            # If action is relative, make it absolute
            if self.form_action and not self.form_action.startswith('http'):
                self.form_action = urljoin(self.base_url, self.form_action)
            elif not self.form_action:
                self.form_action = self.base_url
            
            # Extract all form fields
            form_inputs = form.find_all(['input', 'select', 'textarea'])
            
            for input_elem in form_inputs:
                name = input_elem.get('name')
                if name:
                    input_type = input_elem.get('type', 'text')
                    value = input_elem.get('value', '')
                    
                    self.form_fields[name] = {
                        'type': input_type,
                        'value': value,
                        'required': input_elem.get('required') is not None
                    }
            
            self.logger.info(f"Extracted form: action={self.form_action}, method={self.form_method}, fields={len(self.form_fields)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error extracting real form: {str(e)}")
            return False
    
    async def extract_js_form_handler(self, html_content: str) -> bool:
        """Extract form handler from JavaScript if no HTML form is found."""
        try:
            self.logger.info("Extracting JavaScript form handler...")
            
            # Look for common patterns in booking widgets
            patterns = [
                r'action["\s]*:["\s]*["\']([^"\']+)["\']',
                r'url["\s]*:["\s]*["\']([^"\']+)["\']',
                r'endpoint["\s]*:["\s]*["\']([^"\']+)["\']',
                r'submitUrl["\s]*:["\s]*["\']([^"\']+)["\']'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    potential_action = matches[0]
                    if not potential_action.startswith('http'):
                        potential_action = urljoin(self.base_url, potential_action)
                    
                    self.form_action = potential_action
                    self.logger.info(f"Found JS form action: {self.form_action}")
                    
                    # Set default form fields for booking
                    self.form_fields = {
                        'name': {'type': 'text', 'value': '', 'required': True},
                        'email': {'type': 'email', 'value': '', 'required': True},
                        'company': {'type': 'text', 'value': '', 'required': False},
                        'phone': {'type': 'tel', 'value': '', 'required': False},
                        'message': {'type': 'textarea', 'value': '', 'required': False}
                    }
                    
                    return True
            
            # If no specific action found, try common booking endpoints
            self.form_action = f"{self.base_url}/submit"
            self.form_fields = {
                'name': {'type': 'text', 'value': '', 'required': True},
                'email': {'type': 'email', 'value': '', 'required': True},
                'company': {'type': 'text', 'value': '', 'required': False}
            }
            
            self.logger.info("Using fallback form configuration")
            return True
            
        except Exception as e:
            self.logger.error(f"Error extracting JS form handler: {str(e)}")
            return False
    
    async def submit_real_form(self, contact_data: Dict) -> bool:
        """Submit the form with real data exactly as a browser would."""
        try:
            self.logger.info("Preparing real form submission...")
            
            # Prepare form data
            form_data = {}
            
            # Fill in the extracted form fields with contact data
            for field_name, field_info in self.form_fields.items():
                if field_name.lower() in ['name', 'full_name', 'firstname', 'first_name']:
                    form_data[field_name] = contact_data['name']
                elif field_name.lower() in ['email', 'email_address']:
                    form_data[field_name] = contact_data['email']
                elif field_name.lower() in ['company', 'organization', 'business']:
                    form_data[field_name] = contact_data.get('company', '')
                elif field_name.lower() in ['phone', 'telephone', 'mobile']:
                    form_data[field_name] = contact_data.get('phone', '')
                elif field_name.lower() in ['message', 'comments', 'notes']:
                    form_data[field_name] = f"Booking request for {contact_data['name']}"
                elif field_info['type'] == 'hidden':
                    # Keep existing hidden field values
                    form_data[field_name] = field_info['value']
                else:
                    # For other fields, use existing value or empty string
                    form_data[field_name] = field_info['value']
            
            # Add common booking fields
            form_data.update({
                'service': 'consultation',
                'duration': '30',
                'timezone': 'America/New_York',
                'booking_type': 'appointment'
            })
            
            self.logger.info(f"Form data prepared: {list(form_data.keys())}")
            
            # Set proper headers for form submission
            submission_headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': urlparse(self.base_url).scheme + '://' + urlparse(self.base_url).netloc,
                'Referer': self.base_url,
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Try multiple submission methods
            submission_urls = [
                self.form_action,
                f"{self.base_url}/submit",
                f"{self.base_url}/book",
                f"{self.base_url}/appointment",
                self.base_url
            ]
            
            for url in submission_urls:
                try:
                    self.logger.info(f"Trying form submission to: {url}")
                    
                    # Try POST with form data
                    response = self.session.post(
                        url,
                        data=form_data,
                        headers=submission_headers,
                        cookies=self.cookies,
                        allow_redirects=True,
                        timeout=30
                    )
                    
                    self.logger.info(f"Form submission response: {response.status_code}")
                    
                    # Check if submission was successful
                    if self.is_submission_successful(response):
                        self.logger.info("Form submission appears successful!")
                        return True
                    
                    # Try JSON submission
                    json_headers = submission_headers.copy()
                    json_headers['Content-Type'] = 'application/json'
                    
                    json_response = self.session.post(
                        url,
                        json=form_data,
                        headers=json_headers,
                        cookies=self.cookies,
                        allow_redirects=True,
                        timeout=30
                    )
                    
                    if self.is_submission_successful(json_response):
                        self.logger.info("JSON form submission appears successful!")
                        return True
                        
                except Exception as e:
                    self.logger.debug(f"Submission to {url} failed: {str(e)}")
                    continue
            
            # If we get here, try a direct API approach
            return await self.try_direct_api_submission(contact_data)
            
        except Exception as e:
            self.logger.error(f"Error in real form submission: {str(e)}")
            return False
    
    def is_submission_successful(self, response) -> bool:
        """Check if form submission was successful."""
        try:
            # Success status codes
            if response.status_code in [200, 201, 302, 303]:
                
                # Check response content for success indicators
                content = response.text.lower()
                
                success_indicators = [
                    'success', 'thank you', 'confirmed', 'booked',
                    'appointment scheduled', 'booking confirmed',
                    'your appointment', 'confirmation', 'submitted',
                    'received', 'scheduled'
                ]
                
                error_indicators = [
                    'error', 'failed', 'invalid', 'required',
                    'missing', 'try again', 'problem'
                ]
                
                # If we find success indicators and no error indicators
                has_success = any(indicator in content for indicator in success_indicators)
                has_error = any(indicator in content for indicator in error_indicators)
                
                if has_success and not has_error:
                    return True
                
                # Check for redirect to success page
                if response.status_code in [302, 303]:
                    location = response.headers.get('location', '').lower()
                    if any(word in location for word in ['success', 'thank', 'confirm']):
                        return True
                
                # If no errors and good status code, assume success
                if not has_error and response.status_code in [200, 201]:
                    return True
            
            return False
            
        except Exception:
            return False
    
    async def try_direct_api_submission(self, contact_data: Dict) -> bool:
        """Try direct API submission as last resort."""
        try:
            self.logger.info("Trying direct API submission...")
            
            # Extract widget ID from URL
            widget_match = re.search(r'/booking/([^/?]+)', self.base_url)
            widget_id = widget_match.group(1) if widget_match else 'default'
            
            # Try common API patterns
            api_endpoints = [
                f"https://api.leadconnectorhq.com/booking/{widget_id}/submit",
                f"https://api.leadconnectorhq.com/widget/booking/{widget_id}/submit",
                f"https://api.leadconnectorhq.com/appointments",
                f"https://api.leadconnectorhq.com/bookings"
            ]
            
            api_data = {
                'name': contact_data['name'],
                'email': contact_data['email'],
                'company': contact_data.get('company', ''),
                'widgetId': widget_id,
                'service': 'consultation',
                'duration': 30
            }
            
            for endpoint in api_endpoints:
                try:
                    response = self.session.post(
                        endpoint,
                        json=api_data,
                        headers={
                            'Content-Type': 'application/json',
                            'Origin': 'https://api.leadconnectorhq.com',
                            'Referer': self.base_url
                        },
                        timeout=30
                    )
                    
                    if response.status_code in [200, 201]:
                        self.logger.info(f"Direct API submission successful to {endpoint}")
                        return True
                        
                except:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.error(f"Direct API submission failed: {str(e)}")
            return False