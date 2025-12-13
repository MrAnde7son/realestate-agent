from django.test import TestCase
import importlib

from django.contrib.auth import get_user_model
from django.apps import apps as django_apps
from django.test import TestCase

from core.models import (
    Asset,
    Document,
    RealEstateTransaction,
    Permit,
    Plan,
    Listing,
    AssetDocument,
    AssetTransaction,
    AssetPermit,
    AssetPlan,
    AssetListing,
)
from core.services.asset_links import (
    asset_documents_all,
    asset_transactions_all,
)

User = get_user_model()


class DummyApps:
    @staticmethod
    def get_model(app_label, model_name):
        return django_apps.get_model(app_label, model_name)


class AssetLinkMigrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='linkuser',
            email='linkuser@example.com',
            password='pass1234',
        )
        self.asset = Asset.objects.create(
            scope_type='address',
            city='Tel Aviv',
            street='Herzl',
            number=10,
            created_by=self.user,
        )
        self.other_asset = Asset.objects.create(
            scope_type='address',
            city='Haifa',
            street='Ben Gurion',
            number=5,
            created_by=self.user,
        )

    def test_backfill_creates_links_for_legacy_records(self):
        document = Document.objects.create(
            asset=self.asset,
            user=self.user,
            title='Legacy Doc',
            filename='legacy.pdf',
            file_path='documents/legacy.pdf',
            file_size=100,
            mime_type='application/pdf',
        )
        transaction = RealEstateTransaction.objects.create(
            asset=self.asset,
            deal_id='TX1',
        )
        permit = Permit.objects.create(
            asset=self.asset,
            permit_number='P-1',
        )
        plan = Plan.objects.create(
            asset=self.asset,
            plan_number='PL-1',
        )

        migration_module = importlib.import_module('core.migrations.0043_m2m_links_and_listings')

        migration_module.backfill_docs(DummyApps, None)
        migration_module.backfill_transactions(DummyApps, None)
        migration_module.backfill_permits(DummyApps, None)
        migration_module.backfill_plans(DummyApps, None)

        self.assertTrue(
            AssetDocument.objects.filter(document=document, asset=self.asset).exists()
        )
        self.assertTrue(
            AssetTransaction.objects.filter(transaction=transaction, asset=self.asset).exists()
        )
        self.assertTrue(
            AssetPermit.objects.filter(permit=permit, asset=self.asset).exists()
        )
        self.assertTrue(
            AssetPlan.objects.filter(plan=plan, asset=self.asset).exists()
        )

    def test_all_assets_union_and_helpers(self):
        document = Document.objects.create(
            asset=self.asset,
            user=self.user,
            title='Union Doc',
            filename='union.pdf',
            file_path='documents/union.pdf',
            file_size=120,
            mime_type='application/pdf',
        )
        AssetDocument.objects.create(document=document, asset=self.other_asset)

        transaction = RealEstateTransaction.objects.create(
            asset=self.asset,
            deal_id='TX2',
        )
        AssetTransaction.objects.create(transaction=transaction, asset=self.asset)
        AssetTransaction.objects.create(transaction=transaction, asset=self.other_asset)

        self.assertEqual(
            sorted(asset.id for asset in document.all_assets()),
            sorted([self.asset.id, self.other_asset.id]),
        )
        self.assertEqual(
            sorted(asset.id for asset in transaction.all_assets()),
            sorted([self.asset.id, self.other_asset.id]),
        )
        self.assertEqual(asset_documents_all(self.asset).count(), 1)
        self.assertEqual(asset_transactions_all(self.other_asset).count(), 1)

    def test_transactions_require_m2m_links(self):
        transaction = RealEstateTransaction.objects.create(
            asset=self.asset,
            deal_id='TX-M2M',
        )

        # Without a through-table link, the transaction should not appear for the asset
        self.assertEqual(asset_transactions_all(self.asset).count(), 0)

        AssetTransaction.objects.create(transaction=transaction, asset=self.asset)

        self.assertEqual(asset_transactions_all(self.asset).count(), 1)

    def test_asset_deletion_preserves_related_records(self):
        document = Document.objects.create(
            asset=self.asset,
            user=self.user,
            title='Keep Doc',
            filename='keep.pdf',
            file_path='documents/keep.pdf',
            file_size=90,
            mime_type='application/pdf',
        )
        AssetDocument.objects.create(document=document, asset=self.other_asset)

        listing = Listing.objects.create(
            source='yad2',
            external_id='listing-1',
        )
        AssetListing.objects.create(listing=listing, asset=self.other_asset)

        self.other_asset.delete()

        self.assertTrue(Document.objects.filter(id=document.id).exists())
        self.assertFalse(
            AssetDocument.objects.filter(document=document, asset_id=self.other_asset.id).exists()
        )
        self.assertTrue(Listing.objects.filter(id=listing.id).exists())
