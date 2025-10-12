"""
Tests for Django global models and serializers.

Tests the global source tables, link tables, and their serializers.
"""

import pytest
from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from core.models import (
    Asset, RealEstateTransactionGlobal, MavatPlanGlobal, RamiParcelGlobal,
    DecisiveRecordGlobal, Yad2ListingGlobal,
    AssetToDeal, AssetToMavatPlan, AssetToRamiParcel,
    AssetToDecisiveRecord, AssetToYad2Listing
)
from core.serializers import (
    RealEstateTransactionGlobalSerializer, MavatPlanGlobalSerializer,
    RamiParcelGlobalSerializer, DecisiveRecordGlobalSerializer,
    Yad2ListingGlobalSerializer, AssetSerializer
)


class TestGlobalModels(TestCase):
    """Test global source models."""
    
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
    
    def test_realestatetransactionglobal_creation(self):
        """Test creating a global transaction."""
        transaction = RealEstateTransactionGlobal.objects.create(
            deal_id='DEAL123',
            key_fp='test_fingerprint',
            key_json={'city': 'Tel Aviv', 'street': 'Rothschild'},
            date=self.now,
            price=1000000,
            rooms=3,
            area=80.5,
            floor=2,
            address='Rothschild 123, Tel Aviv',
            raw={'test': 'data'},
            ttl_expires_at=self.ttl_expires
        )
        
        assert transaction.deal_id == 'DEAL123'
        assert transaction.price == 1000000
        assert transaction.rooms == 3
        assert transaction.area == 80.5
        assert transaction.floor == 2
        assert transaction.ttl_expires_at == self.ttl_expires
        assert str(transaction) == "TransactionGlobal(DEAL123, 1000000)"
    
    def test_mavatplanglobal_creation(self):
        """Test creating a global MAVAT plan."""
        plan = MavatPlanGlobal.objects.create(
            plan_id='PLAN123',
            key_fp='test_fingerprint',
            key_json={'city': 'Tel Aviv', 'street': 'Rothschild'},
            plan_number='PLAN123',
            plan_title='Test Plan',
            status='Approved',
            effective_date=self.now,
            plan_type='Residential',
            raw={'test': 'data'},
            ttl_expires_at=self.ttl_expires
        )
        
        assert plan.plan_id == 'PLAN123'
        assert plan.plan_title == 'Test Plan'
        assert plan.status == 'Approved'
        assert plan.plan_type == 'Residential'
        assert str(plan) == "MavatPlanGlobal(PLAN123, Test Plan)"
    
    def test_ramiparcelglobal_creation(self):
        """Test creating a global RAMI parcel."""
        parcel = RamiParcelGlobal.objects.create(
            rami_id='RAMI123',
            key_fp='test_fingerprint',
            key_json={'city': 'Tel Aviv', 'street': 'Rothschild'},
            plan_number='RAMI123',
            plan_name='Test RAMI Plan',
            status='Active',
            status_date=self.now,
            market_value=2000000,
            building_rights=150.0,
            raw={'test': 'data'},
            ttl_expires_at=self.ttl_expires
        )
        
        assert parcel.rami_id == 'RAMI123'
        assert parcel.plan_name == 'Test RAMI Plan'
        assert parcel.market_value == 2000000
        assert parcel.building_rights == 150.0
        assert str(parcel) == "RamiParcelGlobal(RAMI123, Test RAMI Plan)"
    
    def test_decisiverecordglobal_creation(self):
        """Test creating a global decisive record."""
        record = DecisiveRecordGlobal.objects.create(
            decisive_id='DECISIVE123',
            key_fp='test_fingerprint',
            key_json={'city': 'Tel Aviv', 'street': 'Rothschild'},
            appraiser='John Doe',
            date=self.now,
            appraised_value=1500000,
            url='https://example.com/decisive',
            raw={'test': 'data'},
            ttl_expires_at=self.ttl_expires
        )
        
        assert record.decisive_id == 'DECISIVE123'
        assert record.appraiser == 'John Doe'
        assert record.appraised_value == 1500000
        assert record.url == 'https://example.com/decisive'
        assert str(record) == "DecisiveRecordGlobal(DECISIVE123, John Doe)"
    
    def test_yad2listingglobal_creation(self):
        """Test creating a global Yad2 listing."""
        listing = Yad2ListingGlobal.objects.create(
            external_id='YAD2123',
            key_fp='test_fingerprint',
            key_json={'city': 'Tel Aviv', 'street': 'Rothschild'},
            title='Beautiful Apartment',
            price=2000000,
            address='Rothschild 123, Tel Aviv',
            rooms=3,
            area=80.5,
            property_type='Apartment',
            url='https://yad2.co.il/listing/123',
            raw={'test': 'data'},
            ttl_expires_at=self.ttl_expires
        )
        
        assert listing.external_id == 'YAD2123'
        assert listing.title == 'Beautiful Apartment'
        assert listing.price == 2000000
        assert listing.rooms == 3
        assert listing.area == 80.5
        assert listing.property_type == 'Apartment'
        assert str(listing) == "Yad2ListingGlobal(YAD2123, Beautiful Apartment)"
    
    def test_asset_to_deal_link_creation(self):
        """Test creating an asset-to-deal link."""
        transaction = RealEstateTransactionGlobal.objects.create(
            deal_id='DEAL123',
            key_fp='test_fingerprint',
            key_json={'city': 'Tel Aviv', 'street': 'Rothschild'},
            price=1000000
        )
        
        link = AssetToDeal.objects.create(
            asset=self.asset,
            transaction=transaction
        )
        
        assert link.asset == self.asset
        assert link.transaction == transaction
        assert str(link) == f"AssetToDeal({self.asset.id}, DEAL123)"
    
    def test_asset_to_mavat_plan_link_creation(self):
        """Test creating an asset-to-MAVAT plan link."""
        plan = MavatPlanGlobal.objects.create(
            plan_id='PLAN123',
            key_fp='test_fingerprint',
            key_json={'city': 'Tel Aviv', 'street': 'Rothschild'},
            plan_title='Test Plan'
        )
        
        link = AssetToMavatPlan.objects.create(
            asset=self.asset,
            plan=plan
        )
        
        assert link.asset == self.asset
        assert link.plan == plan
        assert str(link) == f"AssetToMavatPlan({self.asset.id}, PLAN123)"
    
    def test_unique_constraints(self):
        """Test that unique constraints work properly."""
        transaction = RealEstateTransactionGlobal.objects.create(
            deal_id='DEAL123',
            key_fp='test_fingerprint',
            key_json={'city': 'Tel Aviv', 'street': 'Rothschild'},
            price=1000000
        )
        
        # Create first link
        AssetToDeal.objects.create(
            asset=self.asset,
            transaction=transaction
        )
        
        # Try to create duplicate link - should raise IntegrityError
        with pytest.raises(Exception):  # IntegrityError
            AssetToDeal.objects.create(
                asset=self.asset,
                transaction=transaction
            )
    
    def test_model_indexes(self):
        """Test that model indexes are properly created."""
        # This test verifies that the indexes are defined in the model Meta
        assert 'deal_id' in [idx.fields[0] for idx in RealEstateTransactionGlobal._meta.indexes]
        assert 'key_fp' in [idx.fields[0] for idx in RealEstateTransactionGlobal._meta.indexes]
        assert 'ttl_expires_at' in [idx.fields[0] for idx in RealEstateTransactionGlobal._meta.indexes]


