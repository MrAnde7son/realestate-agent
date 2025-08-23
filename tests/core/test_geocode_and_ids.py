"""Tests for the geocode_and_ids task."""

import types

import pytest
from django.core.management import call_command

from core.models import Asset
from core import tasks
import gis.gis_client as gis_client


class DummyGS:
    """Minimal TelAvivGS stand-in for testing."""

    def get_address_coordinates(self, street, number):
        return 100.0, 200.0

    def get_blocks(self, x, y):
        return [{"ms_gush": "1234"}]

    def get_parcels(self, x, y):
        return [{"ms_chelka": "56"}]

    _TRANS_2039_4326 = types.SimpleNamespace(transform=lambda x, y: (34.8, 32.1))


def test_geocode_and_ids_updates_asset(monkeypatch):
    """geocode_and_ids should populate asset location and IDs."""

    # Ensure database tables exist
    call_command("migrate", run_syncdb=True, verbosity=0)

    # Patch GIS client with dummy implementation
    monkeypatch.setattr(gis_client, "TelAvivGS", lambda: DummyGS())

    asset = Asset.objects.create(
        scope_type="address",
        street="הרצל",
        number=10,
        status="pending",
        meta={},
    )

    context = tasks.geocode_and_ids(asset.id)

    asset.refresh_from_db()
    assert asset.status == "enriching"
    assert asset.lat == pytest.approx(32.1)
    assert asset.lon == pytest.approx(34.8)
    assert asset.gush == "1234"
    assert asset.helka == "56"
    assert asset.normalized_address == "הרצל 10"

    assert context["gush"] == "1234"
    assert context["helka"] == "56"
    assert context["lat"] == pytest.approx(32.1)
    assert context["lon"] == pytest.approx(34.8)
