import json
import pytest
from django.urls import reverse
from django.test import Client
from core.models import Asset, Document, User

pytestmark = pytest.mark.django_db


def _create_user():
    return User.objects.create_user(
        username="u1", email="u1@example.com", password="pass"
    )


def test_permits_endpoint_with_building_permits():
    client = Client()
    user = _create_user()
    asset = Asset.objects.create(
        scope_type="address", street="Test", number=1, city="Tel Aviv"
    )

    # Create a permit document
    Document.objects.create(
        asset=asset,
        user=user,
        title="Building Permit",
        description="A building permit",
        document_type="permit",
        status="Issued",
        filename="permit.pdf",
        file_path="documents/permit.pdf",
        file_size=100,
        mime_type="application/pdf",
        external_id="12345",
        external_url="http://example.com/permit/12345",
        meta={"request_number": "REQ-1"},
    )

    url = reverse("asset_permits", kwargs={"asset_id": asset.id})
    resp = client.get(url)
    assert resp.status_code == 200
    data = json.loads(resp.content.decode())
    assert "permits" in data
    assert len(data["permits"]) == 1
    p = data["permits"][0]
    assert p["external_id"] == "12345"
    assert p["status"] == "Issued"
    assert p["external_url"] == "http://example.com/permit/12345"


def test_permits_endpoint_with_legacy_permits_key():
    client = Client()
    user = _create_user()
    asset = Asset.objects.create(
        scope_type="address", street="Legacy", number=2, city="Tel Aviv"
    )

    # Create a permit document
    Document.objects.create(
        asset=asset,
        user=user,
        title="Legacy Permit",
        description="A legacy permit",
        document_type="permit",
        status="Approved",
        filename="legacy.pdf",
        file_path="documents/legacy.pdf",
        file_size=100,
        mime_type="application/pdf",
        external_id="999",
        external_url="http://example.com/permit/999",
        meta={"request_number": "REQ-999"},
    )

    url = reverse("asset_permits", kwargs={"asset_id": asset.id})
    resp = client.get(url)
    assert resp.status_code == 200
    data = json.loads(resp.content.decode())
    assert len(data["permits"]) == 1
    p = data["permits"][0]
    assert p["external_id"] == "999"
    assert p["status"] == "Approved"


def test_permits_endpoint_deduplicates_same_permission_num():
    client = Client()
    user = _create_user()
    asset = Asset.objects.create(
        scope_type="address", street="Dup", number=3, city="Tel Aviv"
    )

    # Create two permit documents with same external_id
    Document.objects.create(
        asset=asset,
        user=user,
        title="Permit 1",
        description="First permit",
        document_type="permit",
        status="Stage1",
        filename="permit1.pdf",
        file_path="documents/permit1.pdf",
        file_size=100,
        mime_type="application/pdf",
        external_id="ABC",
        external_url="http://example.com/permit/ABC",
        meta={"request_number": "R1"},
    )

    Document.objects.create(
        asset=asset,
        user=user,
        title="Permit 2",
        description="Second permit",
        document_type="permit",
        status="Stage2",
        filename="permit2.pdf",
        file_path="documents/permit2.pdf",
        file_size=100,
        mime_type="application/pdf",
        external_id="ABC",
        external_url="http://example.com/permit/ABC",
        meta={"request_number": "R2"},
    )

    url = reverse("asset_permits", kwargs={"asset_id": asset.id})
    resp = client.get(url)
    assert resp.status_code == 200
    data = json.loads(resp.content.decode())
    # Should return both documents (no deduplication at endpoint level)
    assert len(data["permits"]) == 2
    assert all(p["external_id"] == "ABC" for p in data["permits"])


def test_permits_endpoint_document_and_meta_merge():
    client = Client()
    user = _create_user()
    asset = Asset.objects.create(
        scope_type="address", street="Doc", number=4, city="Tel Aviv"
    )

    # Create a permit document
    Document.objects.create(
        asset=asset,
        user=user,
        title="Permit PDF",
        description="A permit file",
        document_type="permit",
        status="approved",
        filename="permit.pdf",
        file_path="documents/permit.pdf",
        file_size=100,
        mime_type="application/pdf",
        external_id="DOC-777",
        external_url="http://example.com/doc777.pdf",
        meta={"request_number": "REQ-777"},
    )

    # Create another permit document with different external_id
    Document.objects.create(
        asset=asset,
        user=user,
        title="Another Permit",
        description="Another permit file",
        document_type="permit",
        status="Issued",
        filename="permit2.pdf",
        file_path="documents/permit2.pdf",
        file_size=100,
        mime_type="application/pdf",
        external_id="777",
        external_url="http://example.com/permit777.pdf",
        meta={"request_number": "REQ-777"},
    )

    url = reverse("asset_permits", kwargs={"asset_id": asset.id})
    resp = client.get(url)
    assert resp.status_code == 200
    data = json.loads(resp.content.decode())
    # Should return both documents
    assert len(data["permits"]) == 2
    external_ids = {p["external_id"] for p in data["permits"]}
    assert "DOC-777" in external_ids
    assert "777" in external_ids
