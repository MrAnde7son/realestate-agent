"""
Integration tests for plan enforcement across the entire system
"""

import pytest
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from unittest.mock import patch, MagicMock

from core.models import PlanType, UserPlan, Asset
from core.plan_service import PlanService

User = get_user_model()


@pytest.mark.django_db
class TestPlanEnforcementIntegration:
    """Integration tests for plan enforcement across the system"""

    def setup_method(self):
        """Set up test data for each test method"""
        self.client = APIClient()
        
        # Create test users
        self.free_user = User.objects.create_user(
            username='freeuser',
            email='free@example.com',
            password='testpass123'
        )
        
        self.basic_user = User.objects.create_user(
            username='basicuser',
            email='basic@example.com',
            password='testpass123'
        )
        
        self.pro_user = User.objects.create_user(
            username='prouser',
            email='pro@example.com',
            password='testpass123'
        )
        
        # Create plan types
        self.free_plan = PlanType.objects.create(
            name='free',
            display_name='Free Plan',
            asset_limit=5,
            report_limit=10,
            alert_limit=5
        )
        
        self.basic_plan = PlanType.objects.create(
            name='basic',
            display_name='Basic Plan',
            asset_limit=25,
            report_limit=50,
            alert_limit=25,
            advanced_analytics=True,
            data_export=True
        )
        
        self.pro_plan = PlanType.objects.create(
            name='pro',
            display_name='Pro Plan',
            asset_limit=-1,  # Unlimited
            report_limit=-1,
            alert_limit=-1,
            advanced_analytics=True,
            data_export=True,
            api_access=True,
            priority_support=True,
            custom_reports=True
        )
        
        # Assign plans to users
        UserPlan.objects.create(
            user=self.free_user,
            plan_type=self.free_plan,
            is_active=True
        )
        
        UserPlan.objects.create(
            user=self.basic_user,
            plan_type=self.basic_plan,
            is_active=True
        )
        
        UserPlan.objects.create(
            user=self.pro_user,
            plan_type=self.pro_plan,
            is_active=True
        )

    def test_end_to_end_asset_creation_workflow(self):
        """Test complete asset creation workflow with plan enforcement"""
        # Test free user creating assets up to limit
        self.client.force_authenticate(user=self.free_user)
        
        # Create 5 assets (at limit)
        for i in range(5):
            response = self.client.post('/api/assets/', {
                'address': f'Free User Address {i}',
                'city': 'Test City',
                'price': 100000 + i * 10000,
                'rooms': 3
            })
            assert response.status_code == status.HTTP_201_CREATED
        
        # Try to create 6th asset (should fail)
        response = self.client.post('/api/assets/', {
            'address': 'Free User Address 5',
            'city': 'Test City',
            'price': 150000,
            'rooms': 3
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Verify plan info shows correct usage
        response = self.client.get('/api/plans/info/')
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['limits']['assets']['used'] == 5
        assert data['limits']['assets']['remaining'] == 0

    def test_plan_upgrade_workflow(self):
        """Test complete plan upgrade workflow"""
        # Start with free user at limit
        self.client.force_authenticate(user=self.free_user)
        
        # Create 5 assets (at free limit)
        for i in range(5):
            response = self.client.post('/api/assets/', {
                'address': f'Address {i}',
                'city': 'Test City',
                'price': 100000,
                'rooms': 3
            })
            assert response.status_code == status.HTTP_201_CREATED
        
        # Try to create 6th asset (should fail)
        response = self.client.post('/api/assets/', {
            'address': 'Address 5',
            'city': 'Test City',
            'price': 100000,
            'rooms': 3
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Upgrade to basic plan
        response = self.client.post('/api/plans/upgrade/', {
            'plan_name': 'basic'
        })
        assert response.status_code == status.HTTP_200_OK
        
        # Now should be able to create more assets
        response = self.client.post('/api/assets/', {
            'address': 'Address 5',
            'city': 'Test City',
            'price': 100000,
            'rooms': 3
        })
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify plan info shows upgrade
        response = self.client.get('/api/plans/info/')
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['plan_name'] == 'basic'
        assert data['limits']['assets']['limit'] == 25

    def test_multiple_users_different_plans(self):
        """Test multiple users with different plans creating assets"""
        # Free user - should hit limit at 5
        self.client.force_authenticate(user=self.free_user)
        
        for i in range(6):  # Try to create 6 assets
            response = self.client.post('/api/assets/', {
                'address': f'Free Address {i}',
                'city': 'Test City',
                'price': 100000,
                'rooms': 3
            })
            
            if i < 5:
                assert response.status_code == status.HTTP_201_CREATED
            else:
                assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Basic user - should be able to create 25 assets
        self.client.force_authenticate(user=self.basic_user)
        
        for i in range(26):  # Try to create 26 assets
            response = self.client.post('/api/assets/', {
                'address': f'Basic Address {i}',
                'city': 'Test City',
                'price': 100000,
                'rooms': 3
            })
            
            if i < 25:
                assert response.status_code == status.HTTP_201_CREATED
            else:
                assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Pro user - should be able to create unlimited assets
        self.client.force_authenticate(user=self.pro_user)
        
        for i in range(50):  # Create 50 assets
            response = self.client.post('/api/assets/', {
                'address': f'Pro Address {i}',
                'city': 'Test City',
                'price': 100000,
                'rooms': 3
            })
            assert response.status_code == status.HTTP_201_CREATED

    def test_plan_features_enforcement(self):
        """Test that plan features are properly enforced"""
        # Test free user - should not have advanced features
        self.client.force_authenticate(user=self.free_user)
        
        response = self.client.get('/api/plans/info/')
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['features']['advanced_analytics'] is False
        assert data['features']['data_export'] is False
        assert data['features']['api_access'] is False
        assert data['features']['priority_support'] is False
        assert data['features']['custom_reports'] is False
        
        # Test basic user - should have some advanced features
        self.client.force_authenticate(user=self.basic_user)
        
        response = self.client.get('/api/plans/info/')
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['features']['advanced_analytics'] is True
        assert data['features']['data_export'] is True
        assert data['features']['api_access'] is False
        assert data['features']['priority_support'] is False
        assert data['features']['custom_reports'] is False
        
        # Test pro user - should have all features
        self.client.force_authenticate(user=self.pro_user)
        
        response = self.client.get('/api/plans/info/')
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['features']['advanced_analytics'] is True
        assert data['features']['data_export'] is True
        assert data['features']['api_access'] is True
        assert data['features']['priority_support'] is True
        assert data['features']['custom_reports'] is True

    def test_plan_limits_consistency(self):
        """Test that plan limits are consistent across different operations"""
        # Test basic user
        self.client.force_authenticate(user=self.basic_user)
        
        # Get initial plan info
        response = self.client.get('/api/plans/info/')
        assert response.status_code == status.HTTP_200_OK
        
        initial_data = response.json()
        initial_assets_used = initial_data['limits']['assets']['used']
        asset_limit = initial_data['limits']['assets']['limit']
        
        # Create assets and verify usage updates
        for i in range(5):
            response = self.client.post('/api/assets/', {
                'address': f'Consistency Test Address {i}',
                'city': 'Test City',
                'price': 100000,
                'rooms': 3
            })
            assert response.status_code == status.HTTP_201_CREATED
            
            # Check that usage is updated
            response = self.client.get('/api/plans/info/')
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            expected_used = initial_assets_used + i + 1
            assert data['limits']['assets']['used'] == expected_used
            assert data['limits']['assets']['remaining'] == asset_limit - expected_used

    def test_plan_expiration_handling(self):
        """Test handling of expired plans"""
        from datetime import datetime, timedelta
        
        # Create user with expired plan
        expired_user = User.objects.create_user(
            username='expireduser',
            email='expired@example.com',
            password='testpass123'
        )
        
        expired_date = datetime.now() - timedelta(days=1)
        UserPlan.objects.create(
            user=expired_user,
            plan_type=self.basic_plan,
            is_active=True,
            expires_at=expired_date
        )
        
        self.client.force_authenticate(user=expired_user)
        
        # Should still work (plan is active in DB, just expired)
        response = self.client.post('/api/assets/', {
            'address': 'Expired User Address',
            'city': 'Test City',
            'price': 100000,
            'rooms': 3
        })
        assert response.status_code == status.HTTP_201_CREATED
        
        # Plan info should show expired status
        response = self.client.get('/api/plans/info/')
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['is_expired'] is True

    def test_concurrent_asset_creation(self):
        """Test concurrent asset creation with plan limits"""
        import threading
        import time
        
        results = []
        errors = []
        
        def create_asset(user, index):
            """Helper function to create an asset"""
            client = APIClient()
            client.force_authenticate(user=user)
            
            try:
                response = client.post('/api/assets/', {
                    'address': f'Concurrent Address {index}',
                    'city': 'Test City',
                    'price': 100000,
                    'rooms': 3
                })
                results.append((index, response.status_code))
            except Exception as e:
                errors.append((index, str(e)))
        
        # Create multiple threads to create assets concurrently
        threads = []
        for i in range(8):  # Try to create 8 assets (more than free limit of 5)
            thread = threading.Thread(target=create_asset, args=(self.free_user, i))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        success_count = sum(1 for _, status_code in results if status_code == 201)
        forbidden_count = sum(1 for _, status_code in results if status_code == 403)
        
        # Should have exactly 5 successful creations and 3 forbidden
        assert success_count == 5
        assert forbidden_count == 3
        assert len(errors) == 0

    def test_plan_service_integration_with_api(self):
        """Test that PlanService integrates properly with API endpoints"""
        # Test direct service calls
        plan_info = PlanService.get_user_plan_info(self.basic_user)
        assert plan_info['plan_name'] == 'basic'
        
        # Test validation
        validation_result = PlanService.validate_asset_creation(self.basic_user)
        assert validation_result['can_create'] is True
        
        # Test usage update
        initial_usage = self.basic_user.current_plan.assets_used
        PlanService.update_asset_usage(self.basic_user, 1)
        
        self.basic_user.current_plan.refresh_from_db()
        assert self.basic_user.current_plan.assets_used == initial_usage + 1
        
        # Test upgrade
        upgrade_result = PlanService.upgrade_user_plan(self.basic_user, 'pro')
        assert upgrade_result['success'] is True
        
        self.basic_user.refresh_from_db()
        assert self.basic_user.current_plan.plan_type == self.pro_plan

    def test_error_handling_and_messages(self):
        """Test proper error handling and user-friendly messages"""
        # Test limit exceeded error message
        self.client.force_authenticate(user=self.free_user)
        
        # Create 5 assets to reach limit
        for i in range(5):
            response = self.client.post('/api/assets/', {
                'address': f'Error Test Address {i}',
                'city': 'Test City',
                'price': 100000,
                'rooms': 3
            })
            assert response.status_code == status.HTTP_201_CREATED
        
        # Try to create 6th asset
        response = self.client.post('/api/assets/', {
            'address': 'Error Test Address 5',
            'city': 'Test City',
            'price': 100000,
            'rooms': 3
        })
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        
        # Check error message structure
        assert 'error' in data
        assert 'message' in data
        assert 'current_plan' in data
        assert 'asset_limit' in data
        assert 'assets_used' in data
        assert 'remaining' in data
        
        # Check Hebrew error message
        assert 'הגעת למגבלת הנכסים' in data['message']
        assert 'Free Plan' in data['current_plan']
        assert data['asset_limit'] == 5
        assert data['assets_used'] == 5
        assert data['remaining'] == 0

    def test_plan_limits_with_different_asset_types(self):
        """Test that plan limits apply to all asset types consistently"""
        # Test with different asset configurations
        asset_configs = [
            {'address': 'Apartment 1', 'city': 'Tel Aviv', 'price': 2000000, 'rooms': 3},
            {'address': 'House 1', 'city': 'Haifa', 'price': 1500000, 'rooms': 4},
            {'address': 'Penthouse 1', 'city': 'Jerusalem', 'price': 3000000, 'rooms': 5},
            {'address': 'Studio 1', 'city': 'Eilat', 'price': 800000, 'rooms': 1},
            {'address': 'Villa 1', 'city': 'Herzliya', 'price': 5000000, 'rooms': 6},
        ]
        
        self.client.force_authenticate(user=self.free_user)
        
        # Create assets with different configurations
        for i, config in enumerate(asset_configs):
            response = self.client.post('/api/assets/', config)
            
            if i < 5:  # First 5 should succeed
                assert response.status_code == status.HTTP_201_CREATED
            else:  # 6th should fail
                assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Verify final count
        response = self.client.get('/api/plans/info/')
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['limits']['assets']['used'] == 5
        assert data['limits']['assets']['remaining'] == 0
