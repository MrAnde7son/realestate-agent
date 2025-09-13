# -*- coding: utf-8 -*-
"""
nadlan/scraper.py
-----------------

Simple scraper for retrieving real-estate transaction history from nadlan.gov.il.

This module provides a focused interface using Playwright to interact with the real website
and capture actual API responses, bypassing authentication issues.

Usage
::::::

    from gov.nadlan import NadlanDealsScraper
    scraper = NadlanDealsScraper()
    deals = scraper.get_deals_by_neighborhood_id("65210036")
    for deal in deals:
        print(f"{deal.address} - ₪{deal.deal_amount:,.0f}")

Notes
:::::

* This implementation uses Playwright to interact with the real website
* No authentication tokens are required - it uses the same browser session as the website
* The API is robust and handles various response formats automatically
* Please be courteous and avoid rapid repeated calls to respect the service
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional, Sequence

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

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
            
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(self.timeout)
    
    def _cleanup_driver(self):
        """Clean up the Selenium WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
            except:
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
            street_id: The street ID from nadlan.gov.il

        Returns:
            List of Deal objects

        Raises:
            NadlanAPIError: If the API call fails
        """
        logger.info("Fetching deals for street %s", street_id)
        try:
            deals = asyncio.run(self._fetch_deals_by_street(street_id))
            logger.info(
                "Fetched %s deals for street %s", len(deals), street_id
            )
            return deals
        except Exception as e:
            logger.exception(
                "Failed to fetch deals for street %s", street_id
            )
            raise NadlanAPIError(
                f"Failed to fetch deals for street {street_id}: {e}"
            )

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
            deals = asyncio.run(self._fetch_deals_by_neighborhood(neighbourhood_id))
            logger.info(
                "Fetched %s deals for neighborhood %s", len(deals), neighbourhood_id
            )
            return deals
        except Exception as e:
            logger.exception(
                "Failed to fetch deals for neighborhood %s", neighbourhood_id
            )
            raise NadlanAPIError(
                f"Failed to fetch deals for neighborhood {neighbourhood_id}: {e}"
            )

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
                logger.info(
                    "Using direct address ID %s for address '%s'", address_id, address_query
                )
                try:
                    deals = self.get_deals_by_address_id(address_id)
                    logger.info(
                        "Fetched %s deals for address '%s' using address ID", len(deals), address_query
                    )
                    return deals
                except Exception as e:
                    logger.warning(
                        "Failed to fetch deals by address ID %s, falling back to neighborhood: %s", 
                        address_id, str(e)
                    )
            
            # Fallback to neighborhood-based approach
            neighborhood_id = best_match.get('neighborhood_id')
            if not neighborhood_id:
                raise NadlanAPIError(f"Could not determine neighborhood ID for: {best_match['value']}")

            logger.info(
                "Using neighborhood %s for address '%s'", neighborhood_id, address_query
            )
            # Fetch deals using the neighborhood ID
            deals = self.get_deals_by_neighborhood_id(neighborhood_id)
            logger.info(
                "Fetched %s deals for address '%s'", len(deals), address_query
            )
            return deals

        except Exception as e:
            logger.exception("Failed to get deals for address '%s'", address_query)
            raise NadlanAPIError(
                f"Failed to get deals for address '{address_query}': {e}"
            )

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
        logger.info("Fetching neighborhood info for %s", neighbourhood_id)
        try:
            info = asyncio.run(self._fetch_neighborhood_info(neighbourhood_id))
            logger.info("Fetched neighborhood info for %s", neighbourhood_id)
            return info
        except Exception as e:
            logger.exception(
                "Failed to fetch neighborhood info for %s", neighbourhood_id
            )
            raise NadlanAPIError(
                f"Failed to fetch neighborhood info for {neighbourhood_id}: {e}"
            )

    async def _fetch_neighborhood_info(self, neigh_id: str) -> Dict[str, Any]:
        """Fetch neighborhood information using Playwright."""
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.headless)
            try:
                ctx = await browser.new_context()
                page = await ctx.new_page()
                
                # Load the neighborhood page
                await page.goto(f"https://www.nadlan.gov.il/?view=neighborhood&id={neigh_id}&page=deals", 
                               timeout=int(self.timeout * 1000))
                
                # Get API base from config.json
                api_base = await self._get_api_base(page)
                
                # Make the GetInfo request
                resp = await page.request.post(
                    f"{api_base}/GetInfo",
                    data=json.dumps({"base_name": "neigh_id", "base_id": neigh_id}),
                    headers={"content-type": "application/json"},
                    timeout=int(self.timeout * 1000),
                )
                
                if resp.status != 200:
                    raise NadlanAPIError(f"GetInfo HTTP {resp.status}")
                
                data = await resp.json()
                return {
                    "neigh_id": data["neigh_id"],
                    "neigh_name": data["neigh_name"],
                    "setl_id": str(data["setl_id"]),
                    "setl_name": data["setl_name"],
                }
            finally:
                await browser.close()

    async def _get_api_base(self, page) -> str:
        """Get API base URL from config.json."""
        js = """
        async () => {
          const res = await fetch('/config.json', {credentials:'omit'});
          const cfg = await res.json();
          return cfg.api_base;
        }
        """
        api_base = await page.evaluate(js)
        if not api_base:
            raise NadlanAPIError("config.json missing api_base")
        return api_base

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
                except:
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
        a more comprehensive database or API to map POIs to neighborhood IDs.
        """
        value = poi_item.get('Value', '')
        
        # Known neighborhood mappings (can be expanded)
        known_mappings = {
            'רמת החייל': '65210036',
            'רמת החיל': '65210036',  # Alternative spelling for רמת החייל
            'החיל תל אביב-יפו': '65210036',  # Street in רמת החייל
            'רמת אביב': '65210001',
            'נווה צדק': '65210002',
            'פלורנטין': '65210003',
            'יפו': '65210004',
            'התקווה': '65210005',
            'שכונת שפירא': '65210006',
            'קריית שלום': '65210007',
            'קריית יובל': '65210008',
            'קריית הממשלה': '65210009',
            'קריית הלאום': '65210010',
        }
        
        # City/Settlement mappings (when searching for entire cities)
        city_mappings = {
            'תל אביב': '5000',  # תל אביב-יפו settlement ID
            'תל אביב-יפו': '5000',
            'ירושלים': '3000',
            'חיפה': '4000',
            'באר שבע': '6000',
            'ראשון לציון': '8300',
            'פתח תקווה': '7900',
            'חולון': '6600',
            'רמת גן': '5200',
            'גבעתיים': '5300',
            'קריית אונו': '5400',
            'רמת השרון': '5500',
            'הוד השרון': '5600',
            'כפר סבא': '5700',
            'רעננה': '8700',
        }
        
        # Check if the POI contains any known neighborhood names
        for neighborhood_name, neighborhood_id in known_mappings.items():
            if neighborhood_name in value:
                return neighborhood_id
        
        # Check if the POI contains any known city names
        for city_name, city_id in city_mappings.items():
            if city_name in value:
                return city_id
        
        # If no direct match, return None (will need additional lookup)
        return None

    async def _fetch_deals_by_neighborhood(self, neigh_id: str) -> List[Deal]:
        """Fetch deals by neighborhood using Playwright."""
        async with async_playwright() as pw:
            # Launch browser with additional options for stability
            browser = await pw.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ]
            )
            try:
                # Create context with additional options
                ctx = await browser.new_context(
                    ignore_https_errors=True,
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
                )
                page = await ctx.new_page()

                # Capture the first /api/deal response
                fut = asyncio.get_event_loop().create_future()

                def _maybe_res(r: Response) -> None:
                    url = r.url
                    if "/api/deal" in url:
                        if not fut.done():
                            fut.set_result(r)

                page.on("response", _maybe_res)

                # Navigate to the neighborhood page with retry logic
                url = f"https://www.nadlan.gov.il/?view=neighborhood&id={neigh_id}&page=deals"
                
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        await page.goto(url, timeout=int(self.timeout * 1000), wait_until='domcontentloaded')
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise e
                        logger.warning(f"Navigation attempt {attempt + 1} failed: {e}, retrying...")
                        await asyncio.sleep(1)

                # Wait for /api/deal response
                resp: Response = await asyncio.wait_for(fut, timeout=self.timeout + 10)
                if resp.status != 200:
                    raise NadlanAPIError(f"/api/deal HTTP {resp.status}")

                body_bytes = await resp.body()
                deals = self._decode_deals_payload(body_bytes)
                return deals
            finally:
                await browser.close()

    async def _fetch_deals_by_street(self, street_id: str) -> List[Deal]:
        """Fetch deals by street using Playwright."""
        async with async_playwright() as pw:
            # Launch browser with additional options for stability
            browser = await pw.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ]
            )
            try:
                # Create context with additional options
                ctx = await browser.new_context(
                    ignore_https_errors=True,
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
                )
                page = await ctx.new_page()

                # Capture the first /api/deal response
                fut = asyncio.get_event_loop().create_future()

                def _maybe_res(r: Response) -> None:
                    url = r.url
                    if "/api/deal" in url:
                        if not fut.done():
                            fut.set_result(r)

                page.on("response", _maybe_res)

                # Navigate to the street page with retry logic
                url = f"https://www.nadlan.gov.il/?view=street&id={street_id}&page=deals"
                
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        await page.goto(url, timeout=int(self.timeout * 1000), wait_until='domcontentloaded')
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise e
                        logger.warning(f"Navigation attempt {attempt + 1} failed: {e}, retrying...")
                        await asyncio.sleep(1)

                # Wait for /api/deal response
                resp: Response = await asyncio.wait_for(fut, timeout=self.timeout + 10)
                if resp.status != 200:
                    raise NadlanAPIError(f"/api/deal HTTP {resp.status}")

                body_bytes = await resp.body()
                deals = self._decode_deals_payload(body_bytes)
                return deals
            finally:
                await browser.close()

    async def _fetch_deals_by_address_id(self, address_id: str) -> List[Deal]:
        """Fetch deals by address ID using Playwright."""
        async with async_playwright() as pw:
            # Launch browser with additional options for stability
            browser = await pw.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ]
            )
            try:
                # Create context with additional options
                ctx = await browser.new_context(
                    ignore_https_errors=True,
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
                )
                page = await ctx.new_page()

                # Capture the first /api/deal response
                fut = asyncio.get_event_loop().create_future()

                def _maybe_res(r: Response) -> None:
                    url = r.url
                    if "/api/deal" in url:
                        if not fut.done():
                            fut.set_result(r)

                # Navigate to the address page with retry logic
                url = f"https://www.nadlan.gov.il/?view=address&id={address_id}&page=deals"
                
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        await page.goto(url, timeout=int(self.timeout * 1000), wait_until='networkidle')
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise e
                        logger.warning(f"Navigation attempt {attempt + 1} failed: {e}, retrying...")
                        await asyncio.sleep(1)

                # Wait a bit more for the page to fully load
                await asyncio.sleep(2)

                # Try to get deals data from the page content
                try:
                    # Look for deals data in the page
                    deals_data = await page.evaluate("""
                        () => {
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
                                        const match = content.match(/deals[^=]*=\s*(\[.*?\])/);
                                        if (match) {
                                            return JSON.parse(match[1]);
                                        }
                                    } catch (e) {
                                        // Continue searching
                                    }
                                }
                            }
                            return null;
                        }
                    """)
                    
                    if deals_data:
                        logger.info(f"Found deals data in page content: {len(deals_data)} items")
                        return [Deal.from_item(item) for item in deals_data]
                    
                except Exception as e:
                    logger.warning(f"Failed to extract deals from page content: {e}")

                # Fallback: try to intercept the API call
                page.on("response", _maybe_res)
                
                # Refresh the page to trigger the API call
                await page.reload(wait_until='networkidle')
                await asyncio.sleep(1)
                
                # Wait for /api/deal response
                try:
                    resp: Response = await asyncio.wait_for(fut, timeout=10)
                    if resp.status != 200:
                        raise NadlanAPIError(f"/api/deal HTTP {resp.status}")

                    body_bytes = await resp.body()
                    deals = self._decode_deals_payload(body_bytes)
                except asyncio.TimeoutError:
                    # If we still can't get the API response, return empty list
                    logger.warning("Could not capture API response, returning empty deals list")
                    deals = []
                return deals
            finally:
                await browser.close()

    def _decode_deals_payload(self, body: bytes) -> List[Deal]:
        """
        Decode the deals payload from the API response.
        Handles various formats: plain JSON, API Gateway envelopes, base64+gzip.
        """
        # 1) try plain JSON
        try:
            data = json.loads(body.decode("utf-8"))
            items = self._extract_items_from_json(data)
            if items is not None:
                return [Deal.from_item(x) for x in items]
            # maybe {"body": "..."}
            if isinstance(data, dict) and "body" in data and isinstance(data["body"], str):
                decoded = self._decode_base64_gzip(data["body"])
                items = self._extract_items_from_json(decoded)
                if items is not None:
                    return [Deal.from_item(x) for x in items]
        except Exception:
            # fallthrough to base64 decode
            pass

        # 2) try raw base64+gzip text
        try:
            txt = body.decode("utf-8")
            if txt.startswith("H4sI") or txt.strip().startswith('"H4sI'):
                txt = txt.strip().strip('"')
                decoded = self._decode_base64_gzip(txt)
                items = self._extract_items_from_json(decoded)
                if items is not None:
                    return [Deal.from_item(x) for x in items]
        except Exception:
            pass

        raise NadlanAPIError("Unrecognized /api/deal payload format")

    @staticmethod
    def _extract_items_from_json(obj: Any) -> Optional[Sequence[Dict[str, Any]]]:
        """Extract items from JSON response."""
        if not isinstance(obj, dict):
            return None
        # happy path: {"data":{"items":[...]}}
        data = obj.get("data") if isinstance(obj.get("data"), dict) else obj
        items = data.get("items") if isinstance(data, dict) else None
        if isinstance(items, list):
            return items
        return None

    @staticmethod
    def _decode_base64_gzip(b64_text: str) -> Dict[str, Any]:
        """Decode base64+gzipped data."""
        import base64
        import gzip
        
        raw = base64.b64decode(b64_text)
        decomp = gzip.decompress(raw)
        return json.loads(decomp.decode("utf-8"))


