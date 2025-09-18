import pytest
from core.models import Asset
from core.serializers import AssetSerializer


@pytest.mark.django_db
def test_asset_serializer_meta_multiple_sources():
    asset = Asset(
        scope_type="address",
        meta={
            "city": {
                "value": "תל אביב",
                "source": "מנהל התכנון",
                "fetched_at": "2025-09-01",
                "url": "http://example.com/city",
            },
            "size": {
                "value": 80,
                "source": "yad2",
                "fetched_at": "2025-08-20",
            },
            "rights": {
                "value": {"extra": 1},
                "source": "gis_rights",
                "fetched_at": "2025-08-21",
            },
            "permits": {
                "value": [{"permit": "p"}],
                "source": "gis_permit",
                "fetched_at": "2025-08-22",
                "url": "http://example.com/permits",
            },
            "comps": {
                "value": [{"price": 1_000_000}],
                "source": "gov",
                "fetched_at": "2025-08-23",
            },
        },
    )
    # Save the asset to get a primary key
    asset.save()
    data = AssetSerializer(asset).data
    assert data["city"] == "תל אביב"
    assert data["size"] == 80
    assert data["rights"] == {"extra": 1}
    assert data["permits"] == [{"permit": "p"}]
    assert data["comps"] == [{"price": 1_000_000}]
    assert data["_meta"]["city"] == {
        "source": "מנהל התכנון",
        "fetched_at": "2025-09-01",
        "url": "http://example.com/city",
    }
    assert data["_meta"]["size"] == {
        "source": "yad2",
        "fetched_at": "2025-08-20",
    }
    assert data["_meta"]["rights"] == {
        "source": "gis_rights",
        "fetched_at": "2025-08-21",
    }
    assert data["_meta"]["permits"] == {
        "source": "gis_permit",
        "fetched_at": "2025-08-22",
        "url": "http://example.com/permits",
    }
    assert data["_meta"]["comps"] == {
        "source": "gov",
        "fetched_at": "2025-08-23",
    }
