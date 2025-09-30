#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mavat Selenium Client (stable rewrite)

This module implements a Selenium-based client for interacting with the
Mavat SV3 planning information system.  It provides two search modes:

* Basic search – a free‑text search that accepts plan numbers, names,
  or municipal descriptors.  It populates the single text box on the
  SV3 landing page and clicks the search button.

* Advanced search – a structured search that accepts cadastral
  parameters such as block (גוש) and parcel (חלקה), along with
  optional status and city filters.  It opens the "חיפוש מתקדם" panel,
  fills out the relevant fields, and submits the form.

The client supports context manager usage to ensure the Selenium
WebDriver is started and cleaned up appropriately.  Parsing of
results is best‑effort: it examines tables on the results page and
extracts common columns such as plan ID, title, status, authority,
and location.  Callers can override or extend this logic as needed.

Example
-------

```
from mavat_selenium_client import MavatSeleniumClient

with MavatSeleniumClient(headless=True) as client:
    # Free‑text search
    hits = client.search_plans(query="תל אביב", limit=10)
    for hit in hits:
        print(hit.plan_id, hit.title)

    # Cadastral search
    hits = client.search_plans(block="6638", parcel="1", city="תל אביב")
    for hit in hits:
        print(hit.plan_id, hit.title)

    # Fetch plan details
    if hits:
        details = client.get_plan_details(hits[0].plan_id)
        print(details)
```

"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
)
from webdriver_manager.chrome import ChromeDriverManager