class TestGlobalSerializers(TestCase):
    """Test global source serializers."""
    
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
    
    def test_realestatetransactionglobal_serializer(self):
        """Test RealEstateTransactionGlobal serializer."""
        transaction = RealEstateTransactionGlobal.objects.create(
            deal_id='DEAL123',
            key_fp='test_fingerprint',
            key_json={'city': 'Tel Aviv', 'street': 'Rothschild'},
            date=self.now,
            price=1000000,
            rooms=3,
            area=80.5,
            floor=2,
            address='Rothschild 123, Tel Aviv',
            raw={'test': 'data'},
            ttl_expires_at=self.ttl_expires
        )
        
        serializer = RealEstateTransactionGlobalSerializer(transaction)
        data = serializer.data
        
        assert data['deal_id'] == 'DEAL123'
        assert data['price'] == 1000000
        assert data['rooms'] == 3
        assert data['area'] == 80.5
        assert data['floor'] == 2
        assert data['address'] == 'Rothschild 123, Tel Aviv'
        assert data['key_json'] == {'city': 'Tel Aviv', 'street': 'Rothschild'}
        assert data['raw'] == {'test': 'data'}
    
    def test_mavatplanglobal_serializer(self):
        """Test MavatPlanGlobal serializer."""
        plan = MavatPlanGlobal.objects.create(
            plan_id='PLAN123',
            key_fp='test_fingerprint',
            key_json={'city': 'Tel Aviv', 'street': 'Rothschild'},
            plan_number='PLAN123',
            plan_title='Test Plan',
            status='Approved',
            effective_date=self.now,
            plan_type='Residential',
            raw={'test': 'data'},
            ttl_expires_at=self.ttl_expires
        )
        
        serializer = MavatPlanGlobalSerializer(plan)
        data = serializer.data
        
        assert data['plan_id'] == 'PLAN123'
        assert data['plan_title'] == 'Test Plan'
        assert data['status'] == 'Approved'
        assert data['plan_type'] == 'Residential'
        assert data['key_json'] == {'city': 'Tel Aviv', 'street': 'Rothschild'}
        assert data['raw'] == {'test': 'data'}
    
    def test_asset_serializer_with_global_links(self):
        """Test AssetSerializer with global source links."""
        # Create global records
        transaction = RealEstateTransactionGlobal.objects.create(
            deal_id='DEAL123',
            key_fp='test_fingerprint',
            key_json={'city': 'Tel Aviv', 'street': 'Rothschild'},
            price=1000000
        )
        
        plan = MavatPlanGlobal.objects.create(
            plan_id='PLAN123',
            key_fp='test_fingerprint',
            key_json={'city': 'Tel Aviv', 'street': 'Rothschild'},
            plan_title='Test Plan'
        )
        
        # Create links
        AssetToDeal.objects.create(asset=self.asset, transaction=transaction)
        AssetToMavatPlan.objects.create(asset=self.asset, plan=plan)
        
        serializer = AssetSerializer(self.asset)
        data = serializer.data
        
        assert len(data['deal_links']) == 1
        assert data['deal_links'][0]['transaction']['deal_id'] == 'DEAL123'
        assert data['deal_links'][0]['transaction']['price'] == 1000000
        
        assert len(data['mavat_links']) == 1
        assert data['mavat_links'][0]['plan']['plan_id'] == 'PLAN123'
        assert data['mavat_links'][0]['plan']['plan_title'] == 'Test Plan'


