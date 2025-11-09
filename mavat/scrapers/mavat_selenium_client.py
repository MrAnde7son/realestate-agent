#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mavat Selenium Client

This module provides a Selenium-based client for the Mavat system, following the same
successful pattern used in the Nadlan scraper. Selenium often handles complex JavaScript
interactions better than Playwright for government websites.

Based on the successful approach from: gov/nadlan/scraper_selenium.py
"""

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.keys import Keys
 


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
        self.logger = logging.getLogger(__name__)

    def _wait_for_spinner(self, timeout: float = 15.0) -> None:
        """Wait for the loading spinner overlay to disappear."""
        if not self.driver:
            return

        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, ".ngx-spinner-overlay")
                )
            )
        except TimeoutException:
            # Spinner might remain due to animation glitches; continue anyway
            pass

    def _init_driver(self):
        """Initialize the Selenium WebDriver."""
        if self.driver is None:
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
            
            # Find ChromeDriver path - prefer explicit installation over Selenium Manager
            chromedriver_path = None
            # Check environment variable first
            chromedriver_path = os.environ.get('CHROMEDRIVER_PATH')
            if chromedriver_path and os.path.isfile(chromedriver_path) and os.access(chromedriver_path, os.X_OK):
                logger.debug(f"Using ChromeDriver from CHROMEDRIVER_PATH: {chromedriver_path}")
            else:
                # Check common locations
                common_chromedriver_paths = [
                    '/usr/local/bin/chromedriver',
                    '/usr/bin/chromedriver',
                    '/opt/chromedriver/chromedriver',
                ]
                for path in common_chromedriver_paths:
                    if os.path.isfile(path) and os.access(path, os.X_OK):
                        chromedriver_path = path
                        logger.debug(f"Using ChromeDriver from common location: {chromedriver_path}")
                        break
            
            # Use explicit ChromeDriver path if found, otherwise let Selenium Manager handle it
            if chromedriver_path:
                service = Service(executable_path=chromedriver_path)
            else:
                logger.debug("ChromeDriver not found in common locations, using Selenium Manager")
                service = Service()
            
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
        block: Optional[int] = None,
        parcel: Optional[int] = None,
        district: Optional[str] = None,
        plan_area: Optional[str] = None,
        street: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[MavatSearchHit]:
        """Search for plans using Selenium automation.
        
        Automatically chooses between basic search (for query-only) and advanced search 
        (for specific parameters like city, block, parcel, etc.).
        
        Args:
            query: Free text search query - triggers basic search if only this is provided
            city: City name
            block: Block number  
            parcel: Parcel number
            district: District name
            plan_area: Plan area name
            street: Street name
            status: Status filter
            limit: Maximum results
            
        Returns:
            List of MavatSearchHit objects
        """
        if not self.driver:
            raise RuntimeError("Driver not initialized. Use context manager or call _init_driver() first.")
        
        # Collect all provided parameters
        params = {
            'query': query,
            'city': city,
            'block': block,
            'parcel': parcel,
            'district': district,
            'plan_area': plan_area,
            'street': street,
            'status': status
        }
        
        # Determine which search method to use
        if self._is_advanced_search_needed(**params):
            self.logger.info("Using advanced search due to specific parameters")
            # Remove query from kwargs for advanced search
            advanced_params = {k: v for k, v in params.items() if k != 'query' and v}
            return self._advanced_search(limit=limit, **advanced_params)
        else:
            self.logger.info("Using basic search for query-only search")
            if not query:
                raise ValueError("Query parameter is required for basic search")
            return self._basic_search(query=query, limit=limit)
    
    def _is_advanced_search_needed(self, **kwargs) -> bool:
        """Determine if advanced search is needed based on provided parameters."""
        # Advanced search is needed if any specific parameters other than query are provided
        advanced_params = ['city', 'block', 'parcel', 'district', 'plan_area', 'street', 'status']
        return any(value for param, value in kwargs.items() if param in advanced_params and value)

    def _navigate_to_advanced_search(self) -> None:
        """Navigate to advanced search from the basic search page."""
        self.logger.info("Navigating to advanced search...")
        
        # Wait for page to fully load
        self._wait_for_spinner()
        time.sleep(2)  # Additional wait for dynamic content
        
        # Debug: Check what elements are available on the page
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            self.logger.debug(f"Found {len(buttons)} buttons on page")
            for i, button in enumerate(buttons[:5]):  # Show first 5 buttons
                aria_label = button.get_attribute("aria-label")
                text = button.text.strip()
                class_name = button.get_attribute("class")
                if "חיפוש" in str(aria_label) or "חיפוש" in text or "advanced" in str(aria_label).lower():
                    self.logger.debug(f"Button {i}: aria-label='{aria_label}', text='{text}', class='{class_name}'")
        except Exception as e:
            self.logger.debug(f"Error debugging buttons: {e}")
        
        # Look for the advanced search button/link
        advanced_link_selectors = [
            "button[aria-label='חיפוש מתקדם']",
            "//button[@aria-label='חיפוש מתקדם']",
            "//button[contains(text(), 'חיפוש מתקדם')]",
            "//a[contains(text(), 'חיפוש מתקדם')]",
            "//a[contains(text(), 'advanced')]",
            "a:contains('חיפוש מתקדם')",
            "a:contains('advanced')",
            ".search-link a",
            "[role='link']",
            ".sv3-carousel-control__toggle"
        ]
        
        advanced_link = None
        for selector in advanced_link_selectors:
            try:
                if selector.startswith("//"):
                    advanced_link = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector)),
                        f"Waiting for advanced search element with XPATH: {selector}"
                    )
                else:
                    advanced_link = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector)),
                        f"Waiting for advanced search element with CSS: {selector}"
                    )
                if advanced_link:
                    self.logger.info(f"Found advanced search link with selector: {selector}")
                    self.logger.debug(f"Element tag: {advanced_link.tag_name}, text: '{advanced_link.text}', aria-label: '{advanced_link.get_attribute('aria-label')}'")
                    break
            except Exception as e:
                self.logger.debug(f"Selector '{selector}' failed: {e}")
                continue
        
        if advanced_link:
            try:
                # Scroll to link and click
                self.driver.execute_script("arguments[0].scrollIntoView(true);", advanced_link)
                self._wait_for_spinner()
                advanced_link.click()
                self._wait_for_spinner()
                time.sleep(3)  # Wait for advanced search page to load
                self.logger.info("Successfully navigated to advanced search")
            except Exception as e:
                self.logger.warning(f"Error clicking advanced search link: {e}")
                raise RuntimeError(f"Failed to navigate to advanced search: {e}")
        else:
            # More detailed error message
            page_title = self.driver.title
            current_url = self.driver.current_url
            error_msg = f"Advanced search link not found. Page title: '{page_title}', URL: '{current_url}'"
            self.logger.error(error_msg)
            
            # Try to find any elements with "חיפוש" text
            try:
                elements_with_search = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'חיפוש')]")
                self.logger.debug(f"Found {len(elements_with_search)} elements containing 'חיפוש'")
                for elem in elements_with_search[:3]:
                    self.logger.debug(f"Element: tag={elem.tag_name}, text='{elem.text}', aria-label='{elem.get_attribute('aria-label')}'")
            except Exception as e:
                self.logger.debug(f"Error searching for 'חיפוש' elements: {e}")
            
            raise RuntimeError(error_msg)

    def _enable_dependent_fields(self) -> None:
        """Enable fields that are initially disabled but become enabled after filling block."""
        self.logger.info("Checking for disabled fields that need enabling...")
        
        # Look for disabled fields that might be reactivated
        disabled_fields = [
            "input[name='parcelNumber'][disabled]",
            "input[aria-label='חלקה'][disabled]",
            "input[name='רחוב'][disabled]"
        ]
        
        for selector in disabled_fields:
            try:
                disabled_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                if disabled_field:
                    field_name = disabled_field.get_attribute("name") or disabled_field.get_attribute("aria-label")
                    self.logger.info(f"Found disabled field: {field_name}")
                    
                    # Try to enable it by removing disabled attribute
                    self.driver.execute_script("arguments[0].removeAttribute('disabled');", disabled_field)
                    
                    # Add a change event to trigger any JavaScript listeners
                    self.driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", disabled_field)
                    
                    self.logger.info(f"Attempted to enable field: {field_name}")
            except Exception as e:
                self.logger.debug(f"Error enabling field with selector {selector}: {e}")

    def _click_parent_clickable(self, element) -> None:
        """Try to click parent elements that might be the actual clickable element."""
        try:
            # Find clickable parent elements (button, a, [onclick], etc.)
            parent_element = self.driver.execute_script("""
                let elem = arguments[0];
                let current = elem;
                
                // Look up the DOM tree for clickable parents
                for (let i = 0; i < 5; i++) {
                    if (!current || current === document.body) break;
                    
                    // Check if current element or parent is clickable
                    if (current.tagName === 'BUTTON' || 
                        current.tagName === 'A' ||
                        current.getAttribute('onclick') ||
                        current.getAttribute('role') === 'button' ||
                        current.classList.contains('clickable')) {
                        return current;
                    }
                    current = current.parentElement;
                }
                return elem;
            """, element)
            
            if parent_element and parent_element != element:
                self.logger.info("Found clickable parent element, clicking it...")
                self.driver.execute_script("arguments[0].click();", parent_element)
            else:
                raise Exception("No clickable parent found")
                
        except Exception as e:
            self.logger.debug(f"Parent clickable strategy failed: {e}")
            raise

    def _hide_overlay_and_click(self, element) -> None:
        """Temporarily hide overlays and click the element."""
        try:
            # Hide common overlay elements that might interfere
            hide_script = """
                // Hide common overlays and fixed elements
                const overlays = document.querySelectorAll(
                    '.uk-grid, .fixed, .sticky, .modal-backdrop, .overlay, .popup, ' +
                    '[class*="fixed"], [class*="sticky"], [class*="modal"], [class*="overlay"]'
                );
                
                overlays.forEach(overlay => {
                    if (overlay && !overlay.contains(arguments[0])) {
                        overlay.style.display = 'none';
                    }
                });
                
                // Click the element
                arguments[0].click();
                
                // Restore overlays after a short delay
                setTimeout(() => {
                    overlays.forEach(overlay => {
                        overlay.style.display = '';
                    });
                }, 100);
            """
            
            self.driver.execute_script(hide_script, element)
            self.logger.info("Successfully hid overlays and clicked element")
            
        except Exception as e:
            self.logger.debug(f"Hide overlay strategy failed: {e}")
            raise

    def _fill_advanced_search_form(self, **kwargs) -> None:
        """Fill the advanced search form with provided parameters."""
        self.logger.info("Filling advanced search form...")
        
        # Wait for advanced form to load
        time.sleep(2)
        self._wait_for_spinner()
        
        # Enable disabled fields that depend on block input
        self._enable_dependent_fields()
        
        # Field mappings based on actual HTML structure
        field_mappings = {
            'city': [
                "input[name='ישוב/רשות מקומית']",
                "input[aria-label='ישוב/רשות מקומית']",
                "input[placeholder*='ישוב/רשות']"
            ],
            'block': [
                "input[name='blockNumber']",
                "input[aria-label='גוש']",
                "input[placeholder*='גוש']",
                "input[id='program-number-plans-3']"
            ],
            'parcel': [
                "input[name='parcelNumber']",
                "input[aria-label='חלקה']",
                "input[placeholder*='חלקה']",
                "input[id='program-number-plans-4']"
            ],
            'district': [
                "input[name='מחוז']",
                "input[aria-label='מחוז']",
                "input[placeholder*='מחוז']"
            ],
            'plan_area': [
                "input[name='מרחב תכנון']",
                "input[aria-label='מרחב תכנון']",
                "input[placeholder*='מרחב תכנון']"
            ],
            'street': [
                "input[name='רחוב']",
                "input[aria-label='רחוב']",
                "input[placeholder*='רחוב']"
            ],
            'status': [
                "input[name='סטטוס']",
                "input[aria-label='סטטוס']",
                "input[placeholder*='סטטוס']"
            ]
        }
        
        # Fill each provided field
        for param, value in kwargs.items():
            if not value or param not in field_mappings:
                continue
                
            field_element = None
            for selector in field_mappings[param]:
                try:
                    field_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if field_element and field_element.is_displayed() and field_element.is_enabled():
                        self.logger.info(f"Found {param} field with selector: {selector}")
                        break
                    elif field_element:
                        self.logger.debug(f"Field found but not interactable: {selector}")
                except Exception as e:
                    self.logger.debug(f"Error finding field with selector {selector}: {e}")
                    continue
            
            if field_element:
                try:
                    # Special handling for different field types
                    if 'p-autocomplete' in field_element.get_attribute('class'):
                        # Handle autocomplete fields
                        self.logger.info(f"Handling autocomplete field for {param}")
                        field_element.click()
                        time.sleep(0.5)
                        field_element.clear()
                        field_element.send_keys(str(value))
                        
                        # Try to select from dropdown if it appears
                        try:
                            dropdown_item = self.wait.until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, ".p-autocomplete-item"))
                            )
                            dropdown_item.click()
                            time.sleep(0.5)
                        except:
                            self.logger.debug("No dropdown found, using direct input")
                    
                    elif 'p-calendar' in field_element.get_attribute('class'):
                        # Handle calendar fields  
                        self.logger.info(f"Handling calendar field for {param}")
                        field_element.click()
                        time.sleep(0.5)
                        field_element.send_keys(str(value))
                    
                    elif field_element.tag_name.lower() == 'select':
                        # For select elements, try to find option by text
                        options = field_element.find_elements(By.TAG_NAME, "option")
                        for option in options:
                            if value in option.text or option.get_attribute("value") == value:
                                field_element.click()
                                option.click()
                                break
                    
                    else:
                        # Handle regular input fields
                        self.logger.info(f"Handling regular input field for {param}")
                        
                        # Ensure field is focused and clickable
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", field_element)
                        time.sleep(0.5)
                        
                        # Clear field first
                        field_element.click()
                        time.sleep(0.2)
                        field_element.clear()
                        time.sleep(0.2)
                        
                        # Use JavaScript to set value if regular send_keys fails
                        try:
                            field_element.send_keys(str(value))
                        except Exception as e:
                            self.logger.debug(f"Regular send_keys failed, using JavaScript: {e}")
                            self.driver.execute_script("arguments[0].value = arguments[1];", field_element, str(value))
                            self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", field_element)
                    
                    self.logger.info(f"Successfully filled {param} field with: {value}")
                    time.sleep(0.5)  # Wait between fields
                    
                    # Special case: After filling block, try to enable parcel field
                    if param == 'block' and 'parcel' in kwargs and kwargs['parcel']:
                        self.logger.info("Block filled, attempting to enable parcel field...")
                        try:
                            parcel_field = self.driver.find_element(By.CSS_SELECTOR, "input[name='parcelNumber']")
                            if parcel_field.get_attribute("disabled"):
                                self.driver.execute_script("arguments[0].removeAttribute('disabled');", parcel_field)
                                self.driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", parcel_field)
                                self.logger.info("Parcel field enabled after block input")
                        except Exception as e:
                            self.logger.debug(f"Could not enable parcel field: {e}")
                    
                except Exception as e:
                    self.logger.warning(f"Error filling {param} field: {e}")
            else:
                self.logger.warning(f"Could not find field for parameter: {param}")
                
                # Debug: Show what fields are available
                try:
                    inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    self.logger.debug(f"Available input fields:")
                    for inp in inputs[:10]:  # Show first 10
                        name = inp.get_attribute("name")
                        aria_label = inp.get_attribute("aria-label")
                        placeholder = inp.get_attribute("placeholder")
                        enabled = inp.is_enabled()
                        self.logger.debug(f"  Input: name='{name}', aria-label='{aria_label}', placeholder='{placeholder}', enabled={enabled}")
                except Exception as e:
                    self.logger.debug(f"Error debugging inputs: {e}")

    def _execute_advanced_search(self) -> None:
        """Execute the advanced search by clicking the search button."""
        self.logger.info("Executing advanced search...")
        
        # Wait a bit for the form to be ready
        time.sleep(2)
        
        # Debug: Check for search button containers
        try:
            search_containers = self.driver.find_elements(By.CSS_SELECTOR, ".sv3-save-control__search")
            self.logger.debug(f"Found {len(search_containers)} search control containers")
            for i, container in enumerate(search_containers):
                is_displayed = container.is_displayed()
                container_class = container.get_attribute("class")
                self.logger.debug(f"Container {i}: displayed={is_displayed}, class='{container_class}'")
                
                # Check buttons within this container
                buttons_in_container = container.find_elements(By.TAG_NAME, "button")
                self.logger.debug(f"Container {i} has {len(buttons_in_container)} buttons")
                for j, btn in enumerate(buttons_in_container):
                    btn_text = btn.text.strip()
                    btn_aria_label = btn.get_attribute("aria-label")
                    btn_enabled = btn.is_enabled()
                    btn_displayed = btn.is_displayed()
                    self.logger.debug(f"  Button {j}: text='{btn_text}', aria-label='{btn_aria_label}', enabled={btn_enabled}, displayed={btn_displayed}")
        except Exception as e:
            self.logger.debug(f"Error debugging search containers: {e}")
        
        # Look for search button in advanced search
        search_button_selectors = [
            "button[aria-label='חיפוש']",
            "//button[@aria-label='חיפוש']",
            ".sv3-save-control__search button",
            "//button[contains(text(), 'חיפוש')]",
            "//button[contains(text(), 'חיפה')]",
            "button[type='submit']",
            "input[type='submit']",
            "//*[contains(text(), 'חיף')]",
            ".search-button",
            ".btn-search",
            "[role='button']:contains('חיף')",
            "button.p-button",
            ".p-button"
        ]
        
        search_button = None
        for selector in search_button_selectors:
            try:
                if selector.startswith("//"):
                    search_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector)),
                        f"Looking for search button: {selector}"
                    )
                else:
                    search_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector)),
                        f"Looking for search button: {selector}"
                    )
                if search_button and search_button.is_displayed() and search_button.is_enabled():
                    self.logger.info(f"Found search button with selector: {selector}")
                    break
                else:
                    self.logger.debug(f"Found button but not clickable: {selector}")
            except Exception as e:
                self.logger.debug(f"Search button selector '{selector}' failed: {e}")
                continue
        
        if search_button:
            try:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
                self._wait_for_spinner()
                search_button.click()
                self._wait_for_spinner()
                time.sleep(3)  # Wait for results to load
                self.logger.info("Advanced search executed successfully")
            except Exception as e:
                self.logger.warning(f"Error clicking search button: {e}")
                raise RuntimeError(f"Failed to execute advanced search: {e}")
        else:
            self.logger.warning("No search button found")
            
            # Debug: Show what buttons are available
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                self.logger.debug(f"Available buttons:")
                for i, btn in enumerate(buttons[:10]):  # Show first 10 buttons
                    text = btn.text.strip()
                    enabled = btn.is_enabled()
                    displayed = btn.is_displayed()
                    btn_class = btn.get_attribute("class")
                    self.logger.debug(f"  Button {i}: text='{text}', enabled={enabled}, displayed={displayed}, class='{btn_class}'")
            except Exception as e:
                self.logger.debug(f"Error debugging buttons: {e}")
            
            # Try a direct approach - find any button with "חיפוש" text
            try:
                self.logger.info("Trying direct button search approach...")
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in all_buttons:
                    text_content = btn.text.strip()
                    aria_label = btn.get_attribute("aria-label") or ""
                    if "חיפוש" in text_content or "חיפה" in text_content or "חיפוש" in aria_label:
                        if btn.is_enabled() and btn.is_displayed():
                            self.logger.info(f"Found search button directly: text='{text_content}', aria='{aria_label}'")
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                            btn.click()
                            self._wait_for_spinner()
                            time.sleep(3)
                            self.logger.info("Direct search button click successful")
                            return
            except Exception as e:
                self.logger.warning(f"Direct button search failed: {e}")
            
            # Try pressing Enter key on form as fallback
            try:
                self.logger.info("Trying Enter key on form as fallback")
                form_elements = self.driver.find_elements(By.CSS_SELECTOR, "input:not([disabled]), select:not([disabled])")
                if form_elements:
                    form_elements[-1].send_keys(Keys.RETURN)
                    self._wait_for_spinner()
                    time.sleep(3)
                    self.logger.info("Sent Enter key to form")
                else:
                    self.logger.warning("No form elements found for Enter key")
            except Exception as e:
                self.logger.warning(f"Error executing search via Enter key: {e}")
                raise RuntimeError(f"No search method available: {e}")

    def _basic_search(self, query: str, limit: Optional[int] = None) -> List[MavatSearchHit]:
        """Perform basic search using the simple text input.
        
        Protected method - should only be called via search_plans().
        
        Args:
            query: Free text search query
            limit: Maximum results
            
        Returns:
            List of MavatSearchHit objects
        """
        if not self.driver:
            raise RuntimeError("Driver not initialized. Use context manager or call _init_driver() first.")
        
        try:
            # Navigate to the search page
            self.logger.info(f"Navigating to: {self.SEARCH_URL}")
            self.driver.get(self.SEARCH_URL)

            # Wait for page to load
            self._wait_for_spinner()
            
            # Look for search form elements
            self.logger.info("Looking for search form...")
            
            # Try to find and click on the "תכניות" (Plans) button first
            try:
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
                    self.logger.info("Found plans button, clicking it...")
                    # Scroll to element and click
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", plans_button)
                    self._wait_for_spinner()
                    plans_button.click()
                    self._wait_for_spinner()
                else:
                    self.logger.warning("Could not find plans button, continuing with search...")
            except Exception as e:
                self.logger.warning(f"Could not find plans button: {e}")
            
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
                    self.logger.info(f"Found search input with selector: {selector}")
                    break
                except:
                    continue
            
            if not search_input:
                self.logger.info("No search input found, trying direct URL approach...")
                # Try direct URL with query parameters
                url = f"{self.SEARCH_URL}?text={query}"
                self.logger.info(f"Trying direct URL: {url}")
                self.driver.get(url)
                time.sleep(3)
            else:
                # Fill search input
                self.logger.info(f"Filling search input with: {query}")
                search_input.clear()
                search_input.send_keys(query)
                
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
                    self.logger.info("Found search button, clicking it...")
                    self._wait_for_spinner()
                    search_button.click()
                    self._wait_for_spinner()
                    time.sleep(3)
                else:
                    self.logger.info("No search button found, trying Enter key...")
                    self._wait_for_spinner()
                    search_input.send_keys(Keys.RETURN)
                    self._wait_for_spinner()
                    time.sleep(3)

            # Extract and return results
            return self._extract_search_results(limit)
            
        except Exception as e:
            raise RuntimeError(f"Basic search failed: {e}")

    def _advanced_search(self, limit: Optional[int] = None, **kwargs) -> List[MavatSearchHit]:
        """Perform advanced search using specific form fields.
        
        Protected method - should only be called via search_plans().
        
        Args:
            city: City name
            block: Block number  
            parcel: Parcel number
            district: District name
            plan_area: Plan area name
            street: Street name
            status: Status filter
            limit: Maximum results
            
        Returns:
            List of MavatSearchHit objects
        """
        if not self.driver:
            raise RuntimeError("Driver not initialized. Use context manager or call _init_driver() first.")
        
        try:
            # Navigate to basic search first
            self.logger.info(f"Navigating to: {self.SEARCH_URL}")
            self.driver.get(self.SEARCH_URL)
            self._wait_for_spinner()

            # Navigate to advanced search
            self._navigate_to_advanced_search()
            
            # Fill advanced search form
            self._fill_advanced_search_form(**kwargs)
            
            # Execute the search
            self._execute_advanced_search()

            # Extract and return results
            return self._extract_search_results(limit)
            
        except Exception as e:
            raise RuntimeError(f"Advanced search failed: {e}")

    def _find_show_more_button(self):
        """Locate the 'show more' button if present."""
        if not self.driver:
            return None

        selectors = [
            "div.sv3-results-layout__loadmore_n button",
            "div.sv3-results-layout__loadmore button",
            "button[aria-label='הצג עוד']",
            "button[aria-label*='הצג עוד']",
        ]

        for selector in selectors:
            try:
                candidates = self.driver.find_elements(By.CSS_SELECTOR, selector)
            except Exception:
                candidates = []

            for button in candidates:
                if not button:
                    continue

                text = (button.text or "").strip()
                aria_label = (button.get_attribute("aria-label") or "").strip()

                if "הצג עוד" not in text and "הצג עוד" not in aria_label:
                    continue

                if not button.is_displayed():
                    continue

                if not button.is_enabled():
                    continue

                if button.get_attribute("disabled") is not None:
                    continue

                if button.get_attribute("aria-disabled") in {"true", "1"}:
                    continue

                return button

        # Fallback to searching all buttons and matching by text
        try:
            for button in self.driver.find_elements(By.TAG_NAME, "button"):
                if not button:
                    continue
                text = (button.text or "").strip()
                aria_label = (button.get_attribute("aria-label") or "").strip()
                if "הצג עוד" in text or "הצג עוד" in aria_label:
                    if button.is_displayed() and button.is_enabled():
                        if button.get_attribute("disabled") is None and button.get_attribute("aria-disabled") not in {"true", "1"}:
                            return button
        except Exception:
            pass

        return None

    def _count_loaded_result_rows(self) -> int:
        """Count the number of non-empty result rows in the first data table."""
        if not self.driver:
            return 0

        tables = self.driver.find_elements(By.CSS_SELECTOR, "table")
        for table in tables:
            rows = table.find_elements(By.CSS_SELECTOR, "tr")
            if len(rows) <= 1:
                continue

            data_rows = 0
            for row in rows[1:]:
                cells = row.find_elements(By.CSS_SELECTOR, "td, th")
                if any(cell.text.strip() for cell in cells):
                    data_rows += 1

            if data_rows:
                return data_rows

        return 0

    def _load_more_results_if_needed(self, limit: Optional[int]) -> None:
        """Click the 'show more' button until the desired limit is reached or no more rows exist."""
        if not self.driver:
            return

        # Treat None as unlimited results
        target = limit if limit and limit > 0 else float("inf")

        current_count = self._count_loaded_result_rows()
        max_attempts = 10
        attempts = 0

        self.logger.debug(f"Initial result rows loaded: {current_count}, target: {target}")

        while current_count < target:
            button = self._find_show_more_button()
            if not button:
                self.logger.debug("No 'show more' button found or it is disabled.")
                break

            attempts += 1
            if attempts > max_attempts:
                self.logger.warning("Reached maximum 'show more' attempts; stopping.")
                break

            self.logger.info("Clicking 'show more' to load additional results...")

            try:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", button
                )
            except Exception:
                pass

            try:
                button.click()
            except (ElementClickInterceptedException, StaleElementReferenceException):
                try:
                    self.driver.execute_script("arguments[0].click();", button)
                except Exception as e:
                    self.logger.debug(f"JavaScript click on 'show more' failed: {e}")
                    break
            except Exception as e:
                self.logger.debug(f"Click on 'show more' failed: {e}")
                try:
                    self.driver.execute_script("arguments[0].click();", button)
                except Exception as js_error:
                    self.logger.debug(f"Fallback JavaScript click failed: {js_error}")
                    break

            self._wait_for_spinner()
            time.sleep(2)

            wait_timeout = min(self.timeout, 10)
            try:
                WebDriverWait(self.driver, wait_timeout).until(
                    lambda _: self._count_loaded_result_rows() > current_count
                )
            except TimeoutException:
                new_count = self._count_loaded_result_rows()
                if new_count <= current_count:
                    self.logger.debug("No additional rows loaded after 'show more' click.")
                    break

            current_count = self._count_loaded_result_rows()
            self.logger.debug(f"'Show more' attempt {attempts} loaded {current_count} rows.")

    def _extract_search_results(self, limit: Optional[int]) -> List[MavatSearchHit]:
        """Extract search results from the current page.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of MavatSearchHit objects
        """
        self.logger.info("Extracting search results...")
        time.sleep(3)
        self._wait_for_spinner()

        if limit is not None and limit <= 0:
            return []

        target_count = limit if limit and limit > 0 else None
        self._load_more_results_if_needed(target_count)

        # Extract search results
        hits = []
        
        # Look for tables with actual data (not empty rows)
        tables = self.driver.find_elements(By.CSS_SELECTOR, "table")
        self.logger.info(f"Found {len(tables)} tables on page")
        
        for table_idx, table in enumerate(tables):
            rows = table.find_elements(By.CSS_SELECTOR, "tr")
            self.logger.debug(f"Table {table_idx}: {len(rows)} rows")
            
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
                    self.logger.debug(f"Table {table_idx} has data: {first_data_row}")
                    
                    # Extract data from all rows
                    for row_idx, row in enumerate(rows[1:]):  # Skip header rows
                        try:
                            cells = row.find_elements(By.CSS_SELECTOR, "td, th")
                            cell_texts = [cell.text.strip() for cell in cells]
                            
                            if not any(cell_texts):  # Skip empty rows
                                continue
                            
                            # Determine plan ID (usually first cell with meaningful content)
                            plan_id = cell_texts[0] if cell_texts else None
                            plan_name = cell_texts[1] if len(cell_texts) > 1 else None

                            if not plan_id:
                                plan_id = next((text for text in cell_texts if text), None)
                            if not plan_id:
                                plan_id = f"plan_{table_idx}_{row_idx}"

                            if not plan_name:
                                plan_name = next(
                                    (text for idx, text in enumerate(cell_texts) if idx != 0 and text),
                                    None
                                )

                            title = plan_name or plan_id

                            # Try to identify additional fields based on table structure
                            authority = cell_texts[2] if len(cell_texts) > 2 else None
                            jurisdiction = cell_texts[3] if len(cell_texts) > 3 else None
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
                                    "plan_name": plan_name,
                                    "element_html": row.get_attribute("outerHTML")[:500]
                                }
                            )
                            hits.append(hit)

                            if target_count and len(hits) >= target_count:
                                return hits[:target_count]
                            
                        except Exception as e:
                            self.logger.warning(f"Error extracting data from row {row_idx}: {e}")
                            continue
                    
                    if hits:
                        break  # Found results in this table
        
        self.logger.info(f"Extracted {len(hits)} search results")
        if target_count:
            return hits[:target_count]
        return hits

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
            self.logger.info(f"Navigating to plan page: {plan_url}")
            self.driver.get(plan_url)
            time.sleep(3)
            
            # First, try to click on the plans tab to ensure we're looking at plans, not meetings
            try:
                plans_tab = self.driver.find_element(By.XPATH, "//button[contains(text(), 'תכניות') or @aria-label='תכניות']")
                if plans_tab and plans_tab.is_displayed():
                    self.logger.info("Clicking plans tab to ensure we're viewing plans...")
                    plans_tab.click()
                    time.sleep(2)
            except:
                self.logger.warning("Could not find plans tab, continuing...")
            
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
            
            self.logger.info("Looking for PDF button...")
            for selector in pdf_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            pdf_button = element
                            self.logger.info(f"Found PDF button with selector: {selector} - Text: '{element.text}'")
                            break
                    
                    if pdf_button:
                        break
                except Exception as e:
                    continue
            
            if not pdf_button:
                # Try to find any clickable element that might lead to PDF
                self.logger.info("No specific PDF button found, looking for any PDF-related elements...")
                clickable_elements = self.driver.find_elements(By.CSS_SELECTOR, "a, button, img")
                for element in clickable_elements:
                    if element.is_displayed() and element.is_enabled():
                        text = element.text.lower()
                        title = element.get_attribute('title') or ''
                        if any(keyword in text for keyword in ['pdf', 'הצג', 'download', 'הורד']) or \
                           any(keyword in title.lower() for keyword in ['pdf', 'הצג', 'download', 'הורד']):
                            pdf_button = element
                            self.logger.info(f"Found potential PDF element: '{element.text}' (title: '{title}')")
                            break
            
            if pdf_button:
                self.logger.info(f"Clicking PDF button: '{pdf_button.text}'")
                try:
                    # Scroll to element and click with improved error handling
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", pdf_button)
                    time.sleep(1)
                    
                    # Try multiple click strategies to handle overlay issues
                    click_successful = False
                    click_strategies = [
                        ("Direct click", lambda: pdf_button.click()),
                        ("JavaScript click", lambda: self.driver.execute_script("arguments[0].click();", pdf_button)),
                        ("Actions click", lambda: self.driver.execute_script(
                            "arguments[0].dispatchEvent(new MouseEvent('click', { bubbles: true }));", 
                            pdf_button
                        )),
                        ("Parent clickable element", lambda: self._click_parent_clickable(pdf_button)),
                        ("Hide overlay and click", lambda: self._hide_overlay_and_click(pdf_button))
                    ]
                    
                    for strategy_name, click_method in click_strategies:
                        try:
                            self.logger.info(f"Trying {strategy_name}...")
                            click_method()
                            click_successful = True
                            self.logger.info(f"PDF button click successful with {strategy_name}")
                            break
                        except Exception as e:
                            self.logger.debug(f"{strategy_name} failed: {e}")
                            continue
                    
                    if not click_successful:
                        raise RuntimeError("All click strategies failed")
                        
                    time.sleep(5)  # Wait longer for PDF to load
                    
                    # Check if a new tab/window opened
                    if len(self.driver.window_handles) > 1:
                        self.logger.info("New tab opened, switching to it...")
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        time.sleep(2)
                    
                    # Get the current URL to see if it's a PDF
                    current_url = self.driver.current_url
                    self.logger.info(f"Current URL after click: {current_url}")
                    
                    if current_url.endswith('.pdf') or 'pdf' in current_url.lower():
                        # Download the PDF content
                        pdf_content = self.driver.page_source.encode('utf-8')
                        self.logger.info(f"PDF content size: {len(pdf_content)} bytes")
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
                                self.logger.info(f"Found {len(pdf_links)} PDF links, trying first one...")
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
            self.logger.info(f"Navigating to plan details: {plan_url}")
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

if __name__ == "__main__":
    with MavatSeleniumClient(headless=False) as client:
            hits = client.search_plans(block=6336)
            length = len(hits)
            print(f"Found {length} hits")
