#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mavat Playwright Client

This module provides a Playwright-based client for the Mavat system that can handle
captcha validation and PDF downloads by automating browser interactions.

Based on the approach from: https://github.com/nirfadel/MCP-Hackathon/blob/main/serverb.py
"""

import io
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote

from playwright.sync_api import sync_playwright, Browser, Page, Response


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


class MavatPlaywrightClient:
    """Playwright-based client for the Mavat system."""
    
    BASE_URL = "https://mavat.iplan.gov.il"
    SEARCH_URL = f"{BASE_URL}/SV3"
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """Initialize the Playwright client.
        
        Args:
            headless: Whether to run browser in headless mode
            timeout: Default timeout for operations in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._playwright = None
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def start(self):
        """Start the Playwright browser and create a new page."""
        try:
            self._playwright = sync_playwright().start()
            self.browser = self._playwright.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            self.page = self.browser.new_page()
            self.page.set_default_timeout(self.timeout)
            
            # Set user agent and other headers
            self.page.set_extra_http_headers({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,he-IL;q=0.8,he;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            })
            
        except Exception as e:
            raise RuntimeError(f"Failed to start Playwright browser: {e}")
    
    def close(self):
        """Close the browser and cleanup resources."""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass  # Ignore cleanup errors
        finally:
            self.page = None
            self.browser = None
            self._playwright = None
    
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
        """Search for plans using Playwright automation.
        
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
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first or use context manager.")
        
        try:
            # Navigate to search page
            search_params = []
            if query:
                search_params.append(f"text={quote(query)}")
            if city:
                search_params.append(f"city={quote(city)}")
            if gush:
                search_params.append(f"gush={gush}")
            if helka:
                search_params.append(f"helka={helka}")
            
            url = self.SEARCH_URL
            if search_params:
                url += "?" + "&".join(search_params)
            
            print(f"Navigating to: {url}")
            self.page.goto(url, wait_until="networkidle")
            
            # Wait for search results to load
            time.sleep(2)
            
            # Try to extract search results from the page
            # This is a simplified extraction - in practice, you'd need to
            # analyze the actual page structure
            hits = []
            
            # Look for plan elements on the page
            try:
                # Wait for results to appear
                self.page.wait_for_selector(".result-item, .plan-item, [data-plan-id]", timeout=10000)
                
                # Extract plan information
                plan_elements = self.page.query_selector_all(".result-item, .plan-item, [data-plan-id]")
                
                for element in plan_elements[:limit]:
                    try:
                        plan_id = element.get_attribute("data-plan-id") or element.get_attribute("id") or "unknown"
                        title = element.query_selector("h3, .title, .plan-title")
                        title_text = title.inner_text() if title else None
                        
                        hit = MavatSearchHit(
                            plan_id=plan_id,
                            title=title_text,
                            raw={"element_html": element.inner_html()}
                        )
                        hits.append(hit)
                    except Exception as e:
                        print(f"Error extracting plan data: {e}")
                        continue
                        
            except Exception as e:
                print(f"Could not extract search results: {e}")
                # Return empty results rather than failing
                pass
            
            return hits
            
        except Exception as e:
            raise RuntimeError(f"Search failed: {e}")
    
    def fetch_pdf(self, plan_number: str) -> bytes:
        """Fetch PDF for a specific plan number.
        
        Args:
            plan_number: The plan number to fetch PDF for
            
        Returns:
            PDF content as bytes
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first or use context manager.")
        
        try:
            pdf: bytes | None = None
            
            def response_handler(response: Response):
                nonlocal pdf
                if "application/pdf" in response.headers.get("content-type", ""):
                    pdf = response.body()
            
            # Set up response handler
            self.page.on("response", response_handler)
            
            # Navigate to plan page
            plan_url = f"{self.SEARCH_URL}?text={plan_number}"
            self.page.goto(plan_url, wait_until="networkidle")
            
            # Wait for page to load
            time.sleep(2)
            
            # Look for PDF button and click it
            try:
                # Try different possible selectors for the PDF button
                pdf_selectors = [
                    'button[title="הצג PDF"]',
                    'button:has-text("PDF")',
                    'a[href*="pdf"]',
                    '.pdf-button',
                    '[data-action="pdf"]'
                ]
                
                pdf_button = None
                for selector in pdf_selectors:
                    try:
                        pdf_button = self.page.wait_for_selector(selector, timeout=5000)
                        if pdf_button:
                            break
                    except:
                        continue
                
                if pdf_button:
                    pdf_button.click()
                    # Wait for PDF to load
                    time.sleep(3)
                else:
                    raise RuntimeError("PDF button not found on page")
                    
            except Exception as e:
                print(f"Could not find PDF button: {e}")
                # Try to find any link that might lead to PDF
                links = self.page.query_selector_all("a[href*='pdf'], a[href*='PDF']")
                if links:
                    links[0].click()
                    time.sleep(3)
                else:
                    raise RuntimeError("No PDF link found")
            
            if pdf is None:
                raise RuntimeError("PDF not found - no PDF response captured")
            
            return pdf
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch PDF: {e}")
    
    def get_plan_details(self, plan_id: str) -> MavatPlan:
        """Get detailed information for a specific plan.
        
        Args:
            plan_id: The unique identifier of the plan
            
        Returns:
            MavatPlan object with plan details
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first or use context manager.")
        
        try:
            # Navigate to plan details page
            plan_url = f"{self.SEARCH_URL}?text={plan_id}"
            self.page.goto(plan_url, wait_until="networkidle")
            
            # Wait for page to load
            time.sleep(2)
            
            # Extract plan details from the page
            # This is a simplified extraction - you'd need to analyze the actual page structure
            title_element = self.page.query_selector("h1, .plan-title")
            plan_name = title_element.inner_text() if title_element else None
            
            plan = MavatPlan(
                plan_id=plan_id,
                plan_name=plan_name,
                raw={"page_url": plan_url}
            )
            
            return plan
            
        except Exception as e:
            raise RuntimeError(f"Failed to get plan details: {e}")
    
    def is_accessible(self) -> bool:
        """Check if the Mavat system is accessible.
        
        Returns:
            True if accessible, False otherwise
        """
        if not self.page:
            try:
                self.start()
            except:
                return False
        
        try:
            self.page.goto(self.BASE_URL, timeout=10000)
            return True
        except:
            return False


# Backward compatibility
MavatScraper = MavatPlaywrightClient
