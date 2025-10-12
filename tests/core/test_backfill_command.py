"""
Tests for the backfill management command.

Tests the Django management command for backfilling global source tables.
"""

import pytest
from unittest.mock import Mock, patch, call
from datetime import datetime, timedelta
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone
from io import StringIO

from core.models import (
    Asset, RealEstateTransaction, SourceRecord,
    RealEstateTransactionGlobal, MavatPlanGlobal, RamiParcelGlobal,
    DecisiveRecordGlobal, Yad2ListingGlobal,
    AssetToDeal, AssetToMavatPlan, AssetToRamiParcel,
    AssetToDecisiveRecord, AssetToYad2Listing
)


class TestBackfillCommand(TestCase):
    """Test the backfill management command."""
    
    def setUp(self):
        """Set up test data."""
        self.asset = Asset.objects.create(
            city='Tel Aviv',
            street='Rothschild',
            number=123,
            block='1234',
            parcel='56'
        )
        
        self.now = timezone.now()
        self.ttl_expires = self.now + timedelta(days=30)
    
    def test_backfill_transactions_dry_run(self):
        """Test backfill transactions in dry run mode."""
        # Create test transaction
        transaction = RealEstateTransaction.objects.create(
            asset=self.asset,
            deal_id='DEAL123',
            date=self.now,
            price=1000000,
            rooms=3,
            area=80.5,
            floor=2,
            address='Rothschild 123, Tel Aviv',
            raw={'test': 'data'}
        )
        
        # Run command in dry run mode
        out = StringIO()
        call_command('backfill_globals', '--dry-run', '--source=transactions', stdout=out)
        
        output = out.getvalue()
        assert 'DRY RUN MODE' in output
        assert 'Processing transactions' in output
        assert 'promoted' in output.lower()
        assert 'linked' in output.lower()
        
        # Verify no global records were created
        assert RealEstateTransactionGlobal.objects.count() == 0
        assert AssetToDeal.objects.count() == 0
    
    def test_backfill_transactions_actual_run(self):
        """Test backfill transactions in actual run mode."""
        # Create test transaction
        transaction = RealEstateTransaction.objects.create(
            asset=self.asset,
            deal_id='DEAL123',
            date=self.now,
            price=1000000,
            rooms=3,
            area=80.5,
            floor=2,
            address='Rothschild 123, Tel Aviv',
            raw={'test': 'data'}
        )
        
        # Run command
        out = StringIO()
        call_command('backfill_globals', '--source=transactions', stdout=out)
        
        output = out.getvalue()
        assert 'Processing transactions' in output
        assert 'promoted' in output.lower()
        assert 'linked' in output.lower()
        
        # Verify global records were created
        assert RealEstateTransactionGlobal.objects.count() == 1
        global_transaction = RealEstateTransactionGlobal.objects.first()
        assert global_transaction.deal_id == 'DEAL123'
        assert global_transaction.price == 1000000
        assert global_transaction.rooms == 3
        assert global_transaction.area == 80.5
        assert global_transaction.floor == 2
        
        # Verify link was created
        assert AssetToDeal.objects.count() == 1
        link = AssetToDeal.objects.first()
        assert link.asset == self.asset
        assert link.transaction == global_transaction
    
    def test_backfill_transactions_idempotent(self):
        """Test that backfill is idempotent."""
        # Create test transaction
        transaction = RealEstateTransaction.objects.create(
            asset=self.asset,
            deal_id='DEAL123',
            date=self.now,
            price=1000000,
            rooms=3,
            area=80.5,
            floor=2,
            address='Rothschild 123, Tel Aviv',
            raw={'test': 'data'}
        )
        
        # Run command twice
        call_command('backfill_globals', '--source=transactions')
        call_command('backfill_globals', '--source=transactions')
        
        # Verify only one global record was created
        assert RealEstateTransactionGlobal.objects.count() == 1
        assert AssetToDeal.objects.count() == 1
    
    def test_backfill_transactions_without_deal_id(self):
        """Test backfill transactions without deal_id."""
        # Create test transaction without deal_id
        transaction = RealEstateTransaction.objects.create(
            asset=self.asset,
            date=self.now,
            price=1000000,
            rooms=3,
            area=80.5,
            floor=2,
            address='Rothschild 123, Tel Aviv',
            raw={'test': 'data'}
        )
        
        # Run command
        call_command('backfill_globals', '--source=transactions')
        
        # Verify global record was created with content hash as deal_id
        assert RealEstateTransactionGlobal.objects.count() == 1
        global_transaction = RealEstateTransactionGlobal.objects.first()
        assert global_transaction.deal_id is not None
        assert len(global_transaction.deal_id) == 32  # SHA256 hex length
        assert global_transaction.price == 1000000
    
    def test_backfill_source_records_mavat(self):
        """Test backfill source records for MAVAT."""
        # Create test source record
        source_record = SourceRecord.objects.create(
            asset=self.asset,
            source='mavat',
            external_id='PLAN123',
            raw={
                'plan_number': 'PLAN123',
                'plan_title': 'Test Plan',
                'status': 'Approved',
                'effective_date': self.now.isoformat(),
                'plan_type': 'Residential'
            }
        )
        
        # Run command
        call_command('backfill_globals', '--source=source_records')
        
        # Verify global record was created
        assert MavatPlanGlobal.objects.count() == 1
        global_plan = MavatPlanGlobal.objects.first()
        assert global_plan.plan_id == 'PLAN123'
        assert global_plan.plan_title == 'Test Plan'
        assert global_plan.status == 'Approved'
        assert global_plan.plan_type == 'Residential'
        
        # Verify link was created
        assert AssetToMavatPlan.objects.count() == 1
        link = AssetToMavatPlan.objects.first()
        assert link.asset == self.asset
        assert link.plan == global_plan
    
    def test_backfill_source_records_rami(self):
        """Test backfill source records for RAMI."""
        # Create test source record
        source_record = SourceRecord.objects.create(
            asset=self.asset,
            source='gov_rami',
            external_id='RAMI123',
            raw={
                'plan_number': 'RAMI123',
                'plan_name': 'Test RAMI Plan',
                'status': 'Active',
                'status_date': self.now.isoformat(),
                'market_value': 2000000,
                'building_rights': 150.0
            }
        )
        
        # Run command
        call_command('backfill_globals', '--source=source_records')
        
        # Verify global record was created
        assert RamiParcelGlobal.objects.count() == 1
        global_parcel = RamiParcelGlobal.objects.first()
        assert global_parcel.rami_id == 'RAMI123'
        assert global_parcel.plan_name == 'Test RAMI Plan'
        assert global_parcel.status == 'Active'
        assert global_parcel.market_value == 2000000
        assert global_parcel.building_rights == 150.0
        
        # Verify link was created
        assert AssetToRamiParcel.objects.count() == 1
        link = AssetToRamiParcel.objects.first()
        assert link.asset == self.asset
        assert link.parcel == global_parcel
    
    def test_backfill_source_records_decisive(self):
        """Test backfill source records for decisive."""
        # Create test source record
        source_record = SourceRecord.objects.create(
            asset=self.asset,
            source='decisive',
            external_id='DECISIVE123',
            url='https://example.com/decisive',
            raw={
                'appraiser': 'John Doe',
                'date': self.now.isoformat(),
                'appraised_value': 1500000
            }
        )
        
        # Run command
        call_command('backfill_globals', '--source=source_records')
        
        # Verify global record was created
        assert DecisiveRecordGlobal.objects.count() == 1
        global_record = DecisiveRecordGlobal.objects.first()
        assert global_record.decisive_id == 'DECISIVE123'
        assert global_record.appraiser == 'John Doe'
        assert global_record.appraised_value == 1500000
        assert global_record.url == 'https://example.com/decisive'
        
        # Verify link was created
        assert AssetToDecisiveRecord.objects.count() == 1
        link = AssetToDecisiveRecord.objects.first()
        assert link.asset == self.asset
        assert link.record == global_record
    
    def test_backfill_source_records_yad2(self):
        """Test backfill source records for Yad2."""
        # Create test source record
        source_record = SourceRecord.objects.create(
            asset=self.asset,
            source='yad2',
            external_id='YAD2123',
            url='https://yad2.co.il/listing/123',
            raw={
                'title': 'Beautiful Apartment',
                'price': 2000000,
                'address': 'Rothschild 123, Tel Aviv',
                'rooms': 3,
                'area': 80.5,
                'property_type': 'Apartment'
            }
        )
        
        # Run command
        call_command('backfill_globals', '--source=source_records')
        
        # Verify global record was created
        assert Yad2ListingGlobal.objects.count() == 1
        global_listing = Yad2ListingGlobal.objects.first()
        assert global_listing.external_id == 'YAD2123'
        assert global_listing.title == 'Beautiful Apartment'
        assert global_listing.price == 2000000
        assert global_listing.rooms == 3
        assert global_listing.area == 80.5
        assert global_listing.property_type == 'Apartment'
        assert global_listing.url == 'https://yad2.co.il/listing/123'
        
        # Verify link was created
        assert AssetToYad2Listing.objects.count() == 1
        link = AssetToYad2Listing.objects.first()
        assert link.asset == self.asset
        assert link.listing == global_listing
    
    def test_backfill_source_records_without_external_id(self):
        """Test backfill source records without external_id."""
        # Create test source record without external_id
        source_record = SourceRecord.objects.create(
            asset=self.asset,
            source='mavat',
            raw={
                'plan_number': 'PLAN123',
                'plan_title': 'Test Plan',
                'status': 'Approved'
            }
        )
        
        # Run command
        call_command('backfill_globals', '--source=source_records')
        
        # Verify global record was created with content hash as plan_id
        assert MavatPlanGlobal.objects.count() == 1
        global_plan = MavatPlanGlobal.objects.first()
        assert global_plan.plan_id is not None
        assert len(global_plan.plan_id) == 32  # SHA256 hex length
        assert global_plan.plan_title == 'Test Plan'
    
    def test_backfill_source_records_unknown_source(self):
        """Test backfill source records with unknown source."""
        # Create test source record with unknown source
        source_record = SourceRecord.objects.create(
            asset=self.asset,
            source='unknown_source',
            raw={'test': 'data'}
        )
        
        # Run command
        call_command('backfill_globals', '--source=source_records')
        
        # Verify no global records were created
        assert MavatPlanGlobal.objects.count() == 0
        assert RamiParcelGlobal.objects.count() == 0
        assert DecisiveRecordGlobal.objects.count() == 0
        assert Yad2ListingGlobal.objects.count() == 0
    
    def test_backfill_batch_size(self):
        """Test backfill with custom batch size."""
        # Create multiple test transactions
        for i in range(5):
            RealEstateTransaction.objects.create(
                asset=self.asset,
                deal_id=f'DEAL{i}',
                price=1000000 + i * 100000,
                raw={'test': f'data{i}'}
            )
        
        # Run command with small batch size
        call_command('backfill_globals', '--source=transactions', '--batch-size=2')
        
        # Verify all global records were created
        assert RealEstateTransactionGlobal.objects.count() == 5
        assert AssetToDeal.objects.count() == 5
    
    def test_backfill_all_sources(self):
        """Test backfill all sources."""
        # Create test data for all sources
        RealEstateTransaction.objects.create(
            asset=self.asset,
            deal_id='DEAL123',
            price=1000000
        )
        
        SourceRecord.objects.create(
            asset=self.asset,
            source='mavat',
            external_id='PLAN123',
            raw={'plan_title': 'Test Plan'}
        )
        
        SourceRecord.objects.create(
            asset=self.asset,
            source='gov_rami',
            external_id='RAMI123',
            raw={'plan_name': 'Test RAMI Plan'}
        )
        
        SourceRecord.objects.create(
            asset=self.asset,
            source='decisive',
            external_id='DECISIVE123',
            raw={'appraiser': 'John Doe'}
        )
        
        SourceRecord.objects.create(
            asset=self.asset,
            source='yad2',
            external_id='YAD2123',
            raw={'title': 'Beautiful Apartment'}
        )
        
        # Run command for all sources
        call_command('backfill_globals', '--source=all')
        
        # Verify all global records were created
        assert RealEstateTransactionGlobal.objects.count() == 1
        assert MavatPlanGlobal.objects.count() == 1
        assert RamiParcelGlobal.objects.count() == 1
        assert DecisiveRecordGlobal.objects.count() == 1
        assert Yad2ListingGlobal.objects.count() == 1
        
        # Verify all links were created
        assert AssetToDeal.objects.count() == 1
        assert AssetToMavatPlan.objects.count() == 1
        assert AssetToRamiParcel.objects.count() == 1
        assert AssetToDecisiveRecord.objects.count() == 1
        assert AssetToYad2Listing.objects.count() == 1
    
    def test_backfill_handles_errors(self):
        """Test that backfill handles errors gracefully."""
        # Create test transaction
        transaction = RealEstateTransaction.objects.create(
            asset=self.asset,
            deal_id='DEAL123',
            price=1000000
        )
        
        # Mock an error during processing
        with patch('core.management.commands.backfill_globals.compute_key_fingerprint') as mock_fp:
            mock_fp.side_effect = Exception("Test error")
            
            # Run command
            call_command('backfill_globals', '--source=transactions')
            
            # Verify no global records were created due to error
            assert RealEstateTransactionGlobal.objects.count() == 0
            assert AssetToDeal.objects.count() == 0
