#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mavat Scraper
================

This module contains a lightweight scraper for the `mavat.iplan.gov.il`
planning information system.  The scraper relies on Playwright to
drive a real browser instance so that it can piggyback on the same
authenticated network calls the website uses.  This approach avoids
having to reverse‑engineer internal API tokens or handle complex
session cookies.  It is inspired by the ``NadlanBrowserClient`` in the
``realestate‑agent`` repository but tailored to the structure of the
Mavat site.

The scraper exposes two primary methods:

``search_text``
    Perform a free‑text search in the Mavat portal and return a list
    of :class:`MavatSearchHit` objects summarising each plan found.

``plan_details``
    Navigate directly to a plan page and return a :class:`MavatPlan`
    with basic metadata about the plan.  Additional payloads (e.g.
    documents, GIS layers) are captured in the ``raw`` field.

The Playwright dependency is optional: if Playwright is not installed
the scraper will raise an informative error when used.  To install
Playwright run ``pip install playwright`` and then ``playwright
install`` to download a browser bundle.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


try:
    # Playwright is an optional dependency.  Import lazily so that
    # consumers can still import the module to inspect type hints
    # without triggering an ImportError.  Methods that rely on
    # Playwright will check for its availability at runtime.
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover - tested at runtime
    sync_playwright = None  # type: ignore


@dataclass
class MavatSearchHit:
    """Represents a single search hit returned by Mavat.

    Attributes
    ----------
    plan_id: str
        The unique identifier of the plan.
    title: Optional[str]
        A human friendly name or description for the plan.
    status: Optional[str]
        The current status of the plan (e.g. approved, deposited).
    authority: Optional[str]
        The approving authority or institution.
    jurisdiction: Optional[str]
        The local government or jurisdiction in which the plan is
        located.
    raw: Dict[str, Any]
        The raw JSON item returned by the Mavat API for inspection.
    """

    plan_id: str
    title: Optional[str] = None
    status: Optional[str] = None
    authority: Optional[str] = None
    jurisdiction: Optional[str] = None
    raw: Dict[str, Any] = None


@dataclass
class MavatPlan:
    """Represents basic details about a plan.

    Attributes
    ----------
    plan_id: str
        The unique identifier of the plan.
    plan_name: Optional[str]
        The official name of the plan.
    status: Optional[str]
        The current status of the plan.
    authority: Optional[str]
        The approving authority or institution.
    jurisdiction: Optional[str]
        The local government or jurisdiction of the plan.
    last_update: Optional[str]
        Date of the last update according to the API, if available.
    raw: Dict[str, Any]
        A dictionary containing all captured payloads for advanced
        consumers.  Keys include ``details``, ``documents`` and others
        as exposed by the site.
    """

    plan_id: str
    plan_name: Optional[str] = None
    status: Optional[str] = None
    authority: Optional[str] = None
    jurisdiction: Optional[str] = None
    last_update: Optional[str] = None
    raw: Dict[str, Any] = None


