import pytest
from django.contrib.auth import get_user_model

from core.models import (
    Asset,
    AssetDocument,
    AssetListing,
    AssetTransaction,
    Document,
    Listing,
    RealEstateTransaction,
)
from orchestration.data_pipeline import (
    _create_documents_and_plans,
    _create_django_records_from_collected_data,
)


@pytest.mark.django_db
def test_documents_and_plans_link_existing_document():
    user = get_user_model().objects.create_user(
        email="owner@example.com",
        password="test",
        username="owner",
    )
    existing_asset = Asset.objects.create(scope_type="address", city="Tel Aviv")
    new_asset = Asset.objects.create(scope_type="address", city="Tel Aviv")

    document = Document.objects.create(
        asset=existing_asset,
        user=user,
        title="Existing Appraisal",
        description="",
        document_type="appraisal_decisive",
        status="approved",
        filename="decisive.pdf",
        file_path="/tmp/decisive.pdf",
        file_size=0,
        mime_type="application/pdf",
        external_id="DEC-1",
        source="gov",
        meta={"seed": True},
    )
    AssetDocument.objects.create(document=document, asset=existing_asset)

    gov_data = {"decisive": [{"id": "DEC-1", "date": "01.01.2024", "url": "https://example.com"}]}

    _create_documents_and_plans(new_asset, {}, gov_data, plans=[], mavat_plans=[])

    document.refresh_from_db()
    assert document.asset_id == existing_asset.id
    assert AssetDocument.objects.filter(document=document, asset=new_asset).exists()
    assert set(document.all_assets().values_list("id", flat=True)) == {
        existing_asset.id,
        new_asset.id,
    }


@pytest.mark.django_db
def test_create_django_records_links_existing_transaction():
    existing_asset = Asset.objects.create(scope_type="address", city="Haifa")
    new_asset = Asset.objects.create(scope_type="address", city="Haifa")

    transaction = RealEstateTransaction.objects.create(
        asset=existing_asset,
        deal_id="T-1",
        price=100,
        raw={"seed": True},
    )
    AssetTransaction.objects.create(transaction=transaction, asset=existing_asset)

    gov_data = {
        "decisive": [],
        "transactions": [
            {
                "deal_id": "T-1",
                "deal_amount": 200,
                "rooms": "3",
                "floor": "1",
                "address": "Test st",
            }
        ],
    }

    _create_django_records_from_collected_data(
        new_asset,
        govmap_autocomplete_data={},
        govmap_data={},
        gis_data={},
        gov_data=gov_data,
        plans=[],
        mavat_plans=[],
        listings=[],
    )

    transaction.refresh_from_db()
    assert transaction.asset_id == existing_asset.id
    assert AssetTransaction.objects.filter(transaction=transaction, asset=new_asset).exists()


@pytest.mark.django_db
def test_create_django_records_links_existing_listing():
    existing_asset = Asset.objects.create(scope_type="address", city="Jerusalem")
    new_asset = Asset.objects.create(scope_type="address", city="Jerusalem")

    listing = Listing.objects.create(
        source="yad2",
        external_id="LIST-1",
        title="Original",
        url="https://original",
        raw={"seed": True},
    )
    AssetListing.objects.create(listing=listing, asset=existing_asset)

    listing_payload = {
        "listing_id": "LIST-1",
        "title": "Updated",
        "url": "https://example.com",
        "price": 2500000,
        "rooms": 4,
        "area": 120,
        "address": "Jerusalem",
        "status": "active",
    }

    _create_django_records_from_collected_data(
        new_asset,
        govmap_autocomplete_data={},
        govmap_data={},
        gis_data={},
        gov_data={"decisive": [], "transactions": []},
        plans=[],
        mavat_plans=[],
        listings=[listing_payload],
    )

    listing.refresh_from_db()
    assert AssetListing.objects.filter(listing=listing, asset=new_asset).exists()
    assert listing.raw.get("listing_id") == "LIST-1"
    assert listing.title == "Updated"