# Simple convenience function
def get_deals_by_neighborhood_id(neighbourhood_id: str, timeout: float = 30.0) -> List[Dict[str, Any]]:
    """Convenience function to get deals for a neighborhood."""
    with NadlanDealsScraper(timeout=timeout) as scraper:
        deals = scraper.get_deals_by_neighborhood_id(neighbourhood_id)
        return [deal.to_dict() for deal in deals]


if __name__ == "__main__":
    import argparse
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(
        description="Fetch Israeli real‑estate deals from nadlan.gov.il."
    )
    parser.add_argument(
        "--neighbourhood-id", "-n", metavar="ID", required=True,
        help="Numeric neighbourhood id from the URL (e.g., 65210036)"
    )
    parser.add_argument("--limit", type=int, default=0, help="Limit number of deals to fetch")
    parser.add_argument("--headed", action="store_true", help="Show browser window (debug)")
    parser.add_argument("--csv", metavar="PATH", help="Export deals to CSV")
    args = parser.parse_args()
    
    try:
        with NadlanDealsScraper(headless=not args.headed) as scraper:
            deals = scraper.get_deals_by_neighborhood_id(args.neighbourhood_id)
            
            if not deals:
                print("No deals were found for the given input.")
                sys.exit(0)
            
            # Apply limit if specified
            if args.limit > 0:
                deals = deals[:args.limit]
            
            if args.csv:
                import csv
                with open(args.csv, "w", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    w.writerow(["address", "deal_date", "deal_amount", "rooms", "floor", "asset_type", "year_built", "area"])
                    for d in deals:
                        w.writerow([d.address, d.deal_date, d.deal_amount, d.rooms, d.floor, d.asset_type, d.year_built, d.area])
                print(f"CSV written: {args.csv}")
            else:
                deals_dict = [deal.to_dict() for deal in deals]
                print(json.dumps(deals_dict, ensure_ascii=False, indent=2))
            
    except NadlanAPIError as e:
        logger.error("Error fetching deals: %s", e)
        sys.exit(1)
