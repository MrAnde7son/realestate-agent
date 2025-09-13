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
            # Look for table rows that might contain deal data
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
                            except:
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
        except:
            info['neigh_name'] = f"Neighborhood {neighbourhood_id}"
        
        try:
            # Look for other neighborhood details
            details = self.driver.find_elements(By.CSS_SELECTOR, ".neighborhood-details, .info, .details")
            for detail in details:
                text = detail.text.strip()
                if ':' in text:
                    key, value = text.split(':', 1)
                    info[key.strip()] = value.strip()
        except:
            pass
        
        return info
