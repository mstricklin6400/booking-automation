#!/usr/bin/env python3
"""
Test script to interact with the specific LeadConnector booking widget.
This will help debug and understand the widget structure.
"""

import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_booking_widget():
    """Test interaction with the LeadConnector booking widget."""
    
    booking_url = "https://api.leadconnectorhq.com/widget/booking/vggoBfO4Zr1RTp4M4h8m"
    
    async with async_playwright() as p:
        # Launch browser in visible mode for testing
        browser = await p.chromium.launch(
            headless=False,  # Make visible for debugging
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            logger.info(f"Loading booking widget: {booking_url}")
            await page.goto(booking_url, wait_until='networkidle', timeout=30000)
            
            # Wait for page to fully load
            await page.wait_for_timeout(5000)
            
            # Take screenshot for analysis
            await page.screenshot(path="booking_widget_initial.png", full_page=True)
            logger.info("Screenshot saved: booking_widget_initial.png")
            
            # Analyze page structure
            logger.info("Analyzing page structure...")
            
            # Get page title
            title = await page.title()
            logger.info(f"Page title: {title}")
            
            # Look for calendar elements
            calendar_selectors = [
                '.calendar',
                '[data-testid*="calendar"]',
                '[data-testid*="date"]',
                '.date-picker',
                '.booking-calendar',
                'button[data-date]',
                '[role="button"]'
            ]
            
            logger.info("Looking for calendar elements...")
            for selector in calendar_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        logger.info(f"Found {len(elements)} elements with selector: {selector}")
                        
                        # Get details of first few elements
                        for i, element in enumerate(elements[:3]):
                            is_visible = await element.is_visible()
                            is_enabled = await element.is_enabled()
                            text = await element.inner_text() if await element.is_visible() else "Not visible"
                            logger.info(f"  Element {i+1}: visible={is_visible}, enabled={is_enabled}, text='{text[:50]}'")
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
            
            # Look for form elements
            logger.info("Looking for form elements...")
            form_elements = await page.query_selector_all('input, textarea, select')
            logger.info(f"Found {len(form_elements)} form elements")
            
            for i, element in enumerate(form_elements):
                try:
                    element_type = await element.get_attribute('type') or 'text'
                    element_name = await element.get_attribute('name') or 'no-name'
                    element_placeholder = await element.get_attribute('placeholder') or 'no-placeholder'
                    is_visible = await element.is_visible()
                    logger.info(f"  Form element {i+1}: type={element_type}, name={element_name}, placeholder={element_placeholder}, visible={is_visible}")
                except Exception as e:
                    logger.debug(f"Error analyzing form element {i+1}: {e}")
            
            # Look for clickable buttons
            logger.info("Looking for clickable buttons...")
            buttons = await page.query_selector_all('button')
            logger.info(f"Found {len(buttons)} buttons")
            
            for i, button in enumerate(buttons[:10]):  # Limit to first 10
                try:
                    is_visible = await button.is_visible()
                    is_enabled = await button.is_enabled()
                    text = await button.inner_text() if is_visible else "Not visible"
                    aria_label = await button.get_attribute('aria-label') or ''
                    data_testid = await button.get_attribute('data-testid') or ''
                    logger.info(f"  Button {i+1}: text='{text[:30]}', aria-label='{aria_label}', data-testid='{data_testid}', visible={is_visible}, enabled={is_enabled}")
                except Exception as e:
                    logger.debug(f"Error analyzing button {i+1}: {e}")
            
            # Try to find and click first available date
            logger.info("Attempting to find available dates...")
            
            # More comprehensive date selectors
            date_selectors = [
                'button:not([disabled])[data-date]',
                'button:not([disabled])[aria-label*="Select"]',
                'button:not([disabled])[data-testid*="date"]',
                '.calendar-day:not(.disabled) button',
                '.available-date button',
                'button:not([disabled])[role="gridcell"]',
                'button:not([disabled])[tabindex]'
            ]
            
            date_found = False
            for selector in date_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    logger.info(f"Selector '{selector}': found {len(elements)} elements")
                    
                    for i, element in enumerate(elements[:5]):  # Check first 5
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()
                        if is_visible and is_enabled:
                            text = await element.inner_text()
                            logger.info(f"  Available date element {i+1}: '{text}' - CLICKABLE")
                            
                            if not date_found:
                                # Try clicking the first available date
                                logger.info(f"Attempting to click date: '{text}'")
                                await element.click()
                                await page.wait_for_timeout(2000)
                                
                                # Take screenshot after clicking date
                                await page.screenshot(path="booking_widget_after_date.png", full_page=True)
                                logger.info("Screenshot after date click: booking_widget_after_date.png")
                                
                                date_found = True
                                break
                        else:
                            text = await element.inner_text() if is_visible else "Not visible"
                            logger.info(f"  Date element {i+1}: '{text}' - NOT CLICKABLE (visible={is_visible}, enabled={is_enabled})")
                    
                    if date_found:
                        break
                        
                except Exception as e:
                    logger.debug(f"Date selector {selector} failed: {e}")
            
            if date_found:
                # Look for time slots after selecting date
                logger.info("Looking for time slots...")
                await page.wait_for_timeout(3000)
                
                time_selectors = [
                    'button:not([disabled])[data-time]',
                    'button:not([disabled])[aria-label*="time"]',
                    'button:not([disabled])[data-testid*="time"]',
                    '.time-slot:not(.disabled) button',
                    '.available-time button',
                    'button:not([disabled])[aria-label*="AM"]',
                    'button:not([disabled])[aria-label*="PM"]'
                ]
                
                time_found = False
                for selector in time_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        logger.info(f"Time selector '{selector}': found {len(elements)} elements")
                        
                        for i, element in enumerate(elements[:5]):
                            is_visible = await element.is_visible()
                            is_enabled = await element.is_enabled()
                            if is_visible and is_enabled:
                                text = await element.inner_text()
                                logger.info(f"  Available time element {i+1}: '{text}' - CLICKABLE")
                                
                                if not time_found:
                                    # Try clicking the first available time
                                    logger.info(f"Attempting to click time: '{text}'")
                                    await element.click()
                                    await page.wait_for_timeout(2000)
                                    
                                    # Take screenshot after clicking time
                                    await page.screenshot(path="booking_widget_after_time.png", full_page=True)
                                    logger.info("Screenshot after time click: booking_widget_after_time.png")
                                    
                                    time_found = True
                                    break
                            else:
                                text = await element.inner_text() if is_visible else "Not visible"
                                logger.info(f"  Time element {i+1}: '{text}' - NOT CLICKABLE")
                        
                        if time_found:
                            break
                            
                    except Exception as e:
                        logger.debug(f"Time selector {selector} failed: {e}")
                
                if time_found:
                    # Look for booking form after selecting time
                    logger.info("Looking for booking form...")
                    await page.wait_for_timeout(3000)
                    
                    # Take final screenshot
                    await page.screenshot(path="booking_widget_form.png", full_page=True)
                    logger.info("Final screenshot: booking_widget_form.png")
                    
                    # Analyze form fields that appeared
                    form_elements = await page.query_selector_all('input, textarea, select')
                    logger.info(f"Form now has {len(form_elements)} input elements")
                    
                    for i, element in enumerate(form_elements):
                        try:
                            element_type = await element.get_attribute('type') or 'text'
                            element_name = await element.get_attribute('name') or 'no-name'
                            element_placeholder = await element.get_attribute('placeholder') or 'no-placeholder'
                            is_visible = await element.is_visible()
                            is_required = await element.get_attribute('required') is not None
                            logger.info(f"  Form field {i+1}: type={element_type}, name={element_name}, placeholder={element_placeholder}, visible={is_visible}, required={is_required}")
                        except Exception as e:
                            logger.debug(f"Error analyzing form element: {e}")
            
            # Keep browser open for manual inspection
            logger.info("Test completed. Browser will stay open for 30 seconds for manual inspection...")
            await page.wait_for_timeout(30000)
            
        except Exception as e:
            logger.error(f"Error during test: {e}")
            await page.screenshot(path="booking_widget_error.png", full_page=True)
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_booking_widget())