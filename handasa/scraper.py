"""Scraper for the Tel Aviv municipality Handasa portal."""

from __future__ import annotations

import logging
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from playwright.sync_api import Browser, Page, sync_playwright  # type: ignore
except Exception:  # pragma: no cover - ensure module still imports without Playwright
    Browser = Page = None  # type: ignore
    sync_playwright = None  # type: ignore


class HandasaScraperError(RuntimeError):
    """Raised when the Handasa scraper fails to fetch documents."""


@dataclass
class _PlaywrightContext:
    browser: Browser
    page: Page


class _PlaywrightManager(AbstractContextManager[_PlaywrightContext]):
    """Context manager that provisions a Chromium browser using Playwright."""

    def __enter__(self) -> _PlaywrightContext:  # pragma: no cover - thin wrapper
        if sync_playwright is None:
            raise HandasaScraperError(
                "Playwright is not installed. Install with 'pip install playwright' and 'playwright install'."
            )
        self._playwright = sync_playwright().start()
        browser = self._playwright.chromium.launch(headless=True)
        page = browser.new_page()
        context = _PlaywrightContext(browser=browser, page=page)
        self._context = context  # type: ignore[attr-defined]
        return context

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - best effort cleanup
        context: Optional[_PlaywrightContext] = getattr(self, "_context", None)
        try:
            if context and getattr(context, "page", None):
                try:
                    context.page.close()
                except Exception:
                    logger.debug("Failed to close Handasa Playwright page", exc_info=True)
            if context and getattr(context, "browser", None):
                try:
                    context.browser.close()
                except Exception:
                    logger.debug("Failed to close Handasa Playwright browser", exc_info=True)
        finally:
            playwright = getattr(self, "_playwright", None)
            if playwright is not None:
                try:
                    playwright.stop()
                except Exception:
                    logger.debug("Failed to stop Playwright", exc_info=True)
            self._playwright = None
            self._context = None


class HandasaScraper:
    """High level helper that extracts permits from the Handasa search portal."""

    BASE_URL = (
        "https://handasa.tel-aviv.gov.il/Pages/"
        "SearchResultsAnonPageNew.aspx?block={block}_{parcel}"
    )

    def __init__(
        self,
        *,
        wait_time: float = 5.0,
        context_factory: Optional[Callable[[], AbstractContextManager[_PlaywrightContext]]] = None,
    ) -> None:
        """Create a new scraper instance."""

        self.wait_time = wait_time
        self._context_factory = context_factory or _PlaywrightManager

    # ------------------------------------------------------------------
    def fetch_documents(self, block: int, parcel: int) -> List[Dict]:
        """Return the raw document payloads for a block/parcel pair."""

        if block is None or parcel is None:
            raise HandasaScraperError("Handasa scraper requires block and parcel numbers")

        try:
            block_int = int(block)
            parcel_int = int(parcel)
        except (TypeError, ValueError) as exc:
            raise HandasaScraperError("Block and parcel must be numeric") from exc

        url = self.BASE_URL.format(block=block_int, parcel=parcel_int)
        documents: List[Dict] = []

        context_manager = self._context_factory()
        try:
            with context_manager as context:
                page = context.page

                def handle_response(response) -> None:
                    if "GetBuildingFileDocuments" not in response.url:
                        return
                    if response.status != 200:
                        logger.debug(
                            "Skipping Handasa response", extra={"url": response.url, "status": response.status}
                        )
                        return
                    try:
                        payload = response.json()
                    except Exception as exc:  # pragma: no cover - rare JSON issues
                        logger.debug("Failed to decode Handasa response", extra={"error": str(exc)})
                        return
                    data = payload.get("data")
                    if isinstance(data, list):
                        documents.extend(d for d in data if isinstance(d, dict))

                page.on("response", handle_response)
                logger.info("Navigating to Handasa portal", extra={"url": url})
                page.goto(url, wait_until="networkidle")
                try:
                    page.click("button#btnSearch", timeout=2000)
                except Exception:
                    logger.debug("Search button not clickable – continuing")
                if self.wait_time:
                    page.wait_for_timeout(int(self.wait_time * 1000))
        except Exception as exc:
            raise HandasaScraperError(f"Failed to fetch Handasa documents: {exc}") from exc

        return documents

