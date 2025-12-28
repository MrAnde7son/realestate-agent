"""Test doubles for external gov collectors used in e2e tests.

These helpers keep the e2e suite deterministic by emulating the network
clients that normally power the gov/nadlan collectors.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from gov.decisive import DecisiveAppraisal


class FakeNadlanScraper:
    """Minimal stand-in for :class:`NadlanDealsScraper`.

    The real scraper performs Selenium work and multiple retries.  For the
    tests we just need an object that records the requested address and returns
    a predictable list of deal-like objects.
    """

    def __init__(
        self, deals: Sequence[object] | None = None, fail: bool = False
    ) -> None:
        self._deals = list(deals or [])
        self.fail = fail
        self.calls: List[str] = []

    def get_deals_by_address(
        self, address: str, max_age_days: int = None, force_refresh: bool = False
    ) -> List[object]:
        self.calls.append(address)
        if self.fail:
            raise RuntimeError("forced nadlan failure")
        return list(self._deals)


class FakeDecisiveClient:
    """Stub for the gov.il decisive appraisal client."""

    def __init__(
        self,
        appraisals: Iterable[DecisiveAppraisal | dict] | None = None,
        *,
        fail: bool = False,
    ) -> None:
        self.fail = fail
        self.calls: List[tuple[str, str, int]] = []
        self._appraisals: List[DecisiveAppraisal] = []
        for appraisal in appraisals or []:
            if isinstance(appraisal, DecisiveAppraisal):
                self._appraisals.append(appraisal)
            else:
                self._appraisals.append(DecisiveAppraisal(**appraisal))

    def fetch_appraisals(
        self, block: str = "", plot: str = "", max_pages: int = 1
    ) -> List[DecisiveAppraisal]:
        self.calls.append((block, plot, max_pages))
        if self.fail:
            raise RuntimeError("forced decisive failure")
        return list(self._appraisals)


@dataclass
class FakeNotifier:
    """Simple notifier that matches on listing ids for alert checks."""

    listing_ids: Sequence[str]

    def matches(
        self, listing_snapshot
    ) -> bool:  # pragma: no cover - helper used in tests
        return getattr(listing_snapshot, "listing_id", None) in set(self.listing_ids)

    def notify(
        self, listing_snapshot
    ) -> None:  # pragma: no cover - helper used in tests
        self.last_notified = getattr(listing_snapshot, "listing_id", None)
