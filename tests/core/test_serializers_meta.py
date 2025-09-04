from core.models import Asset
from core.serializers import AssetSerializer


def test_asset_serializer_meta_multiple_sources():
    asset = Asset(
        city="תל אביב",
        price=1000000,
        meta={
            "city": {"source": "מנהל התכנון", "fetched_at": "2025-09-01"},
            "price": {"source": "yad2", "fetched_at": "2025-08-20"},
        },
    )
    data = AssetSerializer(asset).data
    assert data["_meta"]["city"] == {"source": "מנהל התכנון", "fetched_at": "2025-09-01"}
    assert data["_meta"]["price"] == {"source": "yad2", "fetched_at": "2025-08-20"}
