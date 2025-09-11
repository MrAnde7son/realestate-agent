#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mavat Selenium Client

This module provides a Selenium-based client for the Mavat system, following the same
successful pattern used in the Nadlan scraper. Selenium often handles complex JavaScript
interactions better than Playwright for government websites.

Based on the successful approach from: gov/nadlan/scraper_selenium.py
"""

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


@dataclass
class MavatSearchHit:
    """Represents a single search hit returned by Mavat."""
    plan_id: str
    title: Optional[str] = None
    status: Optional[str] = None
    authority: Optional[str] = None
    jurisdiction: Optional[str] = None
    entity_number: Optional[str] = None
    entity_name: Optional[str] = None
    approval_date: Optional[str] = None
    status_date: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


@dataclass
class MavatPlan:
    """Represents basic details about a plan."""
    plan_id: str
    plan_name: Optional[str] = None
    status: Optional[str] = None
    authority: Optional[str] = None
    jurisdiction: Optional[str] = None
    last_update: Optional[str] = None
    entity_number: Optional[str] = None
    approval_date: Optional[str] = None
    status_date: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


@dataclass
class MavatAttachment:
    """Represents a document attachment."""
    filename: str
    file_type: Optional[str] = None
    size: Optional[int] = None
    url: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


class MavatSeleniumClient:
    """Selenium-based client for the Mavat system."""
    
    BASE_URL = "https://mavat.iplan.gov.il"
    SEARCH_URL = f"{BASE_URL}/SV3"
    
    def __init__(self, timeout: float = 30.0, headless: bool = True):
        """Initialize the Selenium client.
        
        Args:
            timeout: Request timeout in seconds
            headless: Whether to run browser in headless mode
        """
        self.timeout = timeout
        self.headless = headless
        self.driver = None
        self.wait = None
    
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
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(self.timeout)
            self.wait = WebDriverWait(self.driver, self.timeout)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def _cleanup_driver(self):
        """Clean up the Selenium WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            finally:
                self.driver = None
                self.wait = None
    
    def __enter__(self):
        """Context manager entry."""
        self._init_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._cleanup_driver()
    
    def search_plans(
        self,
        query: Optional[str] = None,
        city: Optional[str] = None,
        district: Optional[str] = None,
        plan_area: Optional[str] = None,
        street: Optional[str] = None,
        gush: Optional[str] = None,
        helka: Optional[str] = None,
        block_number: Optional[str] = None,
        parcel_number: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[MavatSearchHit]:
        """Search for plans using Selenium automation.
        
        Args:
            query: Free text search query
            city: City name
            district: District name
            plan_area: Plan area name
            street: Street name
            gush: Gush (block) number
            helka: Helka (parcel) number
            block_number: Block number
            parcel_number: Parcel number
            status: Plan status filter
            limit: Maximum results
            
        Returns:
            List of MavatSearchHit objects
        """
        if not self.driver:
            raise RuntimeError("Driver not initialized. Use context manager or call _init_driver() first.")
        
        try:
            # Navigate to the search page
            print(f"Navigating to: {self.SEARCH_URL}")
            self.driver.get(self.SEARCH_URL)
            
            # Wait for page to load
            time.sleep(3)
            
            # Look for search form elements
            print("Looking for search form...")
            
            # Try to find and click on the "תכניות" (Plans) button first
            try:
                # Wait for any loading spinners to disappear first
                time.sleep(2)
                
                # Try multiple selectors for the plans button
                plans_button = None
                button_selectors = [
                    "//button[contains(text(), 'תכניות')]",
                    "//button[@aria-label='תכניות']",
                    "//button[contains(@class, 'select-tab') and contains(text(), 'תכניות')]",
                    "button[aria-label='תכניות']",
                    "button:contains('תכניות')"
                ]
                
                for selector in button_selectors:
                    try:
                        if selector.startswith("//"):
                            plans_button = self.wait.until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                        else:
                            plans_button = self.wait.until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                        if plans_button:
                            break
                    except:
                        continue
                
                if plans_button:
                    print("Found plans button, clicking it...")
                    # Scroll to element and click
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", plans_button)
                    time.sleep(1)
                    plans_button.click()
                    time.sleep(3)  # Wait for content to load
                else:
                    print("Could not find plans button, continuing with search...")
            except Exception as e:
                print(f"Could not find plans button: {e}")
            
            # Look for search input field
            search_input = None
            input_selectors = [
                "input[name='text']",
                "input[type='text']",
                "input[placeholder*='הקלדת שם']",
                "input[placeholder*='חיפוש']"
            ]
            
            for selector in input_selectors:
                try:
                    search_input = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    print(f"Found search input with selector: {selector}")
                    break
                except:
                    continue
            
            if not search_input:
                print("No search input found, trying direct URL approach...")
                # Try direct URL with query parameters
                search_params = []
                if query:
                    search_params.append(f"text={query}")
                if city:
                    search_params.append(f"city={city}")
                if gush:
                    search_params.append(f"gush={gush}")
                if helka:
                    search_params.append(f"helka={helka}")
                
                if search_params:
                    url = f"{self.SEARCH_URL}?{'&'.join(search_params)}"
                    print(f"Trying direct URL: {url}")
                    self.driver.get(url)
                    time.sleep(3)
            else:
                # Fill search input
                search_text = query or city or "תל אביב"
                print(f"Filling search input with: {search_text}")
                search_input.clear()
                search_input.send_keys(search_text)
                
                # Look for search button
                search_button = None
                button_selectors = [
                    "button:contains('חיפוש')",
                    "input[value*='חיפוש']",
                    "button[type='submit']",
                    "//button[contains(text(), 'חיפוש')]"
                ]
                
                for selector in button_selectors:
                    try:
                        if selector.startswith("//"):
                            search_button = self.driver.find_element(By.XPATH, selector)
                        else:
                            search_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if search_button and search_button.is_displayed():
                            break
                    except:
                        continue
                
                if search_button:
                    print("Found search button, clicking it...")
                    search_button.click()
                    time.sleep(3)
                else:
                    print("No search button found, trying Enter key...")
                    search_input.send_keys(Keys.RETURN)
                    time.sleep(3)
            
            # Wait for results to load
            print("Waiting for search results...")
            time.sleep(3)
            
            # Extract search results
            hits = []
            
            # Look for tables with actual data (not empty rows)
            tables = self.driver.find_elements(By.CSS_SELECTOR, "table")
            print(f"Found {len(tables)} tables on page")
            
            for table_idx, table in enumerate(tables):
                rows = table.find_elements(By.CSS_SELECTOR, "tr")
                print(f"Table {table_idx}: {len(rows)} rows")
                
                if len(rows) > 1:  # More than just header
                    # Check if this table has meaningful data
                    first_data_row = None
                    for row in rows[1:]:  # Skip header
                        cells = row.find_elements(By.CSS_SELECTOR, "td, th")
                        cell_texts = [cell.text.strip() for cell in cells]
                        if any(cell_texts):  # Has non-empty content
                            first_data_row = cell_texts
                            break
                    
                    if first_data_row:
                        print(f"Table {table_idx} has data: {first_data_row}")
                        
                        # Extract data from all rows
                        for row_idx, row in enumerate(rows[1:limit+1]):  # Skip header, limit results
                            try:
                                cells = row.find_elements(By.CSS_SELECTOR, "td, th")
                                cell_texts = [cell.text.strip() for cell in cells]
                                
                                if not any(cell_texts):  # Skip empty rows
                                    continue
                                
                                # Determine plan ID (usually first cell with meaningful content)
                                plan_id = None
                                for cell_text in cell_texts:
                                    if cell_text and (cell_text.isdigit() or len(cell_text) > 3):
                                        plan_id = cell_text
                                        break
                                
                                if not plan_id:
                                    plan_id = f"plan_{table_idx}_{row_idx}"
                                
                                # Use the first non-empty cell as title
                                title = next((text for text in cell_texts if text), None)
                                
                                # Try to identify additional fields based on table structure
                                authority = None
                                jurisdiction = None
                                status = None
                                
                                if len(cell_texts) >= 3:
                                    # Common pattern: ID, Title, Authority, Location, Status
                                    if len(cell_texts) >= 4:
                                        authority = cell_texts[2] if len(cell_texts) > 2 else None
                                    if len(cell_texts) >= 5:
                                        jurisdiction = cell_texts[3] if len(cell_texts) > 3 else None
                                    if len(cell_texts) >= 6:
                                        status = cell_texts[4] if len(cell_texts) > 4 else None
                                
                                hit = MavatSearchHit(
                                    plan_id=plan_id,
                                    title=title,
                                    authority=authority,
                                    jurisdiction=jurisdiction,
                                    status=status,
                                    raw={
                                        "table_index": table_idx,
                                        "row_index": row_idx,
                                        "cell_texts": cell_texts,
                                        "element_html": row.get_attribute("outerHTML")[:500]
                                    }
                                )
                                hits.append(hit)
                                
                            except Exception as e:
                                print(f"Error extracting data from row {row_idx}: {e}")
                                continue
                        
                        if hits:
                            break  # Found results in this table
            
            print(f"Extracted {len(hits)} search results")
            return hits[:limit]
            
        except Exception as e:
            raise RuntimeError(f"Search failed: {e}")
    
    def fetch_pdf(self, plan_number: str) -> bytes:
        """Fetch PDF for a specific plan number.
        
        Args:
            plan_number: The plan number to fetch PDF for
            
        Returns:
            PDF content as bytes
        """
        if not self.driver:
            raise RuntimeError("Driver not initialized. Use context manager or call _init_driver() first.")
        
        try:
            # Navigate to plan page
            plan_url = f"{self.SEARCH_URL}?text={plan_number}"
            print(f"Navigating to plan page: {plan_url}")
            self.driver.get(plan_url)
            time.sleep(3)
            
            # First, try to click on the plans tab to ensure we're looking at plans, not meetings
            try:
                plans_tab = self.driver.find_element(By.XPATH, "//button[contains(text(), 'תכניות') or @aria-label='תכניות']")
                if plans_tab and plans_tab.is_displayed():
                    print("Clicking plans tab to ensure we're viewing plans...")
                    plans_tab.click()
                    time.sleep(2)
            except:
                print("Could not find plans tab, continuing...")
            
            # Look for PDF button/link with more comprehensive selectors
            pdf_button = None
            pdf_selectors = [
                "img[title='הצג PDF']",  # Most common - img elements with PDF title
                "button[title='הצג PDF']",
                "button[title*='PDF']",
                "button:contains('PDF')",
                "button:contains('הצג')",
                "a[href*='pdf']",
                "a[href*='PDF']",
                "//img[@title='הצג PDF']",  # XPath for img elements
                "//button[contains(text(), 'PDF')]",
                "//button[contains(text(), 'הצג')]",
                "//a[contains(text(), 'PDF')]",
                "//button[contains(@title, 'PDF')]",
                "//a[contains(@href, 'pdf')]",
                "//a[contains(@href, 'PDF')]"
            ]
            
            print("Looking for PDF button...")
            for selector in pdf_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            pdf_button = element
                            print(f"Found PDF button with selector: {selector} - Text: '{element.text}'")
                            break
                    
                    if pdf_button:
                        break
                except Exception as e:
                    continue
            
            if not pdf_button:
                # Try to find any clickable element that might lead to PDF
                print("No specific PDF button found, looking for any PDF-related elements...")
                clickable_elements = self.driver.find_elements(By.CSS_SELECTOR, "a, button, img")
                for element in clickable_elements:
                    if element.is_displayed() and element.is_enabled():
                        text = element.text.lower()
                        title = element.get_attribute('title') or ''
                        if any(keyword in text for keyword in ['pdf', 'הצג', 'download', 'הורד']) or \
                           any(keyword in title.lower() for keyword in ['pdf', 'הצג', 'download', 'הורד']):
                            pdf_button = element
                            print(f"Found potential PDF element: '{element.text}' (title: '{title}')")
                            break
            
            if pdf_button:
                print(f"Clicking PDF button: '{pdf_button.text}'")
                try:
                    # Scroll to element and click
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", pdf_button)
                    time.sleep(1)
                    pdf_button.click()
                    time.sleep(5)  # Wait longer for PDF to load
                    
                    # Check if a new tab/window opened
                    if len(self.driver.window_handles) > 1:
                        print("New tab opened, switching to it...")
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        time.sleep(2)
                    
                    # Get the current URL to see if it's a PDF
                    current_url = self.driver.current_url
                    print(f"Current URL after click: {current_url}")
                    
                    if current_url.endswith('.pdf') or 'pdf' in current_url.lower():
                        # Download the PDF content
                        pdf_content = self.driver.page_source.encode('utf-8')
                        print(f"PDF content size: {len(pdf_content)} bytes")
                        return pdf_content
                    else:
                        # Look for PDF content in the page
                        page_source = self.driver.page_source
                        if 'PDF' in page_source or 'application/pdf' in page_source:
                            return page_source.encode('utf-8')
                        else:
                            # Check if we can find any PDF links in the page
                            pdf_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='pdf'], a[href*='PDF']")
                            if pdf_links:
                                print(f"Found {len(pdf_links)} PDF links, trying first one...")
                                pdf_links[0].click()
                                time.sleep(3)
                                return self.driver.page_source.encode('utf-8')
                            else:
                                raise RuntimeError("PDF not found after clicking button")
                except Exception as e:
                    raise RuntimeError(f"Error clicking PDF button: {e}")
            else:
                raise RuntimeError("No PDF button found")
                
        except Exception as e:
            raise RuntimeError(f"Failed to fetch PDF: {e}")
    
    def get_plan_details(self, plan_id: str) -> MavatPlan:
        """Get detailed information for a specific plan.
        
        Args:
            plan_id: The unique identifier of the plan
            
        Returns:
            MavatPlan object with plan details
        """
        if not self.driver:
            raise RuntimeError("Driver not initialized. Use context manager or call _init_driver() first.")
        
        try:
            # Navigate to plan details page
            plan_url = f"{self.SEARCH_URL}?text={plan_id}"
            print(f"Navigating to plan details: {plan_url}")
            self.driver.get(plan_url)
            time.sleep(3)
            
            # Extract plan details from the page
            title_element = None
            title_selectors = ["h1", ".plan-title", ".entity-name", "title"]
            
            for selector in title_selectors:
                try:
                    title_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if title_element and title_element.text.strip():
                        break
                except:
                    continue
            
            plan_name = title_element.text.strip() if title_element else None
            
            return MavatPlan(
                plan_id=plan_id,
                plan_name=plan_name,
                raw={"page_url": plan_url}
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to get plan details: {e}")
    
    def is_accessible(self) -> bool:
        """Check if the Mavat system is accessible.
        
        Returns:
            True if accessible, False otherwise
        """
        if not self.driver:
            try:
                self._init_driver()
            except:
                return False
        
        try:
            self.driver.get(self.BASE_URL)
            return "mavat" in self.driver.title.lower() or "תכנון" in self.driver.title
        except:
            return False


# Backward compatibility
MavatScraper = MavatSeleniumClient
