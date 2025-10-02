# -*- coding: utf-8 -*-
import json
import pytest
from django.urls import reverse

from core.models import Asset, SourceRecord
from core.listing_builder import build_listing


@pytest.mark.django_db
def test_listing_consistency_across_surfaces(client):
    a = Asset.objects.create(
        scope_type="address",
        city="תל אביב",
        street="הרצל",
        number="10",
        area=85,
        rooms=4,
        bedrooms=3,
        status="active",
        meta={"price": 2900000, "type": "דירה"},
    )
    SourceRecord.objects.create(
        asset=a, raw={"size": 85, "price": 2900000, "property_type": "דירה"}
    )

    r = client.get(reverse("assets"))
    assert r.status_code == 200
    row = next(x for x in r.json()["rows"] if x["id"] == a.id)
    assert row["netSqm"] == 85
    assert row["price"] == 2900000

    listing = build_listing(a, a.source_records.all())
    assert listing["netSqm"] == row["netSqm"]
    assert listing["price"] == row["price"]

    m = client.post(
        reverse("asset_share_message", args=[a.id]),
        data=json.dumps({}),
        content_type="application/json",
    )
    assert m.status_code == 200
    text = m.json()["text"]
    assert "85" in text
    assert "תל אביב" in text