class MavatScraper:
    """High‑level wrapper around Playwright for scraping Mavat.

    Parameters
    ----------
    headless: bool, optional
        Whether to run the browser in headless mode.  Defaults to
        ``True``.  For debugging it can be helpful to set this to
        ``False`` and watch the browser.
    """

    def __init__(self, headless: bool = True) -> None:
        self.headless = headless

    def _ensure_playwright(self) -> None:
        """Check that Playwright is installed and raise otherwise."""
        if sync_playwright is None:
            raise RuntimeError(
                "Playwright is required for MavatScraper. Install via\n"
                "    pip install playwright\n"
                "and run\n"
                "    playwright install\n"
                "to download the browser binary."
            )

    def _launch(self):
        self._ensure_playwright()
        return sync_playwright().start()

    def search_text(self, text: str, limit: int = 20) -> List[MavatSearchHit]:
        """Search Mavat for plans matching a free text query.

        Parameters
        ----------
        text: str
            The search term to use.  This is equivalent to typing
            into the search box on the Mavat website.
        limit: int, optional
            Maximum number of results to return.  Defaults to 20.

        Returns
        -------
        List[MavatSearchHit]
            A list of search hits summarising each plan found.
        """
        self._ensure_playwright()
        hits: List[MavatSearchHit] = []
        with self._launch() as p:
            browser = p.chromium.launch(headless=self.headless)
            try:
                page = browser.new_page()
                collected: List[Dict[str, Any]] = []

                def on_response(response):
                    try:
                        url = response.url
                        if "/api/" in url and response.status == 200:
                            if any(key in url.lower() for key in ["search", "find", "query"]):
                                try:
                                    data = response.json()
                                except Exception:
                                    try:
                                        data = json.loads(response.text())
                                    except Exception:
                                        data = None
                                if isinstance(data, dict):
                                    items = (
                                        data.get("data", {}).get("items")
                                        or data.get("items")
                                        or data.get("result", {}).get("items")
                                    )
                                    if isinstance(items, list):
                                        collected.extend(items)
                    except Exception:
                        # Ignore any exceptions while listening to responses
                        pass

                page.on("response", on_response)
                # Navigate to the search page
                page.goto(
                    "https://mavat.iplan.gov.il/SV3?searchEntity=0&searchType=0&entityType=0&searchMethod=2",
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                # Attempt to fill the search input and trigger search
                try:
                    # Try to find a search box; there might be multiple inputs, we attempt generically
                    page.fill("input[type=search]", text)
                    page.keyboard.press("Enter")
                except Exception:
                    # If we cannot type programmatically the user can set headless=False and type manually
                    pass
                # Give the site time to issue network requests
                page.wait_for_timeout(4000)
                # Convert collected items into search hits
                for item in collected:
                    plan_id = str(
                        item.get("planId")
                        or item.get("PlanID")
                        or item.get("id")
                        or item.get("PlanId")
                        or ""
                    )
                    title = (
                        item.get("planName")
                        or item.get("PlanName")
                        or item.get("Title")
                        or item.get("name")
                    )
                    status = (
                        item.get("status")
                        or item.get("StatusDesc")
                        or item.get("PlanStatusDesc")
                    )
                    authority = (
                        item.get("authority")
                        or item.get("InstitutionName")
                        or item.get("AuthorityName")
                    )
                    jurisdiction = (
                        item.get("jurisdiction")
                        or item.get("LocalGovName")
                        or item.get("LocalAuthorityName")
                    )
                    hits.append(
                        MavatSearchHit(
                            plan_id=plan_id,
                            title=title,
                            status=status,
                            authority=authority,
                            jurisdiction=jurisdiction,
                            raw=item,
                        )
                    )
                    if limit and len(hits) >= limit:
                        break
                return hits
            finally:
                browser.close()

    def plan_details(self, plan_id: str) -> MavatPlan:
        """Fetch details for a specific plan.

        Parameters
        ----------
        plan_id: str
            The unique identifier of the plan to fetch.

        Returns
        -------
        MavatPlan
            An object containing basic details about the plan.  The
            ``raw`` field contains additional payloads captured during
            the scraping session, keyed by descriptive names (e.g.
            ``details``, ``documents``).
        """
        self._ensure_playwright()
        payloads: Dict[str, Any] = {}
        with self._launch() as p:
            browser = p.chromium.launch(headless=self.headless)
            try:
                page = browser.new_page()
                # Capture various API responses while the page loads
                def on_response(resp):
                    try:
                        if "/api/" in resp.url and resp.status == 200:
                            data: Any
                            try:
                                data = resp.json()
                            except Exception:
                                try:
                                    data = json.loads(resp.text())
                                except Exception:
                                    return
                            # Categorise the response roughly
                            url_lower = resp.url.lower()
                            if any(k in url_lower for k in ["detail", "plandetails", "plan"]):
                                payloads.setdefault("details", data)
                            elif any(k in url_lower for k in ["document", "file"]):
                                docs = payloads.setdefault("documents", [])
                                if isinstance(data, list):
                                    docs.extend(data)
                                else:
                                    docs.append(data)
                            elif any(k in url_lower for k in ["layer", "gis", "map"]):
                                payloads.setdefault("layers", data)
                            else:
                                payloads.setdefault("other", []).append(data)
                    except Exception:
                        pass

                page.on("response", on_response)
                page.goto(
                    f"https://mavat.iplan.gov.il/SV3?searchEntity=0&searchType=0&entityType=0&searchMethod=2&PlanID={plan_id}",
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                page.wait_for_timeout(5000)
                details = payloads.get("details", {})
                # Extract fields with fallbacks
                def _get(d: Dict[str, Any], *keys: str) -> Optional[str]:
                    for k in keys:
                        if isinstance(d.get(k), str):
                            return d[k]
                    return None
                return MavatPlan(
                    plan_id=plan_id,
                    plan_name=_get(details, "planName", "PlanName", "name", "Plan") or None,
                    status=_get(details, "status", "StatusDesc", "PlanStatusDesc") or None,
                    authority=_get(details, "authority", "InstitutionName", "AuthorityName") or None,
                    jurisdiction=_get(details, "jurisdiction", "LocalGovName", "LocalAuthorityName") or None,
                    last_update=_get(details, "lastUpdate", "LastUpdateDate") or None,
                    raw=payloads,
                )
            finally:
                browser.close()