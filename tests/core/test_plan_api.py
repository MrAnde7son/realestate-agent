"""
Test cases for plan-related API endpoints
"""

import pytest
import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from core.models import PlanType, UserPlan, Asset

User = get_user_model()


@pytest.mark.django_db
class TestPlanAPIEndpoints:
    """Test cases for plan-related API endpoints"""

    def setup_method(self):
        """Set up test data for each test method"""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create plan types
        self.free_plan = PlanType.objects.create(
            name='free',
            display_name='Free Plan',
            description='Free plan for basic users',
            price=Decimal('0.00'),
            currency='ILS',
            billing_period='monthly',
            asset_limit=5,
            report_limit=10,
            alert_limit=5,
            advanced_analytics=False,
            data_export=False,
            api_access=False,
            priority_support=False,
            custom_reports=False,
            is_active=True
        )
        
        self.basic_plan = PlanType.objects.create(
            name='basic',
            display_name='Basic Plan',
            description='Basic plan for advanced users',
            price=Decimal('149.00'),
            currency='ILS',
            billing_period='monthly',
            asset_limit=25,
            report_limit=50,
            alert_limit=25,
            advanced_analytics=True,
            data_export=True,
            api_access=False,
            priority_support=False,
            custom_reports=False,
            is_active=True
        )
        
        self.pro_plan = PlanType.objects.create(
            name='pro',
            display_name='Pro Plan',
            description='Professional plan for power users',
            price=Decimal('299.00'),
            currency='ILS',
            billing_period='monthly',
            asset_limit=-1,  # Unlimited
            report_limit=-1,
            alert_limit=-1,
            advanced_analytics=True,
            data_export=True,
            api_access=True,
            priority_support=True,
            custom_reports=True,
            is_active=True
        )

    def test_user_plan_info_authenticated(self):
        """Test getting user plan info when authenticated"""
        # Create user plan
        UserPlan.objects.create(
            user=self.user,
            plan_type=self.basic_plan,
            is_active=True
        )
        
        # Create some assets
        for i in range(10):
            Asset.objects.create(
                address=f"Test Address {i}",
                city="Test City",
                price=100000,
                rooms=3,
                created_by=self.user
            )
        
        # Authenticate and make request
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/plans/info/')
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['plan_name'] == 'basic'
        assert data['display_name'] == 'Basic Plan'
        assert data['price'] == '149.00'
        assert data['limits']['assets']['limit'] == 25
        assert data['limits']['assets']['used'] == 10
        assert data['limits']['assets']['remaining'] == 15
        assert data['features']['advanced_analytics'] is True
        assert data['features']['data_export'] is True

    def test_user_plan_info_unauthenticated(self):
        """Test getting user plan info when not authenticated"""
        response = self.client.get('/api/plans/info/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_plan_info_no_plan(self):
        """Test getting user plan info when user has no plan"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/plans/info/')
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['plan_name'] == 'free'  # Should assign default plan
        assert data['display_name'] == 'Free Plan'

    def test_plan_types_list(self):
        """Test getting list of available plan types"""
        response = self.client.get('/api/plans/types/')
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert 'plans' in data
        assert len(data['plans']) == 3  # free, basic, pro
        
        # Check plan data structure
        plan_names = [plan['name'] for plan in data['plans']]
        assert 'free' in plan_names
        assert 'basic' in plan_names
        assert 'pro' in plan_names
        
        # Check basic plan details
        basic_plan_data = next(plan for plan in data['plans'] if plan['name'] == 'basic')
        assert basic_plan_data['display_name'] == 'Basic Plan'
        assert basic_plan_data['price'] == '149.00'
        assert basic_plan_data['asset_limit'] == 25
        assert basic_plan_data['advanced_analytics'] is True

    def test_upgrade_plan_success(self):
        """Test successful plan upgrade"""
        # Create user with free plan
        UserPlan.objects.create(
            user=self.user,
            plan_type=self.free_plan,
            is_active=True
        )
        
        self.client.force_authenticate(user=self.user)
        
        # Upgrade to basic plan
        response = self.client.post('/api/plans/upgrade/', {
            'plan_name': 'basic'
        })
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert 'success' in data
        assert 'upgraded' in data['message']
        
        # Verify plan was upgraded
        self.user.refresh_from_db()
        assert self.user.current_plan.plan_type == self.basic_plan

    def test_upgrade_plan_invalid_plan(self):
        """Test upgrading to invalid plan"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/plans/upgrade/', {
            'plan_name': 'nonexistent'
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert 'error' in data
        assert 'not found' in data['error'].lower()

    def test_upgrade_plan_same_plan(self):
        """Test upgrading to the same plan"""
        # Create user with basic plan
        UserPlan.objects.create(
            user=self.user,
            plan_type=self.basic_plan,
            is_active=True
        )
        
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/plans/upgrade/', {
            'plan_name': 'basic'
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert 'error' in data
        assert 'already' in data['error'].lower()

    def test_upgrade_plan_unauthenticated(self):
        """Test upgrading plan when not authenticated"""
        response = self.client.post('/api/plans/upgrade/', {
            'plan_name': 'basic'
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_upgrade_plan_missing_plan_name(self):
        """Test upgrading plan without plan_name parameter"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/plans/upgrade/', {})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert 'error' in data
        assert 'plan_name' in data['error'].lower()


@pytest.mark.django_db
class TestAssetCreationWithPlanLimits:
    """Test cases for asset creation with plan limits enforcement"""

    def setup_method(self):
        """Set up test data for each test method"""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create basic plan with limit
        self.basic_plan = PlanType.objects.create(
            name='basic',
            display_name='Basic Plan',
            asset_limit=5
        )
        
        # Create pro plan with unlimited assets
        self.pro_plan = PlanType.objects.create(
            name='pro',
            display_name='Pro Plan',
            asset_limit=-1
        )

    def test_asset_creation_within_limit(self):
        """Test asset creation within plan limits"""
        # Create user with basic plan
        UserPlan.objects.create(
            user=self.user,
            plan_type=self.basic_plan,
            is_active=True
        )
        
        # Create 3 assets (within limit of 5)
        for i in range(3):
            Asset.objects.create(
                address=f"Test Address {i}",
                city="Test City",
                price=100000,
                rooms=3,
                created_by=self.user
            )
        
        self.client.force_authenticate(user=self.user)
        
        # Try to create another asset
        response = self.client.post('/api/assets/', {
            'address': 'New Test Address',
            'city': 'Test City',
            'price': 200000,
            'rooms': 4
        })
        
        assert response.status_code == status.HTTP_201_CREATED

    def test_asset_creation_exceeds_limit(self):
        """Test asset creation when plan limit is exceeded"""
        # Create user with basic plan
        UserPlan.objects.create(
            user=self.user,
            plan_type=self.basic_plan,
            is_active=True
        )
        
        # Create 5 assets (at limit)
        for i in range(5):
            Asset.objects.create(
                address=f"Test Address {i}",
                city="Test City",
                price=100000,
                rooms=3,
                created_by=self.user
            )
        
        self.client.force_authenticate(user=self.user)
        
        # Try to create another asset
        response = self.client.post('/api/assets/', {
            'address': 'New Test Address',
            'city': 'Test City',
            'price': 200000,
            'rooms': 4
        })
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        data = response.json()
        assert data['error'] == 'asset_limit_exceeded'
        assert 'הגעת למגבלת הנכסים' in data['message']
        assert data['current_plan'] == 'Basic Plan'
        assert data['asset_limit'] == 5
        assert data['assets_used'] == 5
        assert data['remaining'] == 0

    def test_asset_creation_unlimited_plan(self):
        """Test asset creation with unlimited plan"""
        # Create user with pro plan
        UserPlan.objects.create(
            user=self.user,
            plan_type=self.pro_plan,
            is_active=True
        )
        
        # Create many assets
        for i in range(50):
            Asset.objects.create(
                address=f"Test Address {i}",
                city="Test City",
                price=100000,
                rooms=3,
                created_by=self.user
            )
        
        self.client.force_authenticate(user=self.user)
        
        # Try to create another asset
        response = self.client.post('/api/assets/', {
            'address': 'New Test Address',
            'city': 'Test City',
            'price': 200000,
            'rooms': 4
        })
        
        assert response.status_code == status.HTTP_201_CREATED

    def test_asset_creation_no_plan(self):
        """Test asset creation when user has no plan"""
        self.client.force_authenticate(user=self.user)
        
        # Create 4 assets (within default limit of 5)
        for i in range(4):
            response = self.client.post('/api/assets/', {
                'address': f'Test Address {i}',
                'city': 'Test City',
                'price': 100000,
                'rooms': 3
            })
            assert response.status_code == status.HTTP_201_CREATED
        
        # Try to create 5th asset (should succeed)
        response = self.client.post('/api/assets/', {
            'address': 'Test Address 4',
            'city': 'Test City',
            'price': 100000,
            'rooms': 3
        })
        assert response.status_code == status.HTTP_201_CREATED
        
        # Try to create 6th asset (should fail)
        response = self.client.post('/api/assets/', {
            'address': 'Test Address 5',
            'city': 'Test City',
            'price': 100000,
            'rooms': 3
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_asset_creation_unauthenticated(self):
        """Test asset creation when not authenticated"""
        response = self.client.post('/api/assets/', {
            'address': 'Test Address',
            'city': 'Test City',
            'price': 100000,
            'rooms': 3
        })
        
        # Should still work for unauthenticated users (no plan limits)
        assert response.status_code == status.HTTP_201_CREATED

    def test_asset_creation_updates_usage_count(self):
        """Test that asset creation updates usage count"""
        # Create user with basic plan
        user_plan = UserPlan.objects.create(
            user=self.user,
            plan_type=self.basic_plan,
            is_active=True,
            assets_used=0
        )
        
        self.client.force_authenticate(user=self.user)
        
        # Create an asset
        response = self.client.post('/api/assets/', {
            'address': 'Test Address',
            'city': 'Test City',
            'price': 100000,
            'rooms': 3
        })
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # Check that usage count was updated
        user_plan.refresh_from_db()
        assert user_plan.assets_used == 1

    def test_asset_creation_with_expired_plan(self):
        """Test asset creation with expired plan"""
        from datetime import datetime, timedelta
        
        # Create user with expired plan
        expired_date = datetime.now() - timedelta(days=1)
        user_plan = UserPlan.objects.create(
            user=self.user,
            plan_type=self.basic_plan,
            is_active=True,
            expires_at=expired_date
        )
        
        self.client.force_authenticate(user=self.user)
        
        # Should still work (plan is active in DB, just expired)
        response = self.client.post('/api/assets/', {
            'address': 'Test Address',
            'city': 'Test City',
            'price': 100000,
            'rooms': 3
        })
        
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestPlanAPIEdgeCases:
    """Test cases for edge cases in plan API"""

    def setup_method(self):
        """Set up test data for each test method"""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_plan_info_with_inactive_plan(self):
        """Test plan info with inactive plan"""
        # Create inactive plan
        inactive_plan = PlanType.objects.create(
            name='inactive',
            display_name='Inactive Plan',
            asset_limit=10,
            is_active=False
        )
        
        UserPlan.objects.create(
            user=self.user,
            plan_type=inactive_plan,
            is_active=False
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/plans/info/')
        
        # Should assign default plan since current plan is inactive
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['plan_name'] == 'free'  # Default plan

    def test_plan_types_only_active(self):
        """Test that only active plans are returned"""
        # Create inactive plan
        PlanType.objects.create(
            name='inactive',
            display_name='Inactive Plan',
            asset_limit=10,
            is_active=False
        )
        
        response = self.client.get('/api/plans/types/')
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        plan_names = [plan['name'] for plan in data['plans']]
        assert 'inactive' not in plan_names

    def test_upgrade_plan_inactive_plan(self):
        """Test upgrading to inactive plan"""
        # Create inactive plan
        inactive_plan = PlanType.objects.create(
            name='inactive',
            display_name='Inactive Plan',
            asset_limit=10,
            is_active=False
        )
        
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/plans/upgrade/', {
            'plan_name': 'inactive'
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert 'error' in data
        assert 'not found' in data['error'].lower()

    def test_plan_info_serialization(self):
        """Test that plan info is properly serialized"""
        # Create plan with all features
        plan_type = PlanType.objects.create(
            name='test',
            display_name='Test Plan',
            description='Test description',
            price=Decimal('99.99'),
            currency='USD',
            billing_period='yearly',
            asset_limit=100,
            report_limit=200,
            alert_limit=50,
            advanced_analytics=True,
            data_export=True,
            api_access=True,
            priority_support=True,
            custom_reports=True
        )
        
        UserPlan.objects.create(
            user=self.user,
            plan_type=plan_type,
            is_active=True
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/plans/info/')
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        
        # Check all fields are present and properly formatted
        assert 'plan_name' in data
        assert 'display_name' in data
        assert 'description' in data
        assert 'price' in data
        assert 'currency' in data
        assert 'billing_period' in data
        assert 'is_active' in data
        assert 'is_expired' in data
        assert 'limits' in data
        assert 'features' in data
        
        # Check limits structure
        assert 'assets' in data['limits']
        assert 'reports' in data['limits']
        assert 'alerts' in data['limits']
        
        # Check features structure
        assert 'advanced_analytics' in data['features']
        assert 'data_export' in data['features']
        assert 'api_access' in data['features']
        assert 'priority_support' in data['features']
        assert 'custom_reports' in data['features']
