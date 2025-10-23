# -*- coding: utf-8 -*-
"""

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
import os
import tempfile
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

from .exceptions import NadlanAPIError
from .models import Deal
from .cache import DealCache, IncrementalDealCollector

import random
from selenium.webdriver.common.action_chains import ActionChains


logger = logging.getLogger(__name__)


class NadlanDealsScraper:
    """Simple scraper for real estate deals from nadlan.gov.il."""
    
    def __init__(self, timeout: float = 30.0, headless: bool = True, max_age_days: int = 365, use_cache: bool = True):
        """Initialize the scraper.
        
        Args:
            timeout: Request timeout in seconds
            headless: Whether to run browser in headless mode
            max_age_days: Maximum age of deals to fetch (in days)
            use_cache: Whether to use caching for better performance
        """
        self.timeout = timeout
        self.headless = headless
        self.max_age_days = max_age_days
        self.use_cache = use_cache
        self.driver = None
        self.current_search_address = None  # Store the current search address for full address construction
        self.error_modal_encountered = False  # Track if error modal was encountered during scraping
        
        # Initialize cache if enabled
        if self.use_cache:
            self.cache = DealCache()
            self.incremental_collector = IncrementalDealCollector(self, self.cache)
        else:
            self.cache = None
            self.incremental_collector = None
        
    def _init_driver(self):
        """Initialize the Selenium WebDriver with headless-safe, stealthy settings."""
        if self.driver is not None:
            return

        options = webdriver.ChromeOptions()

        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1366,768")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-features=Translate")
        options.add_argument(f"--user-data-dir={tempfile.mkdtemp(prefix='chrome_profile_')}")
        options.add_argument("--lang=he-IL")
        options.add_argument("--use-gl=swiftshader")
        options.add_argument("--enable-webgl")
        options.add_argument("--ignore-gpu-blocklist")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        # These help some sites bind mouse events properly under headless
        options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})  # <-- enables self.driver.get_log('performance')

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        try:
            driver.execute_cdp_cmd("Page.setWebLifecycleState", {"state": "active"})
        except Exception:
            pass

        # --- Stealth hardening via CDP (unchanged from your version, kept for completeness) ---
        try:
            driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "Asia/Jerusalem"})
            driver.execute_cdp_cmd("Emulation.setLocaleOverride", {"locale": "he-IL"})
            driver.execute_cdp_cmd("Network.setUserAgentOverride", {
                "userAgent": driver.execute_script("return navigator.userAgent"),
                "acceptLanguage": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
                "platform": "MacIntel"
            })
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'platform', {get: () => 'MacIntel'});
                    Object.defineProperty(navigator, 'language', {get: () => 'he-IL'});
                    Object.defineProperty(navigator, 'languages', {get: () => ['he-IL','he','en-US','en']});
                    Object.defineProperty(navigator, 'vendor', {get: () => 'Google Inc.'});
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(param){
                    if (param === 37445) return 'Google Inc.';
                    if (param === 37446) return 'ANGLE (Apple, Apple GPU)';
                    return getParameter.call(this, param);
                    };
                """
            })
        except Exception as e:
            logger.debug(f"CDP stealth setup failed: {e}")

        try:
            driver.execute_cdp_cmd("Network.enable", {})
            driver.execute_cdp_cmd("Runtime.enable", {})
        except Exception as e:
            logger.debug(f"Could not enable Network/Runtime: {e}")

        driver.set_page_load_timeout(self.timeout)
        driver.set_script_timeout(max(self.timeout, 60))
        self.driver = driver

    def _wait_for_deals_api_call(self, timeout: int = 30) -> bool:
        """Wait for the deals API call to complete by monitoring network requests."""
        import time
        start_time = time.time()
        
        # In headless mode, network monitoring might not work reliably
        # So we'll use a hybrid approach: try network monitoring first, then fall back to DOM-based detection
        network_monitoring_available = True
        
        while time.time() - start_time < timeout:
            try:
                # Try network monitoring first
                if network_monitoring_available:
                    try:
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
                    except Exception as e:
                        logger.debug(f"Network monitoring failed: {e}")
                        network_monitoring_available = False
                
                # Fallback: Check DOM for deals data or loading indicators
                if not network_monitoring_available or time.time() - start_time > timeout * 0.5:
                    # Check if deals table has loaded with data
                    try:
                        table_rows = self.driver.find_elements(By.CSS_SELECTOR, 
                            "tbody tr, .deal-row, [class*='deal'], [class*='transaction']")
                        
                        if len(table_rows) > 0:
                            # Check if we have actual data rows (not just headers)
                            data_rows = []
                            for row in table_rows:
                                cells = row.find_elements(By.CSS_SELECTOR, "td")
                                if len(cells) >= 5:  # Should have at least 5 columns
                                    cell_texts = [cell.text.strip() for cell in cells]
                                    # Skip header rows
                                    if not any(keyword in ' '.join(cell_texts).lower() for keyword in 
                                               ['מספר סידורי', 'כתובת', 'header']):
                                        data_rows.append(row)
                            
                            if len(data_rows) > 0:
                                logger.info(f"Found {len(data_rows)} data rows in deals table")
                                return True
                    except Exception as e:
                        logger.debug(f"DOM-based detection failed: {e}")
                
                time.sleep(1)
                
            except Exception as e:
                logger.debug(f"Error during API call monitoring: {e}")
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
    
    def _extract_city_from_search_address(self, search_address: str) -> str:
        """Extract city name from the search address.
        
        Args:
            search_address: The full search address (e.g., "רוזוב 4 תל אביב-יפו")
            
        Returns:
            City name (e.g., "תל אביב-יפו")
        """
        if not search_address:
            return ""
            
        # Common patterns for extracting city from address
        # Look for common city patterns at the end of the address
        city_patterns = [
            "תל אביב-יפו", "תל אביב", "ירושלים", "חיפה", "באר שבע", "אשדוד", "פתח תקווה",
            "נתניה", "בת ים", "רמת גן", "אשקלון", "רחובות", "הרצליה", "כפר סבא", "ראשון לציון",
            "גבעתיים", "קרית גת", "קרית ביאליק", "קרית מוצקין", "קרית ים", "קרית אתא",
            "קרית שמונה", "קרית מלאכי", "קרית אונו", "קרית טבעון", "קרית חיים", "קרית מוצקין"
        ]
        
        # Try to find city at the end of the address
        for city in city_patterns:
            if search_address.endswith(city):
                return city
                
        # If no city found, try to extract the last word/phrase
        parts = search_address.split()
        if len(parts) >= 2:
            # Take the last 1-2 parts as potential city
            return " ".join(parts[-2:]) if len(parts[-1]) > 3 else " ".join(parts[-1:])
            
        return ""
    
    def _build_full_address(self, street_address: str) -> str:
        """Build full address by combining street address with city from search.
        
        Args:
            street_address: Street address from table (e.g., "עולי הגרדום 20")
            
        Returns:
            Full address (e.g., "עולי הגרדום 20, תל אביב-יפו")
        """
        if not street_address or not self.current_search_address:
            return street_address
            
        city = self._extract_city_from_search_address(self.current_search_address)
        if city and city not in street_address:
            return f"{street_address}, {city}"
            
        return street_address
    
    def _extract_neighborhood_from_page(self) -> str:
        """Extract neighborhood name from the page content.
        
        Returns:
            Neighborhood name (e.g., "נמל תל-אביב")
        """
        try:
            # Look for the neighborhood section with class "otherNeighborhoodsSection"
            neighborhood_section = self.driver.find_elements(By.CSS_SELECTOR, ".otherNeighborhoodsSection .mainTitle")
            
            if neighborhood_section:
                title_text = neighborhood_section[0].text.strip()
                # Extract neighborhood from title like "עסקאות נוספות בשכונה נמל תל-אביב לפי רחובות"
                if "בשכונה" in title_text:
                    # Split by "בשכונה" and take the part after it
                    parts = title_text.split("בשכונה")
                    if len(parts) > 1:
                        neighborhood_part = parts[1].strip()
                        # Remove "לפי רחובות" if present
                        if "לפי רחובות" in neighborhood_part:
                            neighborhood_part = neighborhood_part.split("לפי רחובות")[0].strip()
                        return neighborhood_part
                        
            # Fallback: look for neighborhood in other possible locations
            neighborhood_elements = self.driver.find_elements(By.CSS_SELECTOR, "[class*='neighborhood'], [class*='שכונה']")
            for element in neighborhood_elements:
                text = element.text.strip()
                if text and len(text) < 50:  # Reasonable neighborhood name length
                    return text
                    
        except Exception as e:
            logger.warning(f"Failed to extract neighborhood from page: {e}")
            
        return ""

    def _parse_deal_date(self, date_str: str) -> Optional[datetime]:
        """Parse deal date string to datetime object.
        
        Args:
            date_str: Date string in various formats (e.g., "01/01/2023", "2023-01-01")
            
        Returns:
            Parsed datetime object or None if parsing fails
        """
        if not date_str:
            return None
            
        # Common date formats in Hebrew/Israeli context
        date_formats = [
            "%d/%m/%Y",      # 01/01/2023
            "%Y-%m-%d",      # 2023-01-01
            "%d.%m.%Y",      # 01.01.2023
            "%d-%m-%Y",      # 01-01-2023
            "%d/%m/%y",      # 01/01/23
            "%d.%m.%y",      # 01.01.23
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str.strip(), fmt)
                
                # Handle future dates - if year is in the future, assume it's actually the previous year
                current_year = datetime.now().year
                if parsed_date.year > current_year:
                    logger.warning(f"Date {date_str} appears to be in the future ({parsed_date.year}), assuming it's {parsed_date.year - 1}")
                    parsed_date = parsed_date.replace(year=parsed_date.year - 1)
                
                return parsed_date
            except ValueError:
                continue
                
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def _is_deal_recent(self, deal: Deal, cutoff_date: datetime) -> bool:
        """Check if a deal is recent enough to include.
        
        Args:
            deal: Deal object to check
            cutoff_date: Cutoff date for filtering
            
        Returns:
            True if deal is recent enough, False otherwise
        """
        if not deal.deal_date:
            # If no date, include the deal (conservative approach)
            return True
            
        deal_date = self._parse_deal_date(deal.deal_date)
        if not deal_date:
            # If can't parse date, include the deal (conservative approach)
            return True
            
        return deal_date >= cutoff_date
    
    def _filter_deals_by_age(self, deals: List[Deal]) -> List[Deal]:
        """Filter deals by age based on max_age_days setting.
        
        Args:
            deals: List of deals to filter
            
        Returns:
            Filtered list of recent deals
        """
        if self.max_age_days <= 0:
            return deals
            
        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
        recent_deals = [deal for deal in deals if self._is_deal_recent(deal, cutoff_date)]
        
        logger.info(f"Filtered {len(deals)} deals to {len(recent_deals)} recent deals (last {self.max_age_days} days)")
        return recent_deals
    
    
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

    def _extract_deals_from_table(self, neighborhood: str = "") -> List[Deal]:
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
                                'address': self._build_full_address(cell_texts[1]) if len(cell_texts) > 1 else '',
                                'area': cell_texts[2] if len(cell_texts) > 2 else '',
                                'deal_date': cell_texts[3] if len(cell_texts) > 3 else '',
                                'deal_amount': cell_texts[4] if len(cell_texts) > 4 else '',
                                'parcelNum': cell_texts[5] if len(cell_texts) > 5 else '',
                                'asset_type': cell_texts[6] if len(cell_texts) > 6 else '',
                                'rooms': cell_texts[7] if len(cell_texts) > 7 else '',
                                'floor': cell_texts[8] if len(cell_texts) > 8 else '',
                                'trend': cell_texts[9] if len(cell_texts) > 9 else '',
                                'neighborhood': neighborhood  # Add neighborhood information
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

    def get_deals_by_address(self, address: str, max_age_days: Optional[int] = None, force_refresh: bool = False) -> List[Deal]:
        """Retrieve deals using a specific address with optional caching.

        Args:
            address: The address to search for (e.g., "רוזוב 4 תל אביב")
            max_age_days: Override the default max age for this request
            force_refresh: Force refresh even if cache is available

        Returns:
            List of Deal objects

        Raises:
            NadlanAPIError: If the API call fails
        """
        logger.info("Fetching deals for address %s", address)
        
        # Store the search address for full address construction
        self.current_search_address = address
        
        # Use incremental collector if caching is enabled
        if self.use_cache and self.incremental_collector and not force_refresh:
            try:
                deals = self.incremental_collector.get_deals_incremental(address, force_refresh, max_age_days)
                return deals
            except Exception as e:
                logger.warning(f"Incremental collection failed, falling back to direct fetch: {e}")
        
        # Use Selenium scraping (API fallback disabled until implementation is fixed)
        try:
            self._init_driver()
            deals = self._fetch_deals_by_address_selenium(address)
        except Exception as e:
            logger.error(f"Selenium scraping failed for address {address}: {e}")
            raise NadlanAPIError(f"Failed to fetch deals for address {address}: {e}")
        
        # Apply date filtering if specified
        if max_age_days is not None:
            original_max_age = self.max_age_days
            self.max_age_days = max_age_days
            deals = self._filter_deals_by_age(deals)
            self.max_age_days = original_max_age
        else:
            deals = self._filter_deals_by_age(deals)
        
        # Store in cache if enabled
        if self.use_cache and self.cache:
            # Check if error modal was encountered during scraping
            error_modal_encountered = getattr(self, 'error_modal_encountered', False)
            
            # Cache results if we have them, or if we encountered an error modal (to prevent re-fetching)
            # Mark error modal encounters in metadata to prevent using cached error results
            should_cache = len(deals) > 0 or error_modal_encountered
            
            if should_cache:
                self.cache.store_deals(address, deals, error_modal_encountered)
            else:
                logger.warning(f"Not caching empty results for {address}")
            
        return deals
    
    def _fetch_deals_by_address_selenium(self, address: str) -> List[Deal]:
        """Fetch deals by address using Selenium with search-based navigation."""
        try:
            # Reset error flag at the beginning of each fetch
            self.error_modal_encountered = False
            
            # First, try to navigate to deals page using search
            if self._navigate_to_deals_via_search(address):
                # Wait for page to load completely and check for errors
                self._wait_for_page_load()
                
                # Extract neighborhood from the page
                neighborhood = self._extract_neighborhood_from_page()
                if neighborhood:
                    logger.info(f"Extracted neighborhood: {neighborhood}")
                
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
                        # Set error flag to prevent caching
                        self.error_modal_encountered = True
                        
                        # Take a screenshot for debugging
                        try:
                            screenshot_path = f"error_modal_{address.replace(' ', '_')}_{int(time.time())}.png"
                            self.driver.save_screenshot(screenshot_path)
                            logger.info(f"Screenshot saved: {screenshot_path}")
                        except Exception as e:
                            logger.debug(f"Could not save screenshot: {e}")
                        
                        # Error modal indicates API failure - refresh to reload deals
                        logger.info("Error modal detected - API call failed...")
                        raise NadlanAPIError("Website showed error modal even after refresh: שגיאה בטעינת הנתונים")
                            
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
                
                deals = []
                
                # First, get deals from the current page
                deals = self._extract_deals_from_current_page(neighborhood)
                
                # Then, check for pagination and get deals from all pages
                if deals:
                    deals.extend(self._extract_deals_from_all_pages(neighborhood))
                
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
                    # Only navigate to deals page if we're not already there
                    if 'page=deals' not in current_url:
                        deals_url = current_url + '&page=deals'
                        logger.info(f"Navigating to deals page: {deals_url}")
                        self.driver.get(deals_url)
                        time.sleep(3)
                    else:
                        logger.info("Already on deals page, no need to navigate")
                    return True
                elif 'neighborhood' in current_url:
                    # Only navigate to deals page if we're not already there
                    if 'page=deals' not in current_url:
                        deals_url = current_url + '&page=deals'
                        logger.info(f"Navigating to deals page: {deals_url}")
                        self.driver.get(deals_url)
                        time.sleep(3)
                    else:
                        logger.info("Already on deals page, no need to navigate")
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
                    # Only navigate to deals page if we're not already there
                    if 'page=deals' not in current_url:
                        deals_url = current_url + '&page=deals'
                        logger.info(f"Navigating to deals page: {deals_url}")
                        self.driver.get(deals_url)
                        time.sleep(3)
                    else:
                        logger.info("Already on deals page, no need to navigate")
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
    
    def _extract_deals_from_current_page(self, neighborhood: str = "") -> List[Deal]:
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
                    deals = self._extract_deals_from_table(neighborhood)
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
            deals = self._extract_deals_from_table(neighborhood)
        
        return deals
    
    def _extract_deals_from_all_pages(self, neighborhood: str = "") -> List[Deal]:
        """Extract deals from all pages using pagination with early termination for old deals."""
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
            
            # Calculate cutoff date for early termination
            cutoff_date = datetime.now() - timedelta(days=self.max_age_days) if self.max_age_days > 0 else None
            
            # If max_age_days is very restrictive (less than 1 year), be more aggressive about early termination
            aggressive_early_termination = self.max_age_days > 0 and self.max_age_days < 365
            
            if aggressive_early_termination:
                logger.info(f"Using aggressive early termination for max_age_days={self.max_age_days}")
            
            # Navigate through remaining pages with early termination
            for page_num in range(current_page + 1, total_pages + 1):
                logger.info(f"Extracting deals from page {page_num}/{total_pages}")
                
                # Click next button or navigate to specific page
                if self._navigate_to_page(page_num):
                    # Wait for page to load
                    time.sleep(2)
                    
                    # Extract deals from current page
                    page_deals = self._extract_deals_from_table(neighborhood)
                    if page_deals:
                        logger.info(f"Found {len(page_deals)} deals on page {page_num}")
                        
                        # Check if we should stop pagination due to old deals
                        if cutoff_date:
                            if self._all_deals_older_than(page_deals, cutoff_date):
                                logger.info(f"Stopping pagination at page {page_num} - all deals are older than {self.max_age_days} days")
                                # Still add the deals from this page before stopping
                                all_deals.extend(page_deals)
                                break
                            elif aggressive_early_termination and self._most_deals_older_than(page_deals, cutoff_date, threshold=0.8):
                                logger.info(f"Stopping pagination at page {page_num} - most deals (80%+) are older than {self.max_age_days} days")
                                # Still add the deals from this page before stopping
                                all_deals.extend(page_deals)
                                break
                            
                        all_deals.extend(page_deals)
                    else:
                        logger.warning(f"No deals found on page {page_num}")
                        # If we're using aggressive early termination and no deals found, stop
                        if aggressive_early_termination:
                            logger.info("No deals found on page, stopping pagination due to aggressive early termination")
                            break
                else:
                    logger.warning(f"Failed to navigate to page {page_num}")
                    break
                    
        except Exception as e:
            logger.error(f"Error during pagination: {e}")
        
        logger.info(f"Total deals collected from all pages: {len(all_deals)}")
        return all_deals
    
    def _most_deals_older_than(self, deals: List[Deal], cutoff_date: datetime, threshold: float = 0.8) -> bool:
        """Check if most deals in the list are older than the cutoff date.
        
        Args:
            deals: List of deals to check
            cutoff_date: Cutoff date for comparison
            threshold: Threshold for "most" (default 0.8 = 80%)
            
        Returns:
            True if most deals are older than cutoff date
        """
        if not deals:
            return False
            
        old_deals_count = 0
        for deal in deals:
            if not self._is_deal_recent(deal, cutoff_date):
                old_deals_count += 1
                
        return (old_deals_count / len(deals)) >= threshold
    
    def _all_deals_older_than(self, deals: List[Deal], cutoff_date: datetime) -> bool:
        """Check if all deals in the list are older than the cutoff date.
        
        Args:
            deals: List of deals to check
            cutoff_date: Cutoff date for comparison
            
        Returns:
            True if all deals are older than cutoff date
        """
        if not deals:
            return False
            
        for deal in deals:
            if self._is_deal_recent(deal, cutoff_date):
                return False
                
        return True
    
    def _get_pagination_info(self) -> dict:
        """Get pagination information from the page."""
        try:
            # Look for pagination info in ALL table summaries
            pagination_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                ".tableSummary .pagination .paginate")
            
            logger.info(f"Found {len(pagination_elements)} pagination elements")
            
            # Collect all pagination info
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
                            'total_pages': total_pages,
                            'element': element
                        })
            
            # When searching by address, prioritize the address-specific pagination
            # Look for pagination that's associated with the address deals table
            if pagination_options:
                # First, try to find pagination associated with address-specific deals
                # Look for pagination that's near address-specific content
                address_pagination = None
                neighborhood_pagination = None
                
                for option in pagination_options:
                    # Check if this pagination is associated with address-specific deals
                    # by looking at the table summary text
                    try:
                        table_summary = option['element'].find_element(By.XPATH, "./ancestor::div[contains(@class, 'tableSummary')]")
                        summary_text = table_summary.text.lower()
                        
                        # If the summary mentions the specific address or "עסקאות בכתובת", it's address-specific
                        if any(keyword in summary_text for keyword in ['עסקאות בכתובת', 'בכתובת', 'address']):
                            address_pagination = option
                            logger.info(f"Found address-specific pagination: {option['current_page']} / {option['total_pages']}")
                        # If it mentions neighborhood or "עסקאות נוספות בשכונה", it's neighborhood-specific
                        elif any(keyword in summary_text for keyword in ['עסקאות נוספות בשכונה', 'בשכונה', 'neighborhood']):
                            neighborhood_pagination = option
                            logger.info(f"Found neighborhood-specific pagination: {option['current_page']} / {option['total_pages']}")
                    except Exception as e:
                        logger.debug(f"Could not determine pagination context: {e}")
                        continue
                
                # Prefer address-specific pagination when available
                if address_pagination:
                    logger.info(f"Using address-specific pagination: {address_pagination['current_page']} / {address_pagination['total_pages']}")
                    return address_pagination
                elif neighborhood_pagination:
                    logger.info(f"Using neighborhood-specific pagination: {neighborhood_pagination['current_page']} / {neighborhood_pagination['total_pages']}")
                    return neighborhood_pagination
                else:
                    # Fallback: choose the pagination with the fewest pages (likely address-specific)
                    best_option = min(pagination_options, key=lambda x: x['total_pages'])
                    logger.info(f"Fallback: selected pagination with fewest pages: {best_option['current_page']} / {best_option['total_pages']}")
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
    scraper = NadlanDealsScraper(headless=True)
    deals = scraper.get_deals_by_address("הירקון 319 תל אביב", max_age_days=365 * 10)
    for deal in deals:
        print(f"{deal.address} - ₪{deal.deal_amount:,.0f}")