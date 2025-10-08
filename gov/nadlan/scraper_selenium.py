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
    
    def get_deals_by_street_id(self, street_id: str) -> List[Deal]:
        """
        Fetch deals for a specific street ID.

        Args:
            street_id: The street ID from the search results

        Returns:
            List of Deal objects

        Raises:
            NadlanAPIError: If the fetch fails
        """
        logger.info("Fetching deals for street %s", street_id)
        try:
            self._init_driver()
            deals = self._fetch_deals_by_street_id_selenium(street_id)
            logger.info("Fetched %s deals for street %s", len(deals), street_id)
            return deals
        except Exception as e:
            logger.exception("Failed to fetch deals for street %s", street_id)
            raise NadlanAPIError(f"Failed to fetch deals for street {street_id}: {e}")
        finally:
            self._cleanup_driver()

    def get_deals_by_neighborhood_id(self, neighbourhood_id: str) -> List[Deal]:
        """Retrieve deals using a neighbourhood identifier.

        Args:
            neighbourhood_id: The numeric ID as seen in the URL

        Returns:
            List of Deal objects

        Raises:
            NadlanAPIError: If the API call fails
        """
        logger.info("Fetching deals for neighborhood %s", neighbourhood_id)
        try:
            self._init_driver()
            deals = self._fetch_deals_by_neighborhood_id_selenium(neighbourhood_id)
            logger.info("Fetched %s deals for neighborhood %s", len(deals), neighbourhood_id)
            return deals
        except Exception as e:
            logger.exception("Failed to fetch deals for neighborhood %s", neighbourhood_id)
            raise NadlanAPIError(f"Failed to fetch deals for neighborhood {neighbourhood_id}: {e}")
        finally:
            self._cleanup_driver()

    def search_address(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for addresses using the Nadlan website search.

        Args:
            query: Address search query (in Hebrew or English)
            limit: Maximum number of results to return

        Returns:
            List of address suggestions with IDs and names
        """
        logger.info("Searching for address '%s'", query)
        try:
            self._init_driver()
            results = self._search_address_selenium(query, limit)
            logger.info("Found %s results for '%s'", len(results), query)
            return results
        except Exception as e:
            logger.exception("Address search failed for '%s'", query)
            raise NadlanAPIError(f"Failed to search for address '{query}': {e}")
        finally:
            self._cleanup_driver()

    def get_deals_by_address(self, address_query: str) -> List[Deal]:
        """Retrieve deals by searching for an address first, then fetching deals.

        Args:
            address_query: Address or neighborhood name to search for

        Returns:
            List of Deal objects

        Raises:
            NadlanAPIError: If the search or fetch fails
        """
        logger.info("Fetching deals for address '%s'", address_query)
        try:
            # First search for the address
            search_results = self.search_address(address_query, limit=5)

            if not search_results:
                raise NadlanAPIError(f"No addresses found for query: {address_query}")

            # Get the first (most relevant) result
            best_match = search_results[0]
            
            # Check if we have a direct address match (preferred)
            if best_match.get('type') == 'address' and best_match.get('key'):
                address_id = best_match['key']
                logger.info("Using direct address ID %s for address '%s'", address_id, address_query)
                try:
                    deals = self.get_deals_by_address_id(address_id)
                    logger.info("Fetched %s deals for address '%s' using address ID", len(deals), address_query)
                    return deals
                except Exception as e:
                    logger.warning("Failed to fetch deals by address ID %s, falling back to neighborhood: %s", 
                        address_id, str(e))
            
            # Fallback to neighborhood-based approach
            neighborhood_id = best_match.get('neighborhood_id')
            if not neighborhood_id:
                raise NadlanAPIError(f"Could not determine neighborhood ID for: {best_match['value']}")

            logger.info("Using neighborhood %s for address '%s'", neighborhood_id, address_query)
            # Fetch deals using the neighborhood ID
            deals = self.get_deals_by_neighborhood_id(neighborhood_id)
            logger.info("Fetched %s deals for address '%s'", len(deals), address_query)
            return deals

        except Exception as e:
            logger.exception("Failed to get deals for address '%s'", address_query)
            raise NadlanAPIError(f"Failed to get deals for address '{address_query}': {e}")

    def get_deals_by_address_id(self, address_id: str) -> List[Deal]:
        """Retrieve deals by address ID directly.

        Args:
            address_id: The address ID from the search results

        Returns:
            List of Deal objects

        Raises:
            NadlanAPIError: If the fetch fails
        """
        logger.info("Fetching deals for address ID '%s'", address_id)
        try:
            self._init_driver()
            deals = self._fetch_deals_by_address_id_selenium(address_id)
            logger.info("Fetched %s deals for address ID '%s'", len(deals), address_id)
            return deals
        except Exception as e:
            logger.exception("Failed to fetch deals for address ID '%s'", address_id)
            raise NadlanAPIError(f"Failed to fetch deals for address ID '{address_id}': {e}")
        finally:
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

    def _search_address_selenium(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for addresses using the Nadlan website search."""
        # Navigate to the Nadlan website
        self.driver.get("https://www.nadlan.gov.il/")
        time.sleep(3)
        
        # Find the search input field
        search_box = self.driver.find_element(By.ID, "myInput2")
        
        # Clear and enter the search query
        search_box.clear()
        search_box.send_keys(query)
        
        # Submit the search by pressing Enter
        search_box.send_keys(Keys.RETURN)
        
        # Wait for results to load
        time.sleep(5)
        
        # Check if we got redirected to a specific address page
        current_url = self.driver.current_url
        if "view=address" in current_url and "id=" in current_url:
            # Extract address ID from URL
            import re
            match = re.search(r'id=(\d+)', current_url)
            if match:
                address_id = match.group(1)
                # Try to extract neighborhood ID from the page
                neighborhood_id = self._extract_neighborhood_id_from_page()
                
                return [{
                    'type': 'address',
                    'key': address_id,
                    'value': query,
                    'neighborhood_id': neighborhood_id,
                    'rank': 0
                }]
        
        # If no direct address match, try to find results on the page
        results = []
        
        # Look for address suggestions or results
        try:
            # Look for any clickable elements that might be address results
            address_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                "div[class*='result'], div[class*='address'], div[class*='item'], a[href*='view=address']")
            
            for element in address_elements[:limit]:
                try:
                    href = element.get_attribute('href')
                    text = element.text.strip()
                    
                    if href and 'view=address' in href and text:
                        # Extract address ID from href
                        match = re.search(r'id=(\d+)', href)
                        if match:
                            address_id = match.group(1)
                            neighborhood_id = self._extract_neighborhood_id_from_page()
                            
                            results.append({
                                'type': 'address',
                                'key': address_id,
                                'value': text,
                                'neighborhood_id': neighborhood_id,
                                'rank': len(results)
                            })
                except Exception:
                    continue
                    
        except Exception as e:
            logger.warning(f"Error finding address results: {e}")
        
        # If no results found, try to search using the govmap API directly
        if not results:
            results = self._search_address_govmap_api(query, limit)
        
        return results[:limit]
    
    def _extract_neighborhood_id_from_page(self) -> Optional[str]:
        """Extract neighborhood ID from the current page."""
        try:
            # Look for neighborhood ID in various places on the page
            page_source = self.driver.page_source
            
            # Try to find neighborhood ID in JavaScript variables or data attributes
            import re
            patterns = [
                r'neighborhood[^=]*=.*?(\d+)',
                r'neighborhoodId[^=]*=.*?(\d+)',
                r'hoodId[^=]*=.*?(\d+)',
                r'"neighborhood_id":\s*"(\d+)"',
                r'"hoodId":\s*"(\d+)"'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_source, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            # Look for neighborhood ID in data attributes
            elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-neighborhood-id], [data-hood-id]")
            for element in elements:
                neighborhood_id = (element.get_attribute('data-neighborhood-id') or 
                                 element.get_attribute('data-hood-id'))
                if neighborhood_id:
                    return neighborhood_id
                    
        except Exception as e:
            logger.warning(f"Error extracting neighborhood ID: {e}")
        
        return None
    
    def _search_address_govmap_api(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fallback: Search using the govmap API directly."""
        import urllib.parse
        import requests
        
        try:
            # Encode the query for URL
            encoded_query = urllib.parse.quote(query)
            
            # Construct the autocomplete URL
            url = f"https://es.govmap.gov.il/TldSearch/api/AutoComplete?query={encoded_query}&ids=276267023&gid=govmap"
            
            # Make the request
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Process ADDRESS results (most relevant)
            if 'res' in data and 'ADDRESS' in data['res']:
                for item in data['res']['ADDRESS'][:limit]:
                    neighborhood_id = self._extract_neighborhood_id_from_poi(item)
                    results.append({
                        'type': 'address',
                        'key': item['Key'],
                        'value': item['Value'],
                        'neighborhood_id': neighborhood_id,
                        'rank': item.get('Rank', 0)
                    })
            
            # Process other result types if no addresses found
            if not results:
                for result_type in ['NEIGHBORHOOD', 'POI_MID_POINT', 'STREET', 'SETTLEMENT']:
                    if 'res' in data and result_type in data['res']:
                        for item in data['res'][result_type][:limit//2]:
                            neighborhood_id = self._extract_neighborhood_id_from_poi(item)
                            results.append({
                                'type': result_type.lower(),
                                'key': item['Key'],
                                'value': item['Value'],
                                'neighborhood_id': neighborhood_id,
                                'rank': item.get('Rank', 0)
                            })
            
            # Sort by rank and return top results
            results.sort(key=lambda x: x.get('rank', 0))
            return results[:limit]
            
        except Exception as e:
            logger.warning(f"Govmap API search failed: {e}")
            return []

    def _extract_neighborhood_id_from_poi(self, poi_item: Dict[str, Any]) -> Optional[str]:
        """Extract neighborhood ID from POI (Point of Interest) data.
        
        This is a simplified mapping - in practice you might want to use
        a more sophisticated approach or maintain a mapping table.
        """
        # This is a placeholder implementation
        # In practice, you'd need to implement proper neighborhood ID extraction
        # based on the actual POI data structure
        return None

    def _fetch_deals_by_address_id_selenium(self, address_id: str) -> List[Deal]:
        """Fetch deals by address ID using Selenium."""
        # Navigate to the address page
        url = f"https://www.nadlan.gov.il/?view=address&id={address_id}&page=deals"
        logger.info(f"Navigating to: {url}")
        
        self.driver.get(url)
        
        # Wait for page to load
        time.sleep(5)
        
        # Check if page loaded successfully
        current_url = self.driver.current_url
        logger.info(f"Current URL: {current_url}")
        
        # Try to find deals data in the page
        deals = []
        
        try:
            # Look for deals in various possible locations
            deals_data = self.driver.execute_script("""
                // Look for deals data in various possible locations
                if (window.dealsData) return window.dealsData;
                if (window.app && window.app.deals) return window.app.deals;
                if (window.data && window.data.deals) return window.data.deals;
                
                // Look for script tags with deals data
                const scripts = document.querySelectorAll('script');
                for (let script of scripts) {
                    const content = script.textContent || script.innerText;
                    if (content && content.includes('deals') && content.includes('[')) {
                        try {
                            const match = content.match(/deals[^=]*=\\s*(\\[.*?\\])/);
                            if (match) {
                                return JSON.parse(match[1]);
                            }
                        } catch (e) {
                            // Continue searching
                        }
                    }
                }
                return null;
            """)
            
            if deals_data and isinstance(deals_data, list):
                logger.info(f"Found deals data in page content: {len(deals_data)} items")
                deals = [Deal.from_item(item) for item in deals_data]
            else:
                # Try to find deals in table format
                deals = self._extract_deals_from_table()
                
        except Exception as e:
            logger.warning(f"Failed to extract deals from page content: {e}")
            # Try to find deals in table format as fallback
            deals = self._extract_deals_from_table()
        
        return deals
    
    def _extract_deals_from_table(self) -> List[Deal]:
        """Extract deals from table format on the page."""
        deals = []
        
        try:
            # First try to find the main deals table
            main_table = self.driver.find_element(By.CSS_SELECTOR, "table#dealsTable, .mainTable, table")
            if main_table:
                # Extract from the main table structure
                rows = main_table.find_elements(By.CSS_SELECTOR, "tbody tr")
                
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
                            # From the HTML: מספר סידורי, כתובת, שטח במ"ר, תאריך העסקה, מחיר העסקה, גוש/חלקה/תת-חלקה, סוג נכס, חדרים, קומה, מגמת שינוי
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
                                        price=deal_data.get('price', ''),
                                        date=deal_data.get('date', ''),
                                        rooms=deal_data.get('rooms', ''),
                                        floor=deal_data.get('floor', ''),
                                        area=deal_data.get('area', '')
                                    ))
                                    
                    except Exception as e:
                        logger.debug(f"Error processing table row: {e}")
                        continue
                        
        except Exception as e:
            logger.debug(f"Main table not found, trying alternative selectors: {e}")
            
            # Fallback: Look for any rows that might contain deal data
            try:
                rows = self.driver.find_elements(By.CSS_SELECTOR, 
                    "div[class*='row'], div[class*='deal'], div[class*='transaction'], tr")
                
                for row in rows:
                    try:
                        # Try to extract deal information from the row
                        cells = row.find_elements(By.CSS_SELECTOR, "div, td, span")
                        if len(cells) >= 3:  # Minimum cells for a deal
                            cell_texts = [cell.text.strip() for cell in cells if cell.text.strip()]
                            
                            # Look for patterns that might indicate a deal
                            if any(keyword in ' '.join(cell_texts).lower() for keyword in 
                                   ['₪', 'שקל', 'מחיר', 'תאריך', 'חדר', 'קומה']):
                                
                                # Create a basic deal object
                                deal_data = {
                                    'address': cell_texts[0] if cell_texts else '',
                                    'price': cell_texts[1] if len(cell_texts) > 1 else '',
                                    'date': cell_texts[2] if len(cell_texts) > 2 else '',
                                    'rooms': cell_texts[3] if len(cell_texts) > 3 else '',
                                    'floor': cell_texts[4] if len(cell_texts) > 4 else '',
                                    'area': cell_texts[5] if len(cell_texts) > 5 else ''
                                }
                                
                                # Try to create a Deal object
                                try:
                                    deal = Deal.from_item(deal_data)
                                    deals.append(deal)
                                except Exception:
                                    # If we can't create a proper Deal object, create a basic one
                                    deals.append(Deal(
                                        address=deal_data.get('address', ''),
                                        price=deal_data.get('price', ''),
                                        date=deal_data.get('date', ''),
                                        rooms=deal_data.get('rooms', ''),
                                        floor=deal_data.get('floor', ''),
                                        area=deal_data.get('area', '')
                                    ))
                                    
                    except Exception as e:
                        logger.debug(f"Error processing row: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Error extracting deals from table: {e}")
        
        logger.info(f"Extracted {len(deals)} deals from table format")
        return deals

    def _fetch_deals_by_neighborhood_id_selenium(self, neighbourhood_id: str) -> List[Deal]:
        """Fetch deals by neighborhood ID using Selenium."""
        # Navigate to the neighborhood page
        url = f"https://www.nadlan.gov.il/?view=neighborhood&id={neighbourhood_id}&page=deals"
        logger.info(f"Navigating to: {url}")
        
        self.driver.get(url)
        
        # Wait for page to load completely and check for errors
        self._wait_for_page_load()
        
        # Check for error modal first - improved detection
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
                    screenshot_path = f"error_modal_{neighbourhood_id}_{int(time.time())}.png"
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
            # Look for pagination info in the table summary
            pagination_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                ".tableSummary .pagination .paginate")
            
            for element in pagination_elements:
                text = element.text.strip()
                if '/' in text:
                    # Parse "1 / 52" format
                    parts = text.split('/')
                    if len(parts) == 2:
                        current_page = int(parts[0].strip())
                        total_pages = int(parts[1].strip())
                        return {
                            'current_page': current_page,
                            'total_pages': total_pages
                        }
            
            # Alternative: look for next button to determine if pagination exists
            next_button = self.driver.find_elements(By.CSS_SELECTOR, "#next, .nextBtn")
            if next_button and next_button[0].is_displayed():
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
            # Try to click the next button
            next_button = self.driver.find_elements(By.CSS_SELECTOR, "#next, .nextBtn")
            if next_button and next_button[0].is_displayed():
                next_button[0].click()
                time.sleep(1)  # Wait for navigation
                return True
                
        except Exception as e:
            logger.debug(f"Error navigating to page {page_num}: {e}")
        
        return False

    def _fetch_deals_by_street_id_selenium(self, street_id: str) -> List[Deal]:
        """Fetch deals by street ID using Selenium."""
        # Navigate to the street page
        url = f"https://www.nadlan.gov.il/?view=street&id={street_id}&page=deals"
        logger.info(f"Navigating to: {url}")
        
        self.driver.get(url)
        
        # Wait for page to load
        time.sleep(5)
        
        # Try to find deals data in the page
        deals = []
        
        try:
            # Look for deals in various possible locations
            deals_data = self.driver.execute_script("""
                // Look for deals data in various possible locations
                if (window.dealsData) return window.dealsData;
                if (window.app && window.app.deals) return window.app.deals;
                if (window.data && window.data.deals) return window.data.deals;
                
                // Look for script tags with deals data
                const scripts = document.querySelectorAll('script');
                for (let script of scripts) {
                    const content = script.textContent || script.innerText;
                    if (content && content.includes('deals') && content.includes('[')) {
                        try {
                            const match = content.match(/deals[^=]*=\\s*(\\[.*?\\])/);
                            if (match) {
                                return JSON.parse(match[1]);
                            }
                        } catch (e) {
                            // Continue searching
                        }
                    }
                }
                return null;
            """)
            
            if deals_data and isinstance(deals_data, list):
                logger.info(f"Found deals data in page content: {len(deals_data)} items")
                deals = [Deal.from_item(item) for item in deals_data]
            else:
                # Try to find deals in table format
                deals = self._extract_deals_from_table()
                
        except Exception as e:
            logger.warning(f"Failed to extract deals from page content: {e}")
            # Try to find deals in table format as fallback
            deals = self._extract_deals_from_table()
        
        return deals

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
    deals = scraper.get_deals_by_neighborhood_id("65210036")
    for deal in deals:
        print(f"{deal.address} - ₪{deal.deal_amount:,.0f}")