from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import Asset, Document


class AssetDetailDocumentsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="asset-docs-tester",
            email="asset-docs@example.com",
            password="secure-pass-123",
        )

        cls.asset = Asset.objects.create(
            scope_type="address",
            city="Tel Aviv",
            street="Herzl",
            number=10,
            created_by=cls.user,
        )

        cls.document = Document.objects.create(
            asset=cls.asset,
            user=cls.user,
            title="Ownership Document",
            filename="ownership.pdf",
            file_path="documents/ownership.pdf",
            file_size=2048,
            mime_type="application/pdf",
        )

    def test_asset_detail_excludes_documents_by_default(self):
        response = self.client.get(f"/api/assets/{self.asset.id}")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("asset", payload)
        documents = payload["asset"].get("documents")
        self.assertIsNotNone(documents)
        self.assertEqual(documents, [])

    def test_asset_detail_includes_documents_when_requested(self):
        response = self.client.get(
            f"/api/assets/{self.asset.id}",
            {"includeDocuments": "true"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        documents = payload["asset"].get("documents")

        self.assertIsNotNone(documents)
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0]["title"], self.document.title)

    def test_asset_detail_includes_documents_with_snake_case_param(self):
        response = self.client.get(
            f"/api/assets/{self.asset.id}",
            {"include_documents": "1"},
        )

        self.assertEqual(response.status_code, 200)
        documents = response.json()["asset"].get("documents")

        self.assertIsNotNone(documents)
        self.assertEqual(len(documents), 1)
