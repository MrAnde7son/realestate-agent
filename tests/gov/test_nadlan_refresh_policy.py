"""Tests for the NadlanDealsScraper refresh-or-fail policy."""

from unittest.mock import MagicMock

import pytest

from gov.nadlan.exceptions import NadlanAPIError
from gov.nadlan.models import Deal
from gov.nadlan.scraper import NadlanDealsScraper


@pytest.fixture()
def scraper():
    scraper = NadlanDealsScraper()
    scraper.driver = MagicMock()
    scraper.driver.current_url = (
        "https://www.nadlan.gov.il/?view=address&id=123&page=deals"
    )
    scraper.driver.refresh = MagicMock()
    scraper.driver.get = MagicMock()
    scraper.driver.save_screenshot = MagicMock(return_value=True)
    scraper._wait_for_page_load = MagicMock()
    scraper._human_pause = MagicMock()
    scraper._human_scroll = MagicMock()
    return scraper


def test_refresh_once_and_reparse_success(scraper):
    """Ensure a single refresh triggers a re-parse."""
    scraper._check_for_error_modal = MagicMock(return_value=False)

    deals = [Deal(address="A", deal_amount=1_000_000)]
    parse_fn = MagicMock(return_value=deals)

    result = scraper._refresh_once_and_reparse(parse_fn, address="Some St")

    scraper.driver.refresh.assert_called_once()
    parse_fn.assert_called_once_with("")
    assert result == deals


def test_refresh_once_and_reparse_modal_persists(scraper):
    """If the modal persists after refresh we should give up."""
    scraper._check_for_error_modal = MagicMock(return_value=True)
    parse_fn = MagicMock()

    result = scraper._refresh_once_and_reparse(parse_fn, address="Some St")

    assert result is None
    parse_fn.assert_not_called()


def test_fetch_deals_handles_modal_refresh(scraper):
    """When a modal appears we refresh exactly once and keep data."""
    scraper._navigate_to_deals_via_search = MagicMock(return_value=True)
    scraper._extract_neighborhood_from_page = MagicMock(return_value="שכונה")
    scraper._check_for_error_modal = MagicMock(return_value=True)

    deals = [Deal(address="A", deal_amount=1_000_000)]
    scraper._refresh_once_and_reparse = MagicMock(return_value=deals.copy())
    scraper._extract_deals_from_all_pages = MagicMock(return_value=[])

    result = scraper._fetch_deals_by_address_selenium("Test Address")

    assert result == deals
    assert scraper.error_modal_encountered is True
    scraper._refresh_once_and_reparse.assert_called_once()
    scraper._extract_deals_from_all_pages.assert_called_once_with("שכונה")


def test_fetch_deals_zero_results_after_refresh(scraper):
    """If zero deals remain after the single refresh we fail fast."""
    scraper._navigate_to_deals_via_search = MagicMock(return_value=True)
    scraper._extract_neighborhood_from_page = MagicMock(return_value="שכונה")
    scraper._check_for_error_modal = MagicMock(return_value=False)
    scraper._wait_for_deals_api_call = MagicMock(return_value=True)
    scraper._extract_deals_from_current_page = MagicMock(return_value=[])
    scraper._refresh_once_and_reparse = MagicMock(return_value=None)

    with pytest.raises(
        NadlanAPIError,
        match="No data returned from API after refresh",
    ):
        scraper._fetch_deals_by_address_selenium("Test Address")

    scraper._refresh_once_and_reparse.assert_called_once()
