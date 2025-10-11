# -*- coding: utf-8 -*-
# flake8: noqa
"""
nadlan/scraper.py
-----------------

Simple scraper for retrieving real-estate transaction history from nadlan.gov.il.

This module provides a focused interface using Selenium to interact with the real website
and capture actual data.

Notes
=====
- Robustness updates: optional persistent user profile, human-like pauses/scrolls,
  safer Selenium options, and a refresh-or-fail policy when no data appears.
- Policy you requested: If error modal shows OR zero deals parsed -> refresh once,
  re-parse; if still nothing, raise NadlanAPIError. No modal-closing/backoff loops.
"""
from __future__ import annotations

import json
import logging
import time
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

from .exceptions import NadlanAPIError
from .models import Deal
from .cache import DealCache, IncrementalDealCollector

logger = logging.getLogger(__name__)


class NadlanDealsScraper:
    """Simple scraper for real estate deals from nadlan.gov.il."""

    def __init__(
        self,
        timeout: float = 30.0,
        headless: bool = True,
        max_age_days: int = 365,
        use_cache: bool = True,
        user_data_dir: Optional[str] = None,
    ):
        """Initialize the scraper.

        Args:
            timeout: Request timeout in seconds
            headless: Whether to run browser in headless mode
            max_age_days: Maximum age of deals to fetch (in days)
            use_cache: Whether to use caching for better performance
            user_data_dir: Optional Chrome profile directory to persist cookies/localStorage
        """
        self.timeout = timeout
        self.headless = headless
        self.max_age_days = max_age_days
        self.use_cache = use_cache
        self.user_data_dir = user_data_dir
        self.driver = None
        self.current_search_address = None
        self.error_modal_encountered = False

        if self.use_cache:
            self.cache = DealCache()
            self.incremental_collector = IncrementalDealCollector(self, self.cache)
        else:
            self.cache = None
            self.incremental_collector = None

    # -------------------------
    # Driver / setup
    # -------------------------
    def _safe_user_agent(self) -> str:
        return (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )

    def _init_driver(self, user_data_dir: Optional[str] = None):
        """Initialize the Selenium WebDriver with safe defaults.

        Uses optional persistent profile to keep cookies/localStorage.
        Avoids enabling CDP Network in headless to reduce fingerprint noise.
        """
        if self.driver is not None:
            return

        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()

        if self.headless:
            options.add_argument("--headless=new")  # newer headless
        else:
            ud = user_data_dir or self.user_data_dir
            if ud:
                options.add_argument(f"--user-data-dir={ud}")

        # Stability/perf
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1280,720")
        options.add_argument(f"--user-agent={self._safe_user_agent()}")

        # Reduce automation flags
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Optional: disable images if you want faster loads (commented by default)
        # prefs = {"profile.managed_default_content_settings.images": 2}
        # options.add_experimental_option("prefs", prefs)

        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_page_load_timeout(self.timeout)

        # Enable Network logs only in headed debug sessions; swallow failures
        try:
            if not self.headless:
                self.driver.execute_cdp_cmd("Network.enable", {})
                logger.info("Network monitoring enabled (debug mode).")
            else:
                logger.debug("Skipping Network.enable in headless mode.")
        except Exception as e:
            logger.debug("CDP Network.enable skipped: %s", e)

        # Best-effort minor fingerprint smoothing (non-essential)
        try:
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                        Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3]});
                    """
                },
            )
        except Exception:
            logger.debug("Could not inject minor stealth script (non-fatal).")

    def _cleanup_driver(self):
        """Clean up the Selenium WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            finally:
                self.driver = None

    # -------------------------
    # Human-like helpers
    # -------------------------
    def _human_pause(self, min_s: float = 0.4, max_s: float = 1.2):
        """Small randomized pause to reduce deterministic timings."""
        time.sleep(min_s + random.random() * (max_s - min_s))

    def _human_scroll(self):
        """Small randomized scroll to mimic a human reading the page."""
        try:
            delta = int(random.uniform(100, 350))
            self.driver.execute_script(f"window.scrollBy(0, {delta});")
            self._human_pause(0.2, 0.8)
        except Exception:
            pass

    # -------------------------
    # Modal / failure handling: refresh-or-fail
    # -------------------------
    def _check_for_error_modal(self) -> bool:
        """Check if an error modal is currently displayed."""
        try:
            error_selectors = [
                ".modal.show",
                ".error-modal",
                "[class*='error']",
                "[class*='modal'][style*='display: block']",
                ".modal[style*='display: block']",
                ".modal.show[style*='display: block']",
                "[role='dialog'][class*='modal']",
                ".fade.contanctModal.centerModal.smModal.titleContainer.modal.show",
            ]
            for selector in error_selectors:
                try:
                    error_modals = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for modal in error_modals:
                        if modal.is_displayed():
                            text = modal.text.strip()
                            if any(k in text for k in ["שגיאה", "error", "Error", "טעינת נתונים"]):
                                logger.error("Error modal detected: %s", text)
                                return True
                except Exception:
                    continue
            return False
        except Exception as e:
            logger.debug("Error during modal check: %s", e)
            return False

    def _refresh_once_and_reparse(self, parse_fn, *, address: str, neighborhood: str = "") -> Optional[List[Deal]]:
        """
        Single refresh attempt and re-parse. If still no data or modal persists -> return None.
        parse_fn(neighborhood) must return List[Deal].
        """
        try:
            current_url = self.driver.current_url
        except Exception:
            current_url = None

        logger.info("Refreshing page once and re-parsing (address=%s)...", address)
        try:
            if current_url:
                self.driver.refresh()
            else:
                self.driver.get("https://www.nadlan.gov.il/")
        except Exception as e:
            logger.debug("Refresh failed: %s", e)

        self._wait_for_page_load()
        self._human_pause(0.5, 1.0)
        self._human_scroll()

        # If we lost 'page=deals', force it back (best-effort)
        try:
            url_after = self.driver.current_url
            if url_after and ("address" in url_after or "neighborhood" in url_after) and "page=deals" not in url_after:
                self.driver.get(url_after + "&page=deals")
                self._wait_for_page_load()
        except Exception:
            pass

        # If modal persists after refresh -> bail
        if self._check_for_error_modal():
            logger.error("Modal still present after single refresh")
            return None

        # Re-parse once
        try:
            return parse_fn(neighborhood)
        except Exception as e:
            logger.debug("Re-parse after refresh failed: %s", e)
            return None

    # -------------------------
    # Page / API wait helpers
    # -------------------------
    def _wait_for_deals_api_call(self, timeout: int = 30) -> bool:
        """Wait for the deals API call to complete by monitoring network requests or DOM."""
        start_time = time.time()
        network_monitoring_available = True

        while time.time() - start_time < timeout:
            try:
                if network_monitoring_available:
                    try:
                        logs = self.driver.get_log("performance")
                        for log in logs:
                            message = log.get("message", {})
                            if isinstance(message, str):
                                try:
                                    message = json.loads(message)
                                except (json.JSONDecodeError, TypeError):
                                    continue
                            method = message.get("method", "")
                            if method == "Network.responseReceived":
                                response = message.get("params", {}).get("response", {})
                                url = response.get("url", "")
                                if any(e in url for e in ["/api/deal", "/deal", "deals"]):
                                    status = response.get("status", 0)
                                    if status == 200:
                                        logger.info("Deals API call completed successfully: %s", url)
                                        return True
                                    elif status >= 400:
                                        logger.warning("Deals API call failed with status %s: %s", status, url)
                                        return False
                            elif method == "Network.loadingFailed":
                                error = message.get("params", {}).get("errorText", "")
                                logger.warning("Network request failed while waiting: %s", error)
                    except Exception as e:
                        logger.debug("Network monitoring failed: %s", e)
                        network_monitoring_available = False

                # Fallback to DOM detection after half-timeout or if network logs unavailable
                if not network_monitoring_available or time.time() - start_time > timeout * 0.5:
                    try:
                        table_rows = self.driver.find_elements(By.CSS_SELECTOR, "tbody tr, .deal-row, [class*='deal'], [class*='transaction']")
                        if len(table_rows) > 0:
                            data_rows = []
                            for row in table_rows:
                                cells = row.find_elements(By.CSS_SELECTOR, "td")
                                if len(cells) >= 5:
                                    cell_texts = [cell.text.strip() for cell in cells]
                                    if not any(k in " ".join(cell_texts).lower() for k in ["מספר סידורי", "כתובת", "header"]):
                                        data_rows.append(row)
                            if data_rows:
                                logger.info("Found %d data rows in deals table", len(data_rows))
                                return True
                    except Exception as e:
                        logger.debug("DOM detection failed: %s", e)

                time.sleep(1)
            except Exception as e:
                logger.debug("Error during API call monitoring: %s", e)
                time.sleep(1)

        logger.warning("Timeout waiting for deals API call")
        return False

    def _wait_for_page_load(self):
        """Wait for the page to load completely and check for indicators."""
        try:
            time.sleep(3)
            try:
                _ = self.driver.execute_script("return document.readyState")
            except Exception:
                pass
            time.sleep(2)

            loading_selectors = ["[class*='loading']", "[class*='spinner']", ".loading", ".spinner"]
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
            logger.debug("Error during page load wait: %s", e)

    # -------------------------
    # Content extraction
    # -------------------------
    def _extract_city_from_search_address(self, search_address: str) -> str:
        if not search_address:
            return ""
        city_patterns = [
            "תל אביב-יפו", "תל אביב", "ירושלים", "חיפה", "באר שבע", "אשדוד", "פתח תקווה",
            "נתניה", "בת ים", "רמת גן", "אשקלון", "רחובות", "הרצליה", "כפר סבא", "ראשון לציון",
            "גבעתיים", "קרית גת", "קרית ביאליק", "קרית מוצקין", "קרית ים", "קרית אתא",
            "קרית שמונה", "קרית מלאכי", "קרית אונו", "קרית טבעון", "קרית חיים", "קרית מוצקין",
        ]
        for city in city_patterns:
            if search_address.endswith(city):
                return city
        parts = search_address.split()
        if len(parts) >= 2:
            return " ".join(parts[-2:]) if len(parts[-1]) > 3 else " ".join(parts[-1:])
        return ""

    def _build_full_address(self, street_address: str) -> str:
        if not street_address or not self.current_search_address:
            return street_address
        city = self._extract_city_from_search_address(self.current_search_address)
        if city and city not in street_address:
            return f"{street_address}, {city}"
        return street_address

    def _extract_neighborhood_from_page(self) -> str:
        try:
            neighborhood_section = self.driver.find_elements(By.CSS_SELECTOR, ".otherNeighborhoodsSection .mainTitle")
            if neighborhood_section:
                title_text = neighborhood_section[0].text.strip()
                if "בשכונה" in title_text:
                    parts = title_text.split("בשכונה")
                    if len(parts) > 1:
                        neighborhood_part = parts[1].strip()
                        if "לפי רחובות" in neighborhood_part:
                            neighborhood_part = neighborhood_part.split("לפי רחובות")[0].strip()
                        return neighborhood_part
            neighborhood_elements = self.driver.find_elements(By.CSS_SELECTOR, "[class*='neighborhood'], [class*='שכונה']")
            for element in neighborhood_elements:
                text = element.text.strip()
                if text and len(text) < 50:
                    return text
        except Exception as e:
            logger.warning("Failed to extract neighborhood from page: %s", e)
        return ""

    def _parse_deal_date(self, date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        date_formats = ["%d/%m/%Y", "%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y", "%d/%m/%y", "%d.%m.%y"]
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str.strip(), fmt)
                current_year = datetime.now().year
                if parsed_date.year > current_year:
                    logger.warning("Date %s appears to be in the future (%s), assuming previous year", date_str, parsed_date.year)
                    parsed_date = parsed_date.replace(year=parsed_date.year - 1)
                return parsed_date
            except ValueError:
                continue
        logger.warning("Could not parse date: %s", date_str)
        return None

    def _is_deal_recent(self, deal: Deal, cutoff_date: datetime) -> bool:
        if not deal.deal_date:
            return True
        deal_date = self._parse_deal_date(deal.deal_date)
        if not deal_date:
            return True
        return deal_date >= cutoff_date

    def _filter_deals_by_age(self, deals: List[Deal]) -> List[Deal]:
        if self.max_age_days <= 0:
            return deals
        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
        recent_deals = [deal for deal in deals if self._is_deal_recent(deal, cutoff_date)]
        logger.info("Filtered %d deals to %d recent deals (last %d days)", len(deals), len(recent_deals), self.max_age_days)
        return recent_deals

    # -------------------------
    # Context manager
    # -------------------------
    def __enter__(self):
        self._init_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup_driver()

    # -------------------------
    # Public API
    # -------------------------
    def get_neighborhood_info(self, neighbourhood_id: str) -> Dict[str, Any]:
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
        deals: List[Deal] = []
        try:
            tables = self.driver.find_elements(By.CSS_SELECTOR, "table#dealsTable, .mainTable, table")
            for table_idx, main_table in enumerate(tables):
                logger.info("Processing table %d", table_idx + 1)
                rows = main_table.find_elements(By.CSS_SELECTOR, "tbody tr")
                if len(rows) == 0:
                    logger.info("Table %d has no data rows", table_idx + 1)
                    continue
                logger.info("Table %d has %d data rows", table_idx + 1, len(rows))
                for row in rows:
                    try:
                        cells = row.find_elements(By.CSS_SELECTOR, "td")
                        if len(cells) >= 5:
                            cell_texts = [cell.text.strip() for cell in cells]
                            if any(k in " ".join(cell_texts).lower() for k in ["מספר סידורי", "כתובת", "header"]):
                                continue
                            deal_data = {
                                "serial_number": cell_texts[0] if len(cell_texts) > 0 else "",
                                "address": self._build_full_address(cell_texts[1]) if len(cell_texts) > 1 else "",
                                "area": cell_texts[2] if len(cell_texts) > 2 else "",
                                "deal_date": cell_texts[3] if len(cell_texts) > 3 else "",
                                "deal_amount": cell_texts[4] if len(cell_texts) > 4 else "",
                                "parcelNum": cell_texts[5] if len(cell_texts) > 5 else "",
                                "asset_type": cell_texts[6] if len(cell_texts) > 6 else "",
                                "rooms": cell_texts[7] if len(cell_texts) > 7 else "",
                                "floor": cell_texts[8] if len(cell_texts) > 8 else "",
                                "trend": cell_texts[9] if len(cell_texts) > 9 else "",
                                "neighborhood": neighborhood,
                            }
                            if deal_data["address"] and deal_data["deal_amount"]:
                                try:
                                    deal = Deal.from_item(deal_data)
                                    deals.append(deal)
                                except Exception as e:
                                    logger.debug("Error creating Deal object: %s", e)
                                    deals.append(
                                        Deal(
                                            address=deal_data.get("address", ""),
                                            deal_amount=deal_data.get("deal_amount", ""),
                                            deal_date=deal_data.get("deal_date", ""),
                                            rooms=deal_data.get("rooms", ""),
                                            area=deal_data.get("area", ""),
                                            parcel_block=(deal_data.get("parcelNum", "").split("-")[0] if deal_data.get("parcelNum") else ""),
                                            parcel_parcel=(deal_data.get("parcelNum", "").split("-")[1] if deal_data.get("parcelNum") and "-" in deal_data.get("parcelNum", "") else ""),
                                            parcel_sub_parcel=(deal_data.get("parcelNum", "").split("-")[2] if deal_data.get("parcelNum") and deal_data.get("parcelNum", "").count("-") >= 2 else ""),
                                            asset_type=deal_data.get("asset_type", ""),
                                        )
                                    )
                    except Exception as e:
                        logger.debug("Error processing table row: %s", e)
                        continue
                logger.info("Extracted %d deals from table %d", len([d for d in deals if d]), table_idx + 1)
        except Exception as e:
            logger.debug("Error extracting deals from tables: %s", e)
        logger.info("Total extracted %d deals from all tables", len(deals))
        return deals

    def get_deals_by_address(self, address: str, max_age_days: Optional[int] = None, force_refresh: bool = False) -> List[Deal]:
        logger.info("Fetching deals for address %s", address)
        self.current_search_address = address

        if self.use_cache and self.incremental_collector and not force_refresh:
            try:
                deals = self.incremental_collector.get_deals_incremental(address, force_refresh, max_age_days)
                return deals
            except Exception as e:
                logger.warning("Incremental collection failed, falling back to direct fetch: %s", e)

        try:
            self._init_driver()
            deals = self._fetch_deals_by_address_selenium(address)
        except Exception as e:
            logger.error("Selenium scraping failed for address %s: %s", address, e)
            raise NadlanAPIError(f"Failed to fetch deals for address {address}: {e}")

        if max_age_days is not None:
            original_max_age = self.max_age_days
            self.max_age_days = max_age_days
            deals = self._filter_deals_by_age(deals)
            self.max_age_days = original_max_age
        else:
            deals = self._filter_deals_by_age(deals)

        if self.use_cache and self.cache:
            error_modal_encountered = getattr(self, "error_modal_encountered", False)
            should_cache = len(deals) > 0 or error_modal_encountered
            if should_cache:
                self.cache.store_deals(address, deals, error_modal_encountered)
            else:
                logger.warning("Not caching empty results for %s", address)

        return deals

    def _fetch_deals_by_address_selenium(self, address: str) -> List[Deal]:
        try:
            self.error_modal_encountered = False

            if self._navigate_to_deals_via_search(address):
                self._wait_for_page_load()
                # small human-like behavior
                self._human_pause(0.5, 1.0)
                self._human_scroll()

                neighborhood = self._extract_neighborhood_from_page()
                if neighborhood:
                    logger.info("Extracted neighborhood: %s", neighborhood)

                # Policy: if modal present -> single refresh-and-reparse; else fail.
                if self._check_for_error_modal():
                    self.error_modal_encountered = True
                    try:
                        screenshot_path = f"error_modal_{address.replace(' ', '_')}_{int(time.time())}.png"
                        self.driver.save_screenshot(screenshot_path)
                        logger.info("Screenshot saved: %s", screenshot_path)
                    except Exception:
                        pass

                    deals_after = self._refresh_once_and_reparse(
                        self._extract_deals_from_current_page,
                        address=address,
                        neighborhood=neighborhood,
                    )
                    if not deals_after:
                        raise NadlanAPIError("No data available (modal). Stopping: שגיאה בטעינת הנתונים")

                    # If refresh worked, continue (including pagination)
                    deals = deals_after
                    if deals:
                        deals.extend(self._extract_deals_from_all_pages(neighborhood))
                    return deals

                logger.info("Waiting for deals API call to complete...")
                api_success = self._wait_for_deals_api_call(timeout=20)
                if not api_success:
                    logger.warning("Deals API call may have failed, continuing with data extraction...")

                # Extract deals
                deals = self._extract_deals_from_current_page(neighborhood)

                # If zero deals first pass, perform single refresh-and-reparse
                if not deals:
                    logger.info("No deals parsed on first attempt; single refresh-and-retry.")
                    deals_retry = self._refresh_once_and_reparse(
                        self._extract_deals_from_current_page,
                        address=address,
                        neighborhood=neighborhood,
                    )
                    if not deals_retry:
                        raise NadlanAPIError("No data returned from API after refresh. Stopping.")
                    deals = deals_retry

                # Pagination (only after we have something)
                if deals:
                    deals.extend(self._extract_deals_from_all_pages(neighborhood))

                return deals
            else:
                logger.error("Failed to navigate to deals page via search")
                return []
        except Exception as e:
            logger.error("Error fetching deals for address %s: %s", address, e)
            raise NadlanAPIError(f"Failed to fetch deals for address {address}: {e}")

    def _navigate_to_deals_via_search(self, search_term: str) -> bool:
        try:
            logger.info("Navigating to main page...")
            self.driver.get("https://www.nadlan.gov.il/")
            time.sleep(3)

            self._human_pause(0.3, 0.8)

            search_input = None
            selectors = [
                "#myInput2",
                ".react-autosuggest__input",
                "input[placeholder*='הקלד כתובת']",
                "input[placeholder*='כתובת']",
                "input[type='text']",
                ".searchRow input",
                ".autosuggestContainer input",
            ]

            for selector in selectors:
                try:
                    search_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if search_input and search_input.is_displayed():
                        logger.info("Found search input with selector: %s", selector)
                        break
                except Exception as e:
                    logger.debug("Selector '%s' failed: %s", selector, e)
                    continue

            if not search_input:
                logger.error("Could not find search input with any selector")
                return False

            logger.info("Searching for: %s", search_term)
            self.driver.execute_script("arguments[0].focus();", search_input)
            time.sleep(0.6)

            # Clear + set value
            self.driver.execute_script("arguments[0].value = '';", search_input)
            self.driver.execute_script("arguments[0].value = arguments[1];", search_input, search_term)

            # Fire events
            self.driver.execute_script(
                """
                var input = arguments[0];
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                """,
                search_input,
            )

            time.sleep(2.5)
            self._human_scroll()

            suggestions = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".react-autosuggest__suggestions-list li, .autosuggest-item, [role='option'], .react-autosuggest__suggestion",
            )

            if suggestions:
                logger.info("Found %d suggestions for '%s'", len(suggestions), search_term)
                address_suggestion = None
                for suggestion in suggestions:
                    suggestion_text = suggestion.text.strip()
                    if any(k in suggestion_text.lower() for k in ["רחוב", "street", "כתובת", "address"]):
                        address_suggestion = suggestion
                        break

                target = address_suggestion or suggestions[0]
                logger.info("Clicking suggestion: %s", target.text.strip())
                try:
                    target.click()
                except Exception:
                    try:
                        self.driver.execute_script("arguments[0].click();", target)
                    except Exception:
                        pass
                time.sleep(3)

                current_url = self.driver.current_url
                logger.info("Current URL after search: %s", current_url)

                if "address" in current_url:
                    if "page=deals" not in current_url:
                        deals_url = current_url + "&page=deals"
                        logger.info("Navigating to deals page: %s", deals_url)
                        self.driver.get(deals_url)
                        time.sleep(3)
                    else:
                        logger.info("Already on deals page.")
                    return True
                elif "neighborhood" in current_url:
                    if "page=deals" not in current_url:
                        deals_url = current_url + "&page=deals"
                        logger.info("Navigating to deals page: %s", deals_url)
                        self.driver.get(deals_url)
                        time.sleep(3)
                    else:
                        logger.info("Already on deals page.")
                    return True
                else:
                    logger.warning("Search '%s' did not lead to address or neighborhood page", search_term)
                    return False
            else:
                logger.warning("No autocomplete suggestions found for '%s'", search_term)
                try:
                    search_input.send_keys(Keys.RETURN)
                except Exception:
                    try:
                        self.driver.execute_script(
                            "arguments[0].dispatchEvent(new KeyboardEvent('keydown', {'key':'Enter'}));",
                            search_input,
                        )
                    except Exception:
                        pass
                time.sleep(3)

                current_url = self.driver.current_url
                if "address" in current_url or "neighborhood" in current_url:
                    if "page=deals" not in current_url:
                        deals_url = current_url + "&page=deals"
                        logger.info("Navigating to deals page: %s", deals_url)
                        self.driver.get(deals_url)
                        time.sleep(3)
                    else:
                        logger.info("Already on deals page.")
                    return True
                else:
                    logger.warning("Search did not lead to address or neighborhood page")
                    return False

        except Exception as e:
            logger.error("Error during search navigation: %s", e)
            return False

    def _navigate_to_deals_direct_url(self, neighbourhood_id: str) -> bool:
        try:
            url = f"https://www.nadlan.gov.il/?view=neighborhood&id={neighbourhood_id}&page=deals"
            logger.info("Navigating directly to: %s", url)
            self.driver.get(url)
            time.sleep(3)
            return True
        except Exception as e:
            logger.error("Error with direct URL navigation: %s", e)
            return False

    def _extract_deals_from_current_page(self, neighborhood: str = "") -> List[Deal]:
        max_wait_time = 30
        wait_interval = 1
        waited_time = 0
        deals: List[Deal] = []

        while waited_time < max_wait_time:
            try:
                if self._check_for_error_modal():
                    raise NadlanAPIError("Error modal appeared during data loading: שגיאה בטעינת הנתונים")

                table_rows = self.driver.find_elements(By.CSS_SELECTOR, "tbody tr, .deal-row, [class*='deal'], [class*='transaction']")
                if len(table_rows) > 0:
                    deals_data = self.driver.execute_script(
                        r"""
                        if (window.dealsData) return window.dealsData;
                        if (window.app && window.app.deals) return window.app.deals;
                        if (window.data && window.data.deals) return window.data.deals;
                        if (window.vue && window.vue.$data && window.vue.$data.deals) return window.vue.$data.deals;
                        if (window.vue && window.vue.$children) {
                            for (let child of window.vue.$children) { if (child.deals) return child.deals; }
                        }
                        const scripts = document.querySelectorAll('script');
                        for (let script of scripts) {
                            const content = script.textContent || script.innerText;
                            if (content && content.includes('deals') && content.includes('[')) {
                                try {
                                    const patterns = [
                                        /deals[^=]*=\s*(\[.*?\])/, 
                                        /"deals"\s*:\s*(\[.*?\])/, 
                                        /deals\s*:\s*(\[.*?\])/, 
                                        /data\.deals\s*=\s*(\[.*?\])/ 
                                    ];
                                    for (let p of patterns) {
                                        const m = content.match(p);
                                        if (m) { return JSON.parse(m[1]); }
                                    }
                                } catch (e) {}
                            }
                        }
                        return null;
                        """
                    )
                    if deals_data and isinstance(deals_data, list) and len(deals_data) > 0:
                        logger.info("Found deals data in page content: %d items", len(deals_data))
                        deals = [Deal.from_item(item) for item in deals_data]
                        break

                    deals = self._extract_deals_from_table(neighborhood)
                    if deals:
                        logger.info("Extracted %d deals from table", len(deals))
                        break

                no_deals_msg = self.driver.find_elements(By.CSS_SELECTOR, "[class*='no-deals'], [class*='empty'], [class*='no-data'], .tableSummary")
                if no_deals_msg:
                    for msg in no_deals_msg:
                        if msg.is_displayed() and any(k in msg.text.lower() for k in ["לא נמצאו", "no deals", "empty", "0 עסקאות"]):
                            logger.info("No deals found for this neighborhood")
                            return []

                time.sleep(wait_interval)
                waited_time += wait_interval
            except Exception as e:
                logger.warning("Error during data extraction attempt: %s", e)
                time.sleep(wait_interval)
                waited_time += wait_interval

        if not deals:
            logger.warning("No deals data found after waiting %s seconds", max_wait_time)
            deals = self._extract_deals_from_table(neighborhood)

        return deals

    def _extract_deals_from_all_pages(self, neighborhood: str = "") -> List[Deal]:
        all_deals: List[Deal] = []
        try:
            pagination_info = self._get_pagination_info()
            if not pagination_info:
                logger.info("No pagination found, only one page of deals")
                return []
            total_pages = pagination_info["total_pages"]
            current_page = pagination_info["current_page"]
            logger.info("Found pagination: %d / %d pages", current_page, total_pages)

            cutoff_date = datetime.now() - timedelta(days=self.max_age_days) if self.max_age_days > 0 else None
            aggressive_early_termination = self.max_age_days > 0 and self.max_age_days < 365

            for page_num in range(current_page + 1, total_pages + 1):
                logger.info("Extracting deals from page %d/%d", page_num, total_pages)
                if self._navigate_to_page(page_num):
                    time.sleep(2)
                    page_deals = self._extract_deals_from_table(neighborhood)
                    if page_deals:
                        logger.info("Found %d deals on page %d", len(page_deals), page_num)
                        if cutoff_date:
                            if self._all_deals_older_than(page_deals, cutoff_date):
                                all_deals.extend(page_deals)
                                break
                            elif aggressive_early_termination and self._most_deals_older_than(page_deals, cutoff_date, threshold=0.8):
                                all_deals.extend(page_deals)
                                break
                        all_deals.extend(page_deals)
                    else:
                        logger.warning("No deals found on page %d", page_num)
                        if aggressive_early_termination:
                            break
                else:
                    logger.warning("Failed to navigate to page %d", page_num)
                    break
        except Exception as e:
            logger.error("Error during pagination: %s", e)

        logger.info("Total deals collected from all pages: %d", len(all_deals))
        return all_deals

    def _most_deals_older_than(self, deals: List[Deal], cutoff_date: datetime, threshold: float = 0.8) -> bool:
        if not deals:
            return False
        old_deals = sum(1 for d in deals if not self._is_deal_recent(d, cutoff_date))
        return (old_deals / len(deals)) >= threshold

    def _all_deals_older_than(self, deals: List[Deal], cutoff_date: datetime) -> bool:
        if not deals:
            return False
        for d in deals:
            if self._is_deal_recent(d, cutoff_date):
                return False
        return True

    def _get_pagination_info(self) -> dict:
        try:
            pagination_elements = self.driver.find_elements(By.CSS_SELECTOR, ".tableSummary .pagination .paginate")
            logger.info("Found %d pagination elements", len(pagination_elements))
            options = []
            for i, el in enumerate(pagination_elements):
                text = el.text.strip()
                logger.info("Pagination element %d: '%s'", i + 1, text)
                if "/" in text:
                    parts = text.split("/")
                    if len(parts) == 2:
                        current_page = int(parts[0].strip())
                        total_pages = int(parts[1].strip())
                        options.append({"current_page": current_page, "total_pages": total_pages, "element": el})
            if options:
                addr_opt = None
                neigh_opt = None
                for opt in options:
                    try:
                        ts = opt["element"].find_element(By.XPATH, "./ancestor::div[contains(@class, 'tableSummary')]")
                        summary = ts.text.lower()
                        if any(k in summary for k in ["עסקאות בכתובת", "בכתובת", "address"]):
                            addr_opt = opt
                        elif any(k in summary for k in ["עסקאות נוספות בשכונה", "בשכונה", "neighborhood"]):
                            neigh_opt = opt
                    except Exception:
                        continue
                if addr_opt:
                    return addr_opt
                if neigh_opt:
                    return neigh_opt
                # fallback: choose the one with fewest pages (likely address-specific)
                return min(options, key=lambda x: x["total_pages"])

            # fallback by next button presence
            next_buttons = self.driver.find_elements(By.CSS_SELECTOR, "#next, .nextBtn")
            for nb in next_buttons:
                if nb.is_displayed() and not nb.get_attribute("disabled"):
                    return {"current_page": 1, "total_pages": 2}
        except Exception as e:
            logger.debug("Error getting pagination info: %s", e)
        return None

    def _navigate_to_page(self, page_num: int) -> bool:
        try:
            next_buttons = self.driver.find_elements(By.CSS_SELECTOR, "#next, .nextBtn")
            for i, nb in enumerate(next_buttons):
                try:
                    if nb.is_displayed() and not nb.get_attribute("disabled"):
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", nb)
                            time.sleep(0.5)
                            nb.click()
                            time.sleep(3)
                            new_p = self._get_pagination_info()
                            if new_p and new_p["current_page"] > 1:
                                return True
                        except Exception:
                            try:
                                self.driver.execute_script("arguments[0].click();", nb)
                                time.sleep(3)
                                new_p = self._get_pagination_info()
                                if new_p and new_p["current_page"] > 1:
                                    return True
                            except Exception:
                                continue
                except Exception:
                    continue
        except Exception as e:
            logger.warning("Error navigating to page %d: %s", page_num, e)
        return False

    def _get_neighborhood_info_selenium(self, neighbourhood_id: str) -> Dict[str, Any]:
        url = f"https://www.nadlan.gov.il/?view=neighborhood&id={neighbourhood_id}"
        logger.info("Navigating to: %s", url)
        self.driver.get(url)
        time.sleep(5)
        info: Dict[str, Any] = {}
        try:
            name_el = self.driver.find_element(By.CSS_SELECTOR, "h1, .neighborhood-name, .title")
            info["neigh_name"] = name_el.text.strip()
        except Exception:
            info["neigh_name"] = f"Neighborhood {neighbourhood_id}"
        try:
            details = self.driver.find_elements(By.CSS_SELECTOR, ".neighborhood-details, .info, .details")
            for detail in details:
                text = detail.text.strip()
                if ":" in text:
                    k, v = text.split(":", 1)
                    info[k.strip()] = v.strip()
        except Exception:
            pass
        return info


if __name__ == "__main__":
    # Example dev run: headed with a persistent profile for stability
    scraper = NadlanDealsScraper(headless=False, user_data_dir="/tmp/nadlan_profile")
    try:
        deals = scraper.get_deals_by_address("רוזוב 14 תל אביב", max_age_days=180)
        for deal in deals:
            # Avoid :,.0f here because deal_amount may be str depending on your Deal.from_item
            print(f"{deal.address} - ₪{deal.deal_amount}")
    finally:
        scraper._cleanup_driver()
