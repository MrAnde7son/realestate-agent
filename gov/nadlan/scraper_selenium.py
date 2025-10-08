# -*- coding: utf-8 -*-
"""
nadlan/scraper.py
-----------------

Simple scraper for retrieving real-estate transaction history from nadlan.gov.il.

This module provides a focused interface using Selenium to interact with the real website
and capture actual data, bypassing authentication issues.

Usage
::::::

    from gov.nadlan import NadlanDealsScraper
    scraper = NadlanDealsScraper()
    deals = scraper.get_deals_by_neighborhood_id("65210036")
    for deal in deals:
        print(f"{deal.address} - ₪{deal.deal_amount:,.0f}")

Notes
:::::

* This implementation uses Selenium to interact with the real website
* No authentication tokens are required - it uses the same browser session as the website
* The API is robust and handles various response formats automatically
* Please be courteous and avoid rapid repeated calls to respect the service
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

from .exceptions import NadlanAPIError
from .models import Deal

logger = logging.getLogger(__name__)


class NadlanDealsScraper:
    """Simple scraper for real estate deals from nadlan.gov.il."""
    
    def __init__(self, timeout: float = 30.0, headless: bool = True):
        """Initialize the scraper.
        
        Args:
            timeout: Request timeout in seconds
            headless: Whether to run browser in headless mode
        """
        self.timeout = timeout
        self.headless = headless
        self.driver = None
    
    def _init_driver(self):
        """Initialize the Selenium WebDriver."""
        if self.driver is None:
            service = Service(ChromeDriverManager().install())
            options = webdriver.ChromeOptions()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1280,720')
            options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
            
            # Enable logging for better debugging
            options.add_argument('--enable-logging')
            options.add_argument('--log-level=0')
            
            # Disable images and CSS for faster loading (optional)
            # prefs = {"profile.managed_default_content_settings.images": 2}
            # options.add_experimental_option("prefs", prefs)
            
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(self.timeout)
            
            # Enable network logging
            self.driver.execute_cdp_cmd('Network.enable', {})
            self.driver.execute_cdp_cmd('Runtime.enable', {})
    
    def _wait_for_deals_api_call(self, timeout: int = 30) -> bool:
        """Wait for the deals API call to complete by monitoring network requests."""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Get network logs
                logs = self.driver.get_log('performance')
                
                for log in logs:
                    message = log.get('message', {})
                    if isinstance(message, str):
                        try:
                            message = json.loads(message)
                        except (json.JSONDecodeError, TypeError):
                            continue
                    
                    method = message.get('method', '')
                    
                    # Check for completed API calls
                    if method == 'Network.responseReceived':
                        response = message.get('params', {}).get('response', {})
                        url = response.get('url', '')
                        
                        # Look for deals API endpoints
                        if any(endpoint in url for endpoint in ['/api/deal', '/deal', 'deals']):
                            status = response.get('status', 0)
                            if status == 200:
                                logger.info(f"Deals API call completed successfully: {url}")
                                return True
                            elif status >= 400:
                                logger.warning(f"Deals API call failed with status {status}: {url}")
                                return False
                    
                    # Check for failed requests
                    elif method == 'Network.loadingFailed':
                        error = message.get('params', {}).get('errorText', '')
                        url = message.get('params', {}).get('requestId', '')
                        logger.warning(f"Network request failed: {error}")
                
                time.sleep(1)
                
            except Exception as e:
                logger.debug(f"Error monitoring network requests: {e}")
                time.sleep(1)
        
        logger.warning("Timeout waiting for deals API call")
        return False
    
    def _check_for_error_modal(self) -> bool:
        """Check if an error modal is currently displayed."""
        try:
            # Try multiple selectors for error modals
            error_selectors = [
                ".modal.show",
                ".error-modal", 
                "[class*='error']",
                "[class*='modal'][style*='display: block']",
                ".modal[style*='display: block']",
                ".modal.show[style*='display: block']",
                "[role='dialog'][class*='modal']",
                ".fade.contanctModal.centerModal.smModal.titleContainer.modal.show"
            ]
            
            for selector in error_selectors:
                try:
                    error_modals = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for modal in error_modals:
                        if modal.is_displayed():
                            error_text = modal.text.strip()
                            if any(keyword in error_text for keyword in ['שגיאה', 'error', 'Error', 'טעינת נתונים']):
                                logger.error(f"Error modal detected: {error_text}")
                                return True
                except Exception:
                    continue
            return False
        except Exception as e:
            logger.debug(f"Error during modal check: {e}")
            return False
    
    def _try_close_error_modal(self) -> bool:
        """Try to close the error modal and return True if successful."""
        try:
            # Try different close button selectors
            close_selectors = [
                ".closeModalBtnContainer",
                ".closeModalBtn",
                ".modal .close",
                ".modal .btn-close",
                "[aria-label='Close']",
                "[title='Close']",
                ".modal-header .close",
                "button[class*='close']"
            ]
            
            for selector in close_selectors:
                try:
                    close_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in close_buttons:
                        if button.is_displayed():
                            logger.info(f"Found close button with selector: {selector}")
                            button.click()
                            time.sleep(1)  # Wait for modal to close
                            
                            # Check if modal is still visible
                            if not self._check_for_error_modal():
                                logger.info("Error modal successfully closed")
                                return True
                except Exception as e:
                    logger.debug(f"Error clicking close button with selector '{selector}': {e}")
                    continue
            
            # Try pressing Escape key
            try:
                from selenium.webdriver.common.keys import Keys
                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                time.sleep(1)
                if not self._check_for_error_modal():
                    logger.info("Error modal closed with Escape key")
                    return True
            except Exception as e:
                logger.debug(f"Error pressing Escape key: {e}")
            
            return False
        except Exception as e:
            logger.debug(f"Error during modal close attempt: {e}")
            return False
    
    def _wait_for_page_load(self):
        """Wait for the page to load completely and check for errors."""
        try:
            # Wait for basic page load
            time.sleep(3)
            
            # Wait for JavaScript to finish loading
            self.driver.execute_script("return document.readyState") == "complete"
            
            # Wait a bit more for dynamic content
            time.sleep(2)
            
            # Check if there are any loading indicators
            loading_selectors = [
                "[class*='loading']",
                "[class*='spinner']", 
                ".loading",
                ".spinner"
            ]
            
            for selector in loading_selectors:
                try:
                    loading_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in loading_elements:
                        if element.is_displayed():
                            logger.info("Waiting for loading indicator to disappear...")
                            time.sleep(2)
                            break
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"Error during page load wait: {e}")
    
    def _cleanup_driver(self):
        """Clean up the Selenium WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            finally:
                self.driver = None
    
    def __enter__(self):
        """Context manager entry."""
        self._init_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._cleanup_driver()
    
    def get_neighborhood_info(self, neighbourhood_id: str) -> Dict[str, Any]:
        """Get information about a neighborhood.

        Args:
            neighbourhood_id: The numeric neighborhood ID

        Returns:
            Dictionary with neighborhood information

        Raises:
            NadlanAPIError: If the API call fails
        """
        logger.info("Getting neighborhood info for %s", neighbourhood_id)
        try:
            self._init_driver()
            info = self._get_neighborhood_info_selenium(neighbourhood_id)
            logger.info("Retrieved neighborhood info for %s", neighbourhood_id)
            return info
        except Exception as e:
            logger.exception("Failed to get neighborhood info for %s", neighbourhood_id)
            raise NadlanAPIError(f"Failed to get neighborhood info for {neighbourhood_id}: {e}")
        finally:
            self._cleanup_driver()

    def _extract_deals_from_table(self) -> List[Deal]:
        """Extract deals from all tables on the page."""
        deals = []
        
        try:
            # Find all tables that might contain deals
            tables = self.driver.find_elements(By.CSS_SELECTOR, "table#dealsTable, .mainTable, table")
            
            for table_idx, main_table in enumerate(tables):
                logger.info(f"Processing table {table_idx + 1}")
                
                # Extract from the main table structure
                rows = main_table.find_elements(By.CSS_SELECTOR, "tbody tr")
                
                if len(rows) == 0:
                    logger.info(f"Table {table_idx + 1} has no data rows")
                    continue
                
                logger.info(f"Table {table_idx + 1} has {len(rows)} data rows")
                
                for row in rows:
                    try:
                        cells = row.find_elements(By.CSS_SELECTOR, "td")
                        if len(cells) >= 5:  # Should have at least 5 columns
                            cell_texts = [cell.text.strip() for cell in cells]
                            
                            # Skip header rows
                            if any(keyword in ' '.join(cell_texts).lower() for keyword in 
                                   ['מספר סידורי', 'כתובת', 'header']):
                                continue
                            
                            # Extract deal information based on table structure
                            deal_data = {
                                'serial_number': cell_texts[0] if len(cell_texts) > 0 else '',
                                'address': cell_texts[1] if len(cell_texts) > 1 else '',
                                'area': cell_texts[2] if len(cell_texts) > 2 else '',
                                'deal_date': cell_texts[3] if len(cell_texts) > 3 else '',
                                'deal_amount': cell_texts[4] if len(cell_texts) > 4 else '',
                                'parcelNum': cell_texts[5] if len(cell_texts) > 5 else '',
                                'asset_type': cell_texts[6] if len(cell_texts) > 6 else '',
                                'rooms': cell_texts[7] if len(cell_texts) > 7 else '',
                                'floor': cell_texts[8] if len(cell_texts) > 8 else '',
                                'trend': cell_texts[9] if len(cell_texts) > 9 else ''
                            }
                            
                            # Only process if we have essential data
                            if deal_data['address'] and deal_data['deal_amount']:
                                try:
                                    deal = Deal.from_item(deal_data)
                                    deals.append(deal)
                                except Exception as e:
                                    logger.debug(f"Error creating Deal object: {e}")
                                    # Create a basic deal object
                                    deals.append(Deal(
                                        address=deal_data.get('address', ''),
                                        deal_amount=deal_data.get('deal_amount', ''),
                                        deal_date=deal_data.get('deal_date', ''),
                                        rooms=deal_data.get('rooms', ''),
                                        area=deal_data.get('area', ''),
                                        parcel_block=deal_data.get('parcelNum', '').split('-')[0] if deal_data.get('parcelNum') else '',
                                        parcel_parcel=deal_data.get('parcelNum', '').split('-')[1] if deal_data.get('parcelNum') and '-' in deal_data.get('parcelNum', '') else '',
                                        parcel_sub_parcel=deal_data.get('parcelNum', '').split('-')[2] if deal_data.get('parcelNum') and deal_data.get('parcelNum', '').count('-') >= 2 else '',
                                        asset_type=deal_data.get('asset_type', '')
                                    ))
                                    
                    except Exception as e:
                        logger.debug(f"Error processing table row: {e}")
                        continue
                
                logger.info(f"Extracted {len([d for d in deals if d])} deals from table {table_idx + 1}")
                        
        except Exception as e:
            logger.debug(f"Error extracting deals from tables: {e}")
            
        logger.info(f"Total extracted {len(deals)} deals from all tables")
        return deals

    def get_deals_by_address(self, address: str) -> List[Deal]:
        """Retrieve deals using a specific address.

        Args:
            address: The address to search for (e.g., "רוזוב 4 תל אביב")

        Returns:
            List of Deal objects

        Raises:
            NadlanAPIError: If the API call fails
        """
        logger.info("Fetching deals for address %s", address)
        try:
            self._init_driver()
            return self._fetch_deals_by_address_selenium(address)
        except Exception as e:
            logger.error(f"Error fetching deals for address {address}: {e}")
            raise NadlanAPIError(f"Failed to fetch deals for address {address}: {e}")
    
    def _fetch_deals_by_address_selenium(self, address: str) -> List[Deal]:
        """Fetch deals by address using Selenium with search-based navigation."""
        try:
            # First, try to navigate to deals page using search
            if self._navigate_to_deals_via_search(address):
                # Wait for page to load completely and check for errors
                self._wait_for_page_load()
                
                # Check for error modal first
                error_modal_found = False
                try:
                    # Try multiple selectors for error modals
                    error_selectors = [
                        ".modal.show",
                        ".error-modal", 
                        "[class*='error']",
                        "[class*='modal'][style*='display: block']",
                        ".modal[style*='display: block']",
                        ".modal.show[style*='display: block']",
                        "[role='dialog'][class*='modal']",
                        ".fade.contanctModal.centerModal.smModal.titleContainer.modal.show"
                    ]
                    
                    for selector in error_selectors:
                        try:
                            error_modals = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for modal in error_modals:
                                if modal.is_displayed():
                                    error_text = modal.text.strip()
                                    if any(keyword in error_text for keyword in ['שגיאה', 'error', 'Error', 'טעינת נתונים']):
                                        logger.error(f"Error modal detected with selector '{selector}': {error_text}")
                                        error_modal_found = True
                                        break
                            if error_modal_found:
                                break
                        except Exception as e:
                            logger.debug(f"Error checking selector '{selector}': {e}")
                            continue
                    
                    if error_modal_found:
                        # Take a screenshot for debugging
                        try:
                            screenshot_path = f"error_modal_{address.replace(' ', '_')}_{int(time.time())}.png"
                            self.driver.save_screenshot(screenshot_path)
                            logger.info(f"Screenshot saved: {screenshot_path}")
                        except Exception as e:
                            logger.debug(f"Could not save screenshot: {e}")
                        
                        # Try to close the error modal and continue
                        if self._try_close_error_modal():
                            logger.info("Error modal closed, continuing with data extraction...")
                        else:
                            raise NadlanAPIError("Website showed error modal: שגיאה בטעינת הנתונים")
                            
                except NadlanAPIError:
                    raise
                except Exception as e:
                    logger.debug(f"Error during modal detection: {e}")
                    pass  # Continue if we can't detect modals
                
                # Wait for deals API call to complete
                logger.info("Waiting for deals API call to complete...")
                api_success = self._wait_for_deals_api_call(timeout=20)
                if not api_success:
                    logger.warning("Deals API call may have failed, continuing with data extraction...")
                
                # Wait for the deals table or data to load
                max_wait_time = 30  # Maximum wait time in seconds
                wait_interval = 1   # Check every 1 second
                waited_time = 0
                
                deals = []
                
                # First, get deals from the current page
                deals = self._extract_deals_from_current_page()
                
                # Then, check for pagination and get deals from all pages
                if deals:
                    deals.extend(self._extract_deals_from_all_pages())
                
                return deals
            else:
                logger.error("Failed to navigate to deals page via search")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching deals for address {address}: {e}")
            raise NadlanAPIError(f"Failed to fetch deals for address {address}: {e}")
    
    def _navigate_to_deals_via_search(self, search_term: str) -> bool:
        """Navigate to deals page using the search functionality."""
        try:
            # Navigate to the main page
            logger.info("Navigating to main page...")
            self.driver.get("https://www.nadlan.gov.il/")
            time.sleep(3)
            
            # Find the search input with multiple selectors
            search_input = None
            selectors = [
                "#myInput2",
                ".react-autosuggest__input", 
                "input[placeholder*='הקלד כתובת']",
                "input[placeholder*='כתובת']",
                "input[type='text']",
                ".searchRow input",
                ".autosuggestContainer input"
            ]
            
            for selector in selectors:
                try:
                    search_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if search_input and search_input.is_displayed():
                        logger.info(f"Found search input with selector: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Selector '{selector}' failed: {e}")
                    continue
            
            if not search_input:
                logger.error("Could not find search input with any selector")
                return False
            
            # Use the provided search term directly
            logger.info(f"Searching for: {search_term}")
            
            # Use JavaScript to interact with the input to avoid click interception
            logger.info("Using JavaScript to interact with search input")
            
            # Focus the input using JavaScript
            self.driver.execute_script("arguments[0].focus();", search_input)
            time.sleep(1)
            
            # Clear and set the value using JavaScript
            self.driver.execute_script("arguments[0].value = '';", search_input)
            self.driver.execute_script("arguments[0].value = arguments[1];", search_input, search_term)
            
            # Trigger input events to make the autocomplete work
            self.driver.execute_script("""
                var input = arguments[0];
                var event = new Event('input', { bubbles: true });
                input.dispatchEvent(event);
                var changeEvent = new Event('change', { bubbles: true });
                input.dispatchEvent(changeEvent);
            """, search_input)
            
            time.sleep(3)  # Wait longer for autocomplete
            
            # Look for autocomplete suggestions
            suggestions = self.driver.find_elements(By.CSS_SELECTOR, 
                ".react-autosuggest__suggestions-list li, .autosuggest-item, [role='option'], .react-autosuggest__suggestion")
            
            if suggestions:
                logger.info(f"Found {len(suggestions)} suggestions for '{search_term}'")
                
                # Try to find an address-related suggestion
                address_suggestion = None
                for suggestion in suggestions:
                    suggestion_text = suggestion.text.strip()
                    if any(keyword in suggestion_text.lower() for keyword in ['רחוב', 'street', 'כתובת', 'address']):
                        address_suggestion = suggestion
                        break
                
                # Use address suggestion if found, otherwise use first suggestion
                target_suggestion = address_suggestion or suggestions[0]
                logger.info(f"Clicking suggestion: {target_suggestion.text.strip()}")
                
                target_suggestion.click()
                time.sleep(3)  # Wait for navigation
                
                # Check if we're on an address page
                current_url = self.driver.current_url
                logger.info(f"Current URL after search: {current_url}")
                
                if 'address' in current_url:
                    deals_url = current_url.replace('&page=deals', '') + '&page=deals'
                    logger.info(f"Navigating to deals page: {deals_url}")
                    self.driver.get(deals_url)
                    time.sleep(3)
                    return True
                elif 'neighborhood' in current_url:
                    deals_url = current_url.replace('&page=deals', '') + '&page=deals'
                    logger.info(f"Navigating to deals page: {deals_url}")
                    self.driver.get(deals_url)
                    time.sleep(3)
                    return True
                else:
                    logger.warning(f"Search '{search_term}' did not lead to address or neighborhood page")
                    return False
            else:
                logger.warning(f"No autocomplete suggestions found for '{search_term}'")
                # Try pressing Enter to search
                search_input.send_keys(Keys.RETURN)
                time.sleep(3)
                
                # Check if we're on an address or neighborhood page
                current_url = self.driver.current_url
                if 'address' in current_url or 'neighborhood' in current_url:
                    deals_url = current_url.replace('&page=deals', '') + '&page=deals'
                    logger.info(f"Navigating to deals page: {deals_url}")
                    self.driver.get(deals_url)
                    time.sleep(3)
                    return True
                else:
                    logger.warning("Search did not lead to address or neighborhood page")
                    return False
                    
        except Exception as e:
            logger.error(f"Error during search navigation: {e}")
            return False
    
    def _navigate_to_deals_direct_url(self, neighbourhood_id: str) -> bool:
        """Fallback: Navigate directly to deals page using URL."""
        try:
            url = f"https://www.nadlan.gov.il/?view=neighborhood&id={neighbourhood_id}&page=deals"
            logger.info(f"Navigating directly to: {url}")
            self.driver.get(url)
            time.sleep(3)
            return True
        except Exception as e:
            logger.error(f"Error with direct URL navigation: {e}")
            return False
    
    def _extract_deals_from_current_page(self) -> List[Deal]:
        """Extract deals from the current page."""
        max_wait_time = 30  # Maximum wait time in seconds
        wait_interval = 1   # Check every 1 second
        waited_time = 0
        
        while waited_time < max_wait_time:
            try:
                # Check for error modal again during the wait
                if self._check_for_error_modal():
                    raise NadlanAPIError("Error modal appeared during data loading: שגיאה בטעינת הנתונים")
                
                # Check if deals table has loaded with data
                table_rows = self.driver.find_elements(By.CSS_SELECTOR, 
                    "tbody tr, .deal-row, [class*='deal'], [class*='transaction']")
                
                # Check if we have actual data rows (not just headers)
                if len(table_rows) > 0:
                    # Look for deals data in various possible locations
                    deals_data = self.driver.execute_script("""
                        // Look for deals data in various possible locations
                        if (window.dealsData) return window.dealsData;
                        if (window.app && window.app.deals) return window.app.deals;
                        if (window.data && window.data.deals) return window.data.deals;
                        if (window.vue && window.vue.$data && window.vue.$data.deals) return window.vue.$data.deals;
                        
                        // Look for Vue.js data
                        if (window.vue && window.vue.$children) {
                            for (let child of window.vue.$children) {
                                if (child.deals) return child.deals;
                            }
                        }
                        
                        // Look for script tags with deals data
                        const scripts = document.querySelectorAll('script');
                        for (let script of scripts) {
                            const content = script.textContent || script.innerText;
                            if (content && content.includes('deals') && content.includes('[')) {
                                try {
                                    // Try different patterns
                                    const patterns = [
                                        /deals[^=]*=\\s*(\\[.*?\\])/,
                                        /"deals"\\s*:\\s*(\\[.*?\\])/,
                                        /deals\\s*:\\s*(\\[.*?\\])/,
                                        /data\\.deals\\s*=\\s*(\\[.*?\\])/
                                    ];
                                    
                                    for (let pattern of patterns) {
                                        const match = content.match(pattern);
                                        if (match) {
                                            return JSON.parse(match[1]);
                                        }
                                    }
                                } catch (e) {
                                    // Continue searching
                                }
                            }
                        }
                        return null;
                    """)
                    
                    if deals_data and isinstance(deals_data, list) and len(deals_data) > 0:
                        logger.info(f"Found deals data in page content: {len(deals_data)} items")
                        deals = [Deal.from_item(item) for item in deals_data]
                        break
                    
                    # Try to extract deals from table format
                    deals = self._extract_deals_from_table()
                    if deals:
                        logger.info(f"Extracted {len(deals)} deals from table")
                        break
                
                # Check if there's a "no deals found" message
                no_deals_msg = self.driver.find_elements(By.CSS_SELECTOR, 
                    "[class*='no-deals'], [class*='empty'], [class*='no-data'], .tableSummary")
                if no_deals_msg:
                    for msg in no_deals_msg:
                        if msg.is_displayed() and any(keyword in msg.text.lower() for keyword in 
                            ['לא נמצאו', 'no deals', 'empty', '0 עסקאות']):
                            logger.info("No deals found for this neighborhood")
                            return []
                
                # Wait a bit more
                time.sleep(wait_interval)
                waited_time += wait_interval
                
            except Exception as e:
                logger.warning(f"Error during data extraction attempt: {e}")
                time.sleep(wait_interval)
                waited_time += wait_interval
        
        if not deals:
            logger.warning("No deals data found after waiting %s seconds", max_wait_time)
            # Try one final attempt to extract from table
            deals = self._extract_deals_from_table()
        
        return deals
    
    def _extract_deals_from_all_pages(self) -> List[Deal]:
        """Extract deals from all pages using pagination."""
        all_deals = []
        
        try:
            # Get pagination info
            pagination_info = self._get_pagination_info()
            if not pagination_info:
                logger.info("No pagination found, only one page of deals")
                return []
            
            total_pages = pagination_info['total_pages']
            current_page = pagination_info['current_page']
            
            logger.info(f"Found pagination: {current_page} / {total_pages} pages")
            
            # Navigate through all remaining pages
            for page_num in range(current_page + 1, total_pages + 1):
                logger.info(f"Extracting deals from page {page_num}/{total_pages}")
                
                # Click next button or navigate to specific page
                if self._navigate_to_page(page_num):
                    # Wait for page to load
                    time.sleep(2)
                    
                    # Extract deals from current page
                    page_deals = self._extract_deals_from_table()
                    if page_deals:
                        logger.info(f"Found {len(page_deals)} deals on page {page_num}")
                        all_deals.extend(page_deals)
                    else:
                        logger.warning(f"No deals found on page {page_num}")
                else:
                    logger.warning(f"Failed to navigate to page {page_num}")
                    break
                    
        except Exception as e:
            logger.error(f"Error during pagination: {e}")
        
        logger.info(f"Total deals collected from all pages: {len(all_deals)}")
        return all_deals
    
    def _get_pagination_info(self) -> dict:
        """Get pagination information from the page."""
        try:
            # Look for pagination info in ALL table summaries
            pagination_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                ".tableSummary .pagination .paginate")
            
            logger.info(f"Found {len(pagination_elements)} pagination elements")
            
            # Collect all pagination info and choose the one with most pages
            pagination_options = []
            
            for i, element in enumerate(pagination_elements):
                text = element.text.strip()
                logger.info(f"Pagination element {i+1}: '{text}'")
                if '/' in text:
                    # Parse "1 / 52" format
                    parts = text.split('/')
                    if len(parts) == 2:
                        current_page = int(parts[0].strip())
                        total_pages = int(parts[1].strip())
                        logger.info(f"Found pagination option: {current_page} / {total_pages}")
                        pagination_options.append({
                            'current_page': current_page,
                            'total_pages': total_pages
                        })
            
            # Choose the pagination with the most pages (likely the neighborhood table)
            if pagination_options:
                best_option = max(pagination_options, key=lambda x: x['total_pages'])
                logger.info(f"Selected pagination with most pages: {best_option['current_page']} / {best_option['total_pages']}")
                return best_option
            
            # Alternative: look for next button to determine if pagination exists
            next_buttons = self.driver.find_elements(By.CSS_SELECTOR, "#next, .nextBtn")
            logger.info(f"Found {len(next_buttons)} next buttons")
            
            for i, next_button in enumerate(next_buttons):
                if next_button.is_displayed() and not next_button.get_attribute('disabled'):
                    logger.info(f"Next button {i+1} is enabled and visible")
                    # If there's a next button, assume we're on page 1 and there are more pages
                    return {
                        'current_page': 1,
                        'total_pages': 2  # Conservative estimate, will be updated as we navigate
                    }
                
        except Exception as e:
            logger.debug(f"Error getting pagination info: {e}")
        
        return None
    
    def _navigate_to_page(self, page_num: int) -> bool:
        """Navigate to a specific page number."""
        try:
            # Find all next buttons and try to click the one that's enabled
            next_buttons = self.driver.find_elements(By.CSS_SELECTOR, "#next, .nextBtn")
            logger.info(f"Found {len(next_buttons)} next buttons for page {page_num}")
            
            for i, next_button in enumerate(next_buttons):
                try:
                    if next_button.is_displayed() and not next_button.get_attribute('disabled'):
                        logger.info(f"Attempting to click next button {i+1} for page {page_num}")
                        
                        # Try regular click first
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                            time.sleep(0.5)
                            next_button.click()
                            time.sleep(3)  # Wait longer for page load
                            
                            # Check if pagination changed
                            new_pagination = self._get_pagination_info()
                            if new_pagination and new_pagination['current_page'] > 1:
                                logger.info(f"Regular click successful for button {i+1}, now on page {new_pagination['current_page']}")
                                return True
                            else:
                                logger.debug(f"Regular click didn't change page for button {i+1}")
                                
                        except Exception as click_error:
                            logger.debug(f"Regular click failed for button {i+1}: {click_error}")
                            
                            # Try JavaScript click as fallback
                            try:
                                self.driver.execute_script("arguments[0].click();", next_button)
                                time.sleep(3)  # Wait longer for page load
                                
                                # Check if pagination changed
                                new_pagination = self._get_pagination_info()
                                if new_pagination and new_pagination['current_page'] > 1:
                                    logger.info(f"JavaScript click successful for button {i+1}, now on page {new_pagination['current_page']}")
                                    return True
                                else:
                                    logger.debug(f"JavaScript click didn't change page for button {i+1}")
                                    
                            except Exception as js_error:
                                logger.debug(f"JavaScript click failed for button {i+1}: {js_error}")
                                continue
                                
                except Exception as e:
                    logger.debug(f"Error with next button {i+1}: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Error navigating to page {page_num}: {e}")
        
        return False

    def _get_neighborhood_info_selenium(self, neighbourhood_id: str) -> Dict[str, Any]:
        """Get neighborhood info using Selenium."""
        # Navigate to the neighborhood page
        url = f"https://www.nadlan.gov.il/?view=neighborhood&id={neighbourhood_id}"
        logger.info(f"Navigating to: {url}")
        
        self.driver.get(url)
        
        # Wait for page to load
        time.sleep(5)
        
        # Extract neighborhood information from the page
        info = {}
        
        try:
            # Look for neighborhood name
            name_element = self.driver.find_element(By.CSS_SELECTOR, "h1, .neighborhood-name, .title")
            info['neigh_name'] = name_element.text.strip()
        except Exception:
            info['neigh_name'] = f"Neighborhood {neighbourhood_id}"
        
        try:
            # Look for other neighborhood details
            details = self.driver.find_elements(By.CSS_SELECTOR, ".neighborhood-details, .info, .details")
            for detail in details:
                text = detail.text.strip()
                if ':' in text:
                    key, value = text.split(':', 1)
                    info[key.strip()] = value.strip()
        except Exception:
            pass
        
        return info

if __name__ == "__main__":
    scraper = NadlanDealsScraper(headless=False)
    deals = scraper.get_deals_by_address("רוזוב 14 תל אביב")
    for deal in deals:
        print(f"{deal.address} - ₪{deal.deal_amount:,.0f}")