@dataclass
class MavatSearchHit:
    """Represents a single search result returned by Mavat."""
    plan_id: str
    title: Optional[str] = None
    status: Optional[str] = None
    authority: Optional[str] = None
    jurisdiction: Optional[str] = None
    entity_number: Optional[str] = None
    approval_date: Optional[str] = None
    status_date: Optional[str] = None
    url: Optional[str] = None
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
    url: Optional[str] = None
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
    """Selenium‑based client for the Mavat SV3 planning information system."""

    BASE_URL = "https://mavat.iplan.gov.il"
    SEARCH_URL = f"{BASE_URL}/SV3"

    def __init__(self, timeout: float = 30.0, headless: bool = True) -> None:
        """Initialise the Mavat client.

        Parameters
        ----------
        timeout: float, optional
            How long to wait for page loads and element searches.
        headless: bool, optional
            Whether to run Chrome in headless mode.  The default is True.
        """
        self.timeout = timeout
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None

    # ------------------------------------------------------------------
    # WebDriver lifecycle
    # ------------------------------------------------------------------
    def _init_driver(self) -> None:
        if self.driver is not None:
            return
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        if self.headless:
            # Use the new headless mode introduced in newer Chromes.  It
            # better handles popups and downloads than the legacy flag.
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1366,900")
        options.add_argument("--lang=he-IL")
        # Present ourselves as a normal Chrome on Windows
        options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/124.0.0.0 Safari/537.36'
        )
        # Hide webdriver flag from JavaScript checks
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_page_load_timeout(self.timeout)
        self.wait = WebDriverWait(self.driver, self.timeout)
        # Remove navigator.webdriver property to avoid detection
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

    def _cleanup_driver(self) -> None:
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            finally:
                self.driver = None
                self.wait = None

    def __enter__(self) -> 'MavatSeleniumClient':
        self._init_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._cleanup_driver()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _wait_for_spinner(self, timeout: Optional[float] = None) -> None:
        """Wait until the global spinner overlay disappears.

        Some pages in Mavat display a full‑screen spinner while loading
        results.  This method waits up to ``timeout`` seconds (or the
        client's configured timeout) for the spinner to become invisible.
        If the spinner remains, the method returns without raising.
        """
        if not self.driver:
            return
        max_time = timeout or self.timeout
        try:
            WebDriverWait(self.driver, max_time).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".ngx-spinner-overlay"))
            )
        except TimeoutException:
            # Spinner can stick; continue anyway
            pass

    def _safe_click(self, element: Optional[webdriver.remote.webelement.WebElement]) -> None:
        """Click an element if it exists and is interactable.

        If ``element`` is None or the click fails, the exception is
        suppressed.  This helper prevents accidents where None is
        accidentally clicked.
        """
        if not element:
            return
        try:
            self.wait.until(EC.element_to_be_clickable(element))
            element.click()
        except Exception:
            try:
                # fallback to JavaScript click
                self.driver.execute_script("arguments[0].click();", element)
            except Exception:
                pass

    def _scroll_into_view(self, element: Optional[webdriver.remote.webelement.WebElement]) -> None:
        """Scroll the page so that ``element`` is visible in the viewport."""
        if not element:
            return
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", element
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Accessibility
    # ------------------------------------------------------------------
    def is_accessible(self) -> bool:
        """Return True if the Mavat system loads successfully.

        This method performs a simple GET of ``BASE_URL`` and checks for
        expected words in the page title.  If the page fails to load or
        the title does not contain "mavat" or "מידע", the method
        returns False.
        """
        try:
            if not self.driver:
                self._init_driver()
            self.driver.get(self.BASE_URL)
            # Wait a short time to allow the page title to stabilise
            time.sleep(1.5)
            title = (self.driver.title or "").lower()
            return ("mavat" in title) or ("מידע" in title) or ("תכנון" in title)
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Search functions
    # ------------------------------------------------------------------
    def search_plans(
        self,
        query: Optional[str] = None,
        city: Optional[str] = None,
        district: Optional[str] = None,
        plan_area: Optional[str] = None,
        street: Optional[str] = None,
        block: Optional[str] = None,
        parcel: Optional[str] = None,
        block_number: Optional[str] = None,
        parcel_number: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> List[MavatSearchHit]:
        """Search for plans using the Mavat web interface.

        This convenience method chooses between basic and advanced
        searches based on the provided arguments.  If ``query`` or
        ``city`` is supplied, a basic free‑text search is performed.
        Otherwise, a cadastral search is attempted using the block and
        parcel numbers (gush/chelka).  Unrecognised or unsupported
        parameters are ignored.

        Parameters
        ----------
        query: str, optional
            Free‑text search term (plan number, name, authority, etc.).
        city: str, optional
            City name for free‑text search; if provided it is used as
            the search term when ``query`` is not supplied.
        block: str, optional
            Alias for ``block_number`` for backward compatibility.
        parcel: str, optional
            Alias for ``parcel_number``.
        block_number: str, optional
            Cadastral block (גוש) number for advanced search.
        parcel_number: str, optional
            Cadastral parcel (חלקה) number for advanced search.
        status: str, optional
            Human‑readable status label (e.g. "מופקדת"), used as a
            filter in advanced search.  If supplied it is used to
            click the corresponding checkbox in the search panel.
        limit: int, optional
            Maximum number of search results to return.

        Returns
        -------
        List[MavatSearchHit]
            A list of search hits.  Each hit contains common fields
            extracted from the results table.  Unparsed fields are
            stored in the ``raw`` attribute.
        """
        if not self.driver:
            raise RuntimeError(
                "Driver not initialized. Use context manager or call __enter__() first."
            )

        # Normalise parameter names
        gush = block_number or block
        chelka = parcel_number or parcel
        # Determine search mode: use basic if a text term or city is supplied
        if query or city:
            search_term = query or city
            return self._search_basic(search_term, limit=limit)
        # Fallback to advanced search using cadastral parameters
        return self._search_advanced(
            gush=gush,
            chelka=chelka,
            statuses=[status] if status else None,
            city=city,
            limit=limit,
        )

    # ------------------------------------------------------------------
    # Basic search implementation
    # ------------------------------------------------------------------
    def _search_basic(self, search_term: str, limit: int = 20) -> List[MavatSearchHit]:
        """Perform a free‑text search on the SV3 landing page.

        ``search_term`` must contain at least three characters; shorter
        values will raise a ValueError.
        """
        if not search_term or len(search_term.strip()) < 3:
            raise ValueError("Basic search requires a term of at least 3 characters")

        # Load the search page
        self.driver.get(self.SEARCH_URL)
        self._wait_for_spinner()

        # Locate the input box; the SV3 basic search uses id "sv3-search__input"
        try:
            input_box = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#sv3-search__input"))
            )
        except TimeoutException:
            raise RuntimeError("Could not locate basic search input field")

        input_box.clear()
        input_box.send_keys(search_term.strip())

        # Locate the submit button; the button inside .sv3-search__submit triggers search
        try:
            submit_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".sv3-search__submit button"))
            )
        except TimeoutException:
            raise RuntimeError("Could not locate basic search submit button")

        self._safe_click(submit_btn)
        # Wait for results; spinner hides when done
        self._wait_for_spinner()
        # Additional small wait to ensure tables render
        time.sleep(1.0)
        return self._parse_results(limit=limit)

    # ------------------------------------------------------------------
    # Advanced search implementation
    # ------------------------------------------------------------------
    def _open_advanced_panel(self) -> None:
        """Ensure the advanced search panel is open.

        On the SV3 landing page there is a link labelled "חיפוש מתקדם"
        underneath the basic search bar.  This helper clicks the link
        if found.  If the link is not present, it silently returns.
        """
        # We need to be on the search page
        self.driver.get(self.SEARCH_URL)
        self._wait_for_spinner()
        try:
            adv_link = self.driver.find_element(By.CSS_SELECTOR, ".search-link a")
            self._safe_click(adv_link)
            # Allow any animations to finish
            time.sleep(0.5)
            self._wait_for_spinner()
        except NoSuchElementException:
            pass

    def _search_advanced(
        self,
        gush: Optional[str] = None,
        chelka: Optional[str] = None,
        statuses: Optional[List[str]] = None,
        city: Optional[str] = None,
        limit: int = 20,
    ) -> List[MavatSearchHit]:
        """Perform a cadastral search using the advanced search form.

        Parameters
        ----------
        gush: str, optional
            The cadastral block number (גוש).
        chelka: str, optional
            The cadastral parcel number (חלקה).
        statuses: List[str], optional
            List of status labels to check in the advanced form (e.g.
            ["מופקדת", "מאושרת"]).  If None, no status filtering is
            performed.
        city: str, optional
            City name to provide additional context when filling the form.
        limit: int, optional
            Maximum number of results to return.

        Returns
        -------
        List[MavatSearchHit]
            A list of search hits parsed from the results.
        """
        # Open advanced panel
        self._open_advanced_panel()

        # Fill block and parcel fields using label heuristics.  In SV3
        # advanced search, the labels often include the Hebrew words
        # "גוש" (block) and "חלקה" (parcel).  We'll search for
        # corresponding input siblings.
        def set_text_by_label(label_contains: str, value: Optional[str]) -> None:
            if not value:
                return
            xpath = f"//label[contains(normalize-space(.), '{label_contains}')]/following::input[1]"
            try:
                el = self.driver.find_element(By.XPATH, xpath)
                self._scroll_into_view(el)
                el.clear()
                el.send_keys(value)
            except NoSuchElementException:
                # If we can't find by label, try fallback IDs from earlier versions
                fallback_ids = {
                    'גוש': ['#Gush', '#blockNumber'],
                    'חלקה': ['#Chelka', '#parcelNumber'],
                }
                for css in fallback_ids.get(label_contains, []):
                    try:
                        el = self.driver.find_element(By.CSS_SELECTOR, css)
                        self._scroll_into_view(el)
                        el.clear()
                        el.send_keys(value)
                        return
                    except NoSuchElementException:
                        continue

        set_text_by_label('גוש', gush)
        set_text_by_label('חלקה', chelka)

        # If a city is provided, attempt to fill it into a city autocomplete
        if city:
            try:
                city_input = self.driver.find_element(By.XPATH, "//label[contains(., 'יישוב')]/following::input[1]")
                self._scroll_into_view(city_input)
                city_input.clear()
                city_input.send_keys(city)
                # Press enter to select the first suggestion
                city_input.send_keys(Keys.ENTER)
            except NoSuchElementException:
                pass

        # Check status checkboxes if requested
        if statuses:
            for label in statuses:
                try:
                    cb_label = self.driver.find_element(By.XPATH, f"//label[contains(normalize-space(.), '{label}')]")
                    self._scroll_into_view(cb_label)
                    self._safe_click(cb_label)
                except NoSuchElementException:
                    continue

        # Locate and click the search button within the advanced panel.  We look
        # for a button with text "חיפוש" that appears after the form.
        search_btn = None
        try:
            search_btn = self.driver.find_element(By.XPATH, "//button[contains(normalize-space(.), 'חיפוש')]")
        except NoSuchElementException:
            pass
        # As a fallback, click the main submit button used by basic search
        if not search_btn:
            try:
                search_btn = self.driver.find_element(By.CSS_SELECTOR, ".sv3-search__submit button")
            except NoSuchElementException:
                pass
        self._safe_click(search_btn)
        # Wait for results
        self._wait_for_spinner()
        time.sleep(1.0)
        return self._parse_results(limit=limit)

    # ------------------------------------------------------------------
    # Result parsing
    # ------------------------------------------------------------------
    def _parse_results(self, limit: int = 20) -> List[MavatSearchHit]:
        """Parse search results from the results page.

        The Mavat results page generally renders one or more tables.  This
        method iterates through those tables and extracts text from each
        row.  It attempts to map columns to attributes using simple
        heuristics: the first non‑empty cell becomes the title, the
        second becomes the authority, the third becomes the location,
        and the fourth becomes the status.  Additional information is
        stored in the ``raw`` dict.
        """
        hits: List[MavatSearchHit] = []
        if not self.driver:
            return hits

        # Some result pages use tables; others use cards.  Try tables first.
        tables = self.driver.find_elements(By.CSS_SELECTOR, "table")
        for table_idx, table in enumerate(tables):
            try:
                rows = table.find_elements(By.CSS_SELECTOR, "tr")
            except StaleElementReferenceException:
                continue
            if len(rows) <= 1:
                continue  # skip if only header or empty

            headers: List[str] = []
            try:
                headers = [h.text.strip() for h in rows[0].find_elements(By.CSS_SELECTOR, "th, td")]
            except StaleElementReferenceException:
                pass
            for row_idx, row in enumerate(rows[1:], start=1):
                try:
                    cells = row.find_elements(By.CSS_SELECTOR, "td, th")
                except StaleElementReferenceException:
                    continue
                cell_texts = [c.text.strip() for c in cells]
                if not any(cell_texts):
                    continue
                # Determine plan ID and title
                plan_id: Optional[str] = None
                title: Optional[str] = None
                for val in cell_texts:
                    if val and not title:
                        title = val
                    if val and (val.isdigit() or len(val) > 3):
                        # use first significant token as plan id candidate
                        plan_id = val
                        break
                if not plan_id:
                    plan_id = f"row_{table_idx}_{row_idx}"
                # Map other columns based on position or header keywords
                authority: Optional[str] = None
                jurisdiction: Optional[str] = None
                status: Optional[str] = None
                if len(cell_texts) >= 3:
                    # Common pattern: [ID, Title, Authority, Location, Status]
                    if len(cell_texts) > 2:
                        authority = cell_texts[2]
                    if len(cell_texts) > 3:
                        jurisdiction = cell_texts[3]
                    if len(cell_texts) > 4:
                        status = cell_texts[4]
                # See if there is a clickable link in the row (plan URL)
                link_href: Optional[str] = None
                try:
                    link = row.find_element(By.CSS_SELECTOR, "a")
                    link_href = link.get_attribute("href")
                except NoSuchElementException:
                    pass
                hits.append(
                    MavatSearchHit(
                        plan_id=plan_id,
                        title=title,
                        authority=authority,
                        jurisdiction=jurisdiction,
                        status=status,
                        url=link_href,
                        raw={
                            "headers": headers,
                            "cells": cell_texts,
                            "table_index": table_idx,
                            "row_index": row_idx,
                        },
                    )
                )
                if len(hits) >= limit:
                    return hits

        # If no tables found, try card‐style results
        if not hits:
            cards = self.driver.find_elements(By.CSS_SELECTOR, "div.uk-card")
            for idx, card in enumerate(cards):
                text = card.text.strip()
                if not text:
                    continue
                lines = text.splitlines()
                plan_id = lines[0] if lines else f"card_{idx}"
                title = lines[1] if len(lines) > 1 else plan_id
                link_href: Optional[str] = None
                try:
                    link = card.find_element(By.CSS_SELECTOR, "a")
                    link_href = link.get_attribute("href")
                except NoSuchElementException:
                    pass
                hits.append(
                    MavatSearchHit(
                        plan_id=plan_id,
                        title=title,
                        url=link_href,
                        raw={"card_text": text},
                    )
                )
                if len(hits) >= limit:
                    break
        return hits

    # ------------------------------------------------------------------
    # Plan details and PDF
    # ------------------------------------------------------------------
    def get_plan_details(self, plan_id: str) -> MavatPlan:
        """Retrieve basic details for a specific plan.

        The method navigates to the plan by performing a basic search
        using the ``plan_id`` as the query, then selecting the first
        result and scraping the title from the details page.  The
        returned ``MavatPlan`` includes only a few fields; callers can
        access the entire raw HTML via the ``raw`` attribute if
        necessary.  If no results are found, a ``RuntimeError`` is
        raised.
        """
        if not self.driver:
            raise RuntimeError(
                "Driver not initialized. Use context manager or call __enter__() first."
            )
        # Search for the plan id
        hits = self._search_basic(plan_id, limit=1)
        if not hits:
            raise RuntimeError(f"No results found for plan identifier: {plan_id}")
        first = hits[0]
        # Navigate to the plan details page
        if first.url:
            self.driver.get(first.url)
        else:
            # Fallback: click the first result row
            self._open_first_result()
        self._wait_for_spinner()
        time.sleep(0.8)
        # Extract the plan name from typical locations
        plan_name: Optional[str] = None
        try:
            candidates = self.driver.find_elements(By.XPATH, "//h1 | //h2 | //div[contains(@class,'title')] | //div[contains(@class,'plan-title')]")
            for c in candidates:
                txt = c.text.strip()
                if txt:
                    plan_name = txt
                    break
        except Exception:
            pass
        return MavatPlan(
            plan_id=plan_id,
            plan_name=plan_name,
            url=self.driver.current_url,
            raw={"url": self.driver.current_url},
        )

    def _open_first_result(self) -> None:
        """Click the first result row on the results page.

        This helper is used when we do not have a direct link to a plan
        details page.  It attempts to click the first row in the first
        table or, if no tables exist, the first card.  Exceptions are
        ignored.
        """
        try:
            tables = self.driver.find_elements(By.CSS_SELECTOR, "table")
            for table in tables:
                rows = table.find_elements(By.CSS_SELECTOR, "tr")
                if len(rows) > 1:
                    first_row = rows[1]
                    try:
                        link = first_row.find_element(By.CSS_SELECTOR, "a")
                        self._scroll_into_view(link)
                        self._safe_click(link)
                    except NoSuchElementException:
                        self._scroll_into_view(first_row)
                        self._safe_click(first_row)
                    self._wait_for_spinner()
                    time.sleep(0.5)
                    return
        except Exception:
            pass
        # fallback to cards
        try:
            cards = self.driver.find_elements(By.CSS_SELECTOR, "div.uk-card")
            if cards:
                card = cards[0]
                self._scroll_into_view(card)
                self._safe_click(card)
                self._wait_for_spinner()
                time.sleep(0.5)
        except Exception:
            pass

    def fetch_pdf(self, plan_identifier: str) -> Optional[bytes]:
        """Attempt to download a PDF document for the given plan.

        The PDF download mechanism on Mavat is inconsistent.  This
        method performs best‑effort discovery of PDF buttons or links on
        the plan details page.  If a direct PDF URL is found, it is
        fetched using an in‑page `fetch` and returned as bytes.  If
        nothing is found, the method returns None.
        """
        # Navigate to the plan details page first
        details = self.get_plan_details(plan_identifier)
        if not self.driver:
            return None
        # Look for links or buttons that mention PDF
        selectors = [
            "//img[@title='הצג PDF']/parent::*",
            "//button[contains(@title, 'PDF') or contains(normalize-space(.), 'PDF') or contains(normalize-space(.), 'הצג PDF')]",
            "//a[contains(@href,'.pdf') or contains(normalize-space(.), 'PDF')]",
        ]
        pdf_el: Optional[Any] = None
        for sel in selectors:
            try:
                elems = self.driver.find_elements(By.XPATH, sel)
                for el in elems:
                    if el.is_displayed():
                        pdf_el = el
                        break
                if pdf_el:
                    break
            except Exception:
                continue
        if not pdf_el:
            return None
        # If the element is a link with a PDF href, attempt direct fetch
        href = pdf_el.get_attribute("href") if pdf_el else None
        if href and href.lower().endswith(".pdf"):
            try:
                # Use fetch from page context to bypass cross‑origin restrictions
                script = (
                    "const url = arguments[0];"
                    "return fetch(url, {credentials:'include'})"
                    ".then(r => r.arrayBuffer())"
                    ".then(buf => btoa(String.fromCharCode(...new Uint8Array(buf))));"
                )
                b64 = self.driver.execute_script(script, href)
                if b64:
                    import base64
                    return base64.b64decode(b64)
            except Exception:
                pass
        # Otherwise click the button/link to trigger a new tab or download
        self._safe_click(pdf_el)
        time.sleep(1.0)
        # If a new tab opened, switch to it
        try:
            handles = self.driver.window_handles
            if len(handles) > 1:
                self.driver.switch_to.window(handles[-1])
                time.sleep(0.5)
            # If URL ends with .pdf, fetch content via page context
            current_url = self.driver.current_url
            if current_url.lower().endswith('.pdf'):
                script = (
                    "return fetch(window.location.href, {credentials:'include'})"
                    ".then(r => r.arrayBuffer())"
                    ".then(buf => btoa(String.fromCharCode(...new Uint8Array(buf))));"
                )
                b64 = self.driver.execute_script(script)
                if b64:
                    import base64
                    return base64.b64decode(b64)
        except Exception:
            pass
        return None


if __name__ == "__main__":
    # Small demonstration when run directly
    with MavatSeleniumClient(headless=False) as client:
        if not client.is_accessible():
            print("Mavat is not accessible. Check your network or try again later.")
        else:
            print("Mavat system is reachable. Performing a demo search...")
            try:
                results = client.search_plans(query="תל אביב", limit=5)
                for hit in results:
                    print(f"{hit.plan_id} | {hit.title} | {hit.status}")
                if results:
                    print("\nFetching first plan details...")
                    plan = client.get_plan_details(results[0].plan_id)
                    print(plan)
            except Exception as e:
                print(f"Error during demo: {e}")