from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest


class _DummyTransformer:
    @staticmethod
    def from_crs(*args, **kwargs):
        return _DummyTransformer()

    def transform(self, x, y, *args, **kwargs):
        return x, y


sys.modules.setdefault("pyproj", SimpleNamespace(Transformer=_DummyTransformer))

from core.models import Asset
from orchestration.pipeline.asset_expansion import auto_expand_related_assets


@pytest.mark.django_db
def test_auto_expand_creates_related_address(monkeypatch):
    base_asset = Asset.objects.create(
        scope_type="address",
        city="Tel Aviv",
        street="Rozov",
        number=14,
        status="done",
    )

    linked: list[int] = []

    def fake_link(asset, *args, **kwargs):
        linked.append(asset.id)

    monkeypatch.setattr(
        "orchestration.pipeline.asset_expansion._link_existing_data_to_asset",
        fake_link,
    )

    created_ids = auto_expand_related_assets(
        base_asset.id,
        listings=[{"address": "Rozov 18 Tel Aviv"}],
    )

    assert created_ids, "expected a new asset to be created from listing payload"
    new_asset = Asset.objects.get(id=created_ids[0])

    assert new_asset.scope_type == "address"
    assert new_asset.street == "Rozov"
    assert new_asset.number == 18
    assert new_asset.city == "Tel Aviv"
    assert new_asset.meta.get("auto_created") is True
    assert new_asset.meta.get("scope_type") == "address"
    assert linked == created_ids


@pytest.mark.django_db
def test_auto_expand_creates_parcel_asset_from_transactions(monkeypatch):
    base_asset = Asset.objects.create(
        scope_type="address",
        city="Tel Aviv",
        street="Rozov",
        number=14,
        status="done",
    )

    linked: list[int] = []

    def fake_link(asset, *args, **kwargs):
        linked.append(asset.id)

    monkeypatch.setattr(
        "orchestration.pipeline.asset_expansion._link_existing_data_to_asset",
        fake_link,
    )

    created_ids = auto_expand_related_assets(
        base_asset.id,
        gov_data={
            "transactions": [
                {
                    "block": "123",
                    "parcel": "456",
                    "city": "Tel Aviv",
                }
            ]
        },
    )

    assert created_ids, "expected parcel asset to be created when block/parcel provided"
    parcel_asset = Asset.objects.get(id=created_ids[0])

    assert parcel_asset.scope_type == "parcel"
    assert parcel_asset.block == "123"
    assert parcel_asset.parcel == "456"
    assert parcel_asset.city == "Tel Aviv"
    assert parcel_asset.normalized_address.startswith("Block 123 Parcel 456")
    assert parcel_asset.meta.get("auto_created") is True
    assert parcel_asset.meta.get("scope_type") == "parcel"
    assert linked == created_ids