class TestGlobalViews(APITestCase):
    """Test global source API views."""
    
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
    
    def test_global_transactions_view(self):
        """Test global transactions API view."""
        # Create test transactions
        transaction1 = RealEstateTransactionGlobal.objects.create(
            deal_id='DEAL123',
            key_fp='test_fingerprint',
            key_json={'city': 'Tel Aviv', 'street': 'Rothschild', 'number': 123},
            price=1000000
        )
        
        transaction2 = RealEstateTransactionGlobal.objects.create(
            deal_id='DEAL456',
            key_fp='test_fingerprint2',
            key_json={'city': 'Haifa', 'street': 'Herzl', 'number': 456},
            price=800000
        )
        
        # Test filtering by city
        response = self.client.get('/api/global/transactions/?city=Tel Aviv')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data['transactions']) == 1
        assert data['transactions'][0]['deal_id'] == 'DEAL123'
        
        # Test filtering by street
        response = self.client.get('/api/global/transactions/?street=Rothschild')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data['transactions']) == 1
        assert data['transactions'][0]['deal_id'] == 'DEAL123'
        
        # Test filtering by number
        response = self.client.get('/api/global/transactions/?number=123')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data['transactions']) == 1
        assert data['transactions'][0]['deal_id'] == 'DEAL123'
        
        # Test limit parameter
        response = self.client.get('/api/global/transactions/?limit=1')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data['transactions']) <= 1
    
    def test_global_mavat_plans_view(self):
        """Test global MAVAT plans API view."""
        # Create test plans
        plan1 = MavatPlanGlobal.objects.create(
            plan_id='PLAN123',
            key_fp='test_fingerprint',
            key_json={'city': 'Tel Aviv', 'street': 'Rothschild', 'number': 123},
            plan_title='Test Plan 1'
        )
        
        plan2 = MavatPlanGlobal.objects.create(
            plan_id='PLAN456',
            key_fp='test_fingerprint2',
            key_json={'city': 'Haifa', 'street': 'Herzl', 'number': 456},
            plan_title='Test Plan 2'
        )
        
        # Test filtering by city
        response = self.client.get('/api/global/mavat-plans/?city=Tel Aviv')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data['plans']) == 1
        assert data['plans'][0]['plan_id'] == 'PLAN123'
    
    def test_global_rami_parcels_view(self):
        """Test global RAMI parcels API view."""
        # Create test parcels
        parcel1 = RamiParcelGlobal.objects.create(
            rami_id='RAMI123',
            key_fp='test_fingerprint',
            key_json={'city': 'Tel Aviv', 'street': 'Rothschild', 'number': 123},
            plan_name='Test RAMI Plan 1'
        )
        
        parcel2 = RamiParcelGlobal.objects.create(
            rami_id='RAMI456',
            key_fp='test_fingerprint2',
            key_json={'city': 'Haifa', 'street': 'Herzl', 'number': 456},
            plan_name='Test RAMI Plan 2'
        )
        
        # Test filtering by city
        response = self.client.get('/api/global/rami-parcels/?city=Tel Aviv')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data['parcels']) == 1
        assert data['parcels'][0]['rami_id'] == 'RAMI123'
    
    def test_global_decisive_records_view(self):
        """Test global decisive records API view."""
        # Create test records
        record1 = DecisiveRecordGlobal.objects.create(
            decisive_id='DECISIVE123',
            key_fp='test_fingerprint',
            key_json={'city': 'Tel Aviv', 'street': 'Rothschild', 'number': 123},
            appraiser='John Doe'
        )
        
        record2 = DecisiveRecordGlobal.objects.create(
            decisive_id='DECISIVE456',
            key_fp='test_fingerprint2',
            key_json={'city': 'Haifa', 'street': 'Herzl', 'number': 456},
            appraiser='Jane Smith'
        )
        
        # Test filtering by city
        response = self.client.get('/api/global/decisive-records/?city=Tel Aviv')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data['records']) == 1
        assert data['records'][0]['decisive_id'] == 'DECISIVE123'
    
    def test_global_yad2_listings_view(self):
        """Test global Yad2 listings API view."""
        # Create test listings
        listing1 = Yad2ListingGlobal.objects.create(
            external_id='YAD2123',
            key_fp='test_fingerprint',
            key_json={'city': 'Tel Aviv', 'street': 'Rothschild', 'number': 123},
            title='Beautiful Apartment 1'
        )
        
        listing2 = Yad2ListingGlobal.objects.create(
            external_id='YAD2456',
            key_fp='test_fingerprint2',
            key_json={'city': 'Haifa', 'street': 'Herzl', 'number': 456},
            title='Beautiful Apartment 2'
        )
        
        # Test filtering by city
        response = self.client.get('/api/global/yad2-listings/?city=Tel Aviv')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data['listings']) == 1
        assert data['listings'][0]['external_id'] == 'YAD2123'
