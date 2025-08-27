"""Scrapers for the Mavat domain.

This subpackage contains scraping logic for interacting with the
`mavat.iplan.gov.il` site.  Currently it exposes the
``MavatScraper`` class which uses Playwright to automate the
site and extract search results and plan details.  It is designed
to be minimal and self‑contained so it can be reused in CLI tools,
FastAPI microservices or data pipelines.
"""

from .mavat_scraper import MavatPlan, MavatScraper, MavatSearchHit

__all__ = ["MavatScraper", "MavatSearchHit", "MavatPlan"]
