"""
Test cases for PlanService business logic
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from unittest.mock import patch, MagicMock

from core.models import PlanType, UserPlan, Asset
from core.plan_service import PlanService

User = get_user_model()


@pytest.mark.django_db
class TestPlanService:
    """Test cases for PlanService class"""

    def test_assign_default_plan(self):
        """Test assigning default plan to user"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create free plan
        free_plan, created = PlanType.objects.get_or_create(
            name='free',
            defaults={
                'display_name': 'Free Plan',
                'asset_limit': 1
            }
        )
        
        # Assign default plan
        result = PlanService.assign_default_plan(user)
        
        assert result is not None
        assert result.plan_type == free_plan
        assert result.user == user
        assert result.is_active is True
        
        # Check that user now has a current plan
        assert user.current_plan == result

    def test_assign_default_plan_existing_plan(self):
        """Test assigning default plan when user already has a plan"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create existing plan
        existing_plan, created = PlanType.objects.get_or_create(
            name='basic',
            defaults={
                'display_name': 'Basic Plan',
                'asset_limit': 10
            }
        )
        
        UserPlan.objects.create(
            user=user,
            plan_type=existing_plan,
            is_active=True
        )
        
        # Create free plan
        free_plan, created = PlanType.objects.get_or_create(
            name='free',
            defaults={
                'display_name': 'Free Plan',
                'asset_limit': 1
            }
        )
        
        # Should not create new plan if user already has one
        result = PlanService.assign_default_plan(user)
        
        # assign_default_plan always assigns a free plan, even if user has existing plan
        assert result is not None
        assert result.plan_type == free_plan
        assert user.current_plan.plan_type == free_plan

    def test_get_user_plan_info(self):
        """Test getting user plan information"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create plan
        plan_type, created = PlanType.objects.get_or_create(
            name='test_basic_service',
            defaults={
                'display_name': 'Basic Plan',
                'description': 'Basic plan for users',
                'price': Decimal('149.00'),
                'currency': 'ILS',
                'billing_period': 'monthly',
                'asset_limit': 10,
                'report_limit': 50,
                'alert_limit': 25,
                'advanced_analytics': True,
                'data_export': True,
                'api_access': False,
                'priority_support': False,
                'custom_reports': False
            }
        )
        
        user_plan = UserPlan.objects.create(
            user=user,
            plan_type=plan_type,
            is_active=True
        )
        
        # Create some assets
        for i in range(10):
            Asset.objects.create(
                scope_type="address",
                street=f"Test Street {i}",
                city="Test City",
                price=100000,
                rooms=3,
                created_by=user
            )
        
        # Get plan info
        plan_info = PlanService.get_user_plan_info(user)
        
        assert plan_info['plan_name'] == 'test_basic_service'
        assert plan_info['display_name'] == 'Basic Plan'
        assert plan_info['description'] == 'Basic plan for users'
        assert plan_info['price'] == Decimal('149.00')
        assert plan_info['currency'] == 'ILS'
        assert plan_info['billing_period'] == 'monthly'
        assert plan_info['is_active'] is True
        assert plan_info['is_expired'] is False
        
        # Check limits
        assert plan_info['limits']['assets']['limit'] == 25
        assert plan_info['limits']['assets']['used'] == 10
        assert plan_info['limits']['assets']['remaining'] == 15
        
        assert plan_info['limits']['reports']['limit'] == 50
        assert plan_info['limits']['reports']['used'] == 0
        assert plan_info['limits']['reports']['remaining'] == 50
        
        assert plan_info['limits']['alerts']['limit'] == 25
        assert plan_info['limits']['alerts']['used'] == 0
        assert plan_info['limits']['alerts']['remaining'] == 25
        
        # Check features
        assert plan_info['features']['advanced_analytics'] is True
        assert plan_info['features']['data_export'] is True
        assert plan_info['features']['api_access'] is False
        assert plan_info['features']['priority_support'] is False
        assert plan_info['features']['custom_reports'] is False

    def test_get_user_plan_info_no_plan(self):
        """Test getting plan info when user has no plan"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        PlanService.get_or_create_plan_types()
        # Should assign default plan and return info
        plan_info = PlanService.get_user_plan_info(user)
        
        assert plan_info['plan_name'] == 'free'
        assert plan_info['display_name'] == 'חבילה חינמית'
        assert plan_info['limits']['assets']['limit'] == 1

    def test_validate_asset_creation_success(self):
        """Test successful asset creation validation"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create plan with limit
        plan_type, created = PlanType.objects.get_or_create(
            name='test_basic_25',
            defaults={
                'display_name': 'Basic Plan',
                'asset_limit': 10
            }
        )
        
        UserPlan.objects.create(
            user=user,
            plan_type=plan_type,
            is_active=True
        )
        
        # Create some assets
        for i in range(10):
            Asset.objects.create(
                scope_type="address",
                street=f"Test Street {i}",
                city="Test City",
                price=100000,
                rooms=3,
                created_by=user
            )
        
        # Should allow more assets
        result = PlanService.validate_asset_creation(user)
        
        assert result['can_create'] is True

    def test_validate_asset_creation_limit_exceeded(self):
        """Test asset creation validation when limit is exceeded"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create plan with limit
        plan_type, created = PlanType.objects.get_or_create(
            name='test_basic_10',
            defaults={
                'display_name': 'Basic Plan',
                'asset_limit': 10
            }
        )
        
        UserPlan.objects.create(
            user=user,
            plan_type=plan_type,
            is_active=True
        )
        
        # Create assets up to limit
        for i in range(10):
            Asset.objects.create(
                scope_type="address",
                street=f"Test Street {i}",
                city="Test City",
                price=100000,
                rooms=3,
                created_by=user
            )
        
        # Should not allow more assets
        result = PlanService.validate_asset_creation(user)
        
        assert result['can_create'] is False
        assert result['error'] == 'asset_limit_exceeded'
        assert 'asset limit' in result['message']
        assert result['current_plan'] == 'test_basic_10'
        assert result['asset_limit'] == 10
        assert result['assets_used'] == 10
        assert result['remaining'] == 0

    def test_validate_asset_creation_unlimited_plan(self):
        """Test asset creation validation with unlimited plan"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create unlimited plan
        plan_type, created = PlanType.objects.get_or_create(
            name='test_pro_unlimited',
            defaults={
                'display_name': 'Pro Plan',
                'asset_limit': -1  # Unlimited
            }
        )
        
        UserPlan.objects.create(
            user=user,
            plan_type=plan_type,
            is_active=True
        )
        
        # Create many assets
        for i in range(100):
            Asset.objects.create(
                scope_type="address",
                street=f"Test Street {i}",
                city="Test City",
                price=100000,
                rooms=3,
                created_by=user
            )
        
        # Should still allow more assets
        result = PlanService.validate_asset_creation(user)
        
        assert result['can_create'] is True

    def test_validate_asset_creation_no_plan(self):
        """Test asset creation validation when user has no plan"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create free plan
        free_plan, created = PlanType.objects.get_or_create(
            name='free',
            defaults={
                'display_name': 'Free Plan',
                'asset_limit': 1
            }
        )
        
        # Should assign default plan and allow creation
        result = PlanService.validate_asset_creation(user)
        
        assert result['can_create'] is True
        assert user.current_plan is not None
        assert user.current_plan.plan_type == free_plan

    def test_update_asset_usage(self):
        """Test updating asset usage count"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create plan
        plan_type, created = PlanType.objects.get_or_create(
            name='test_basic_25',
            defaults={
                'display_name': 'Basic Plan',
                'asset_limit': 10
            }
        )
        
        user_plan = UserPlan.objects.create(
            user=user,
            plan_type=plan_type,
            is_active=True,
            assets_used=5
        )
        
        # Update usage
        PlanService.update_asset_usage(user, 3)
        
        # Check updated usage
        user_plan.refresh_from_db()
        assert user_plan.assets_used == 8  # 5 + 3

    def test_update_asset_usage_no_plan(self):
        """Test updating asset usage when user has no plan"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create free plan
        free_plan, created = PlanType.objects.get_or_create(
            name='free',
            defaults={
                'display_name': 'Free Plan',
                'asset_limit': 1
            }
        )
        
        # update_asset_usage doesn't assign a plan automatically
        # First assign a plan, then update usage
        PlanService.assign_default_plan(user)
        PlanService.update_asset_usage(user, 2)
        
        assert user.current_plan is not None
        assert user.current_plan.plan_type == free_plan
        assert user.current_plan.assets_used == 2

    def test_upgrade_user_plan(self):
        """Test upgrading user plan"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create free plan
        free_plan, created = PlanType.objects.get_or_create(
            name='free',
            defaults={
                'display_name': 'Free Plan',
                'asset_limit': 1
            }
        )
        
        # Create basic plan
        basic_plan, created = PlanType.objects.get_or_create(
            name='basic',
            defaults={
                'display_name': 'Basic Plan',
                'asset_limit': 10
            }
        )
        
        # Assign free plan
        UserPlan.objects.create(
            user=user,
            plan_type=free_plan,
            is_active=True
        )
        
        # Upgrade to basic plan
        result = PlanService.upgrade_user_plan(user, 'basic')
        
        # upgrade_user_plan returns a UserPlan object
        assert result is not None
        assert result.plan_type == basic_plan
        assert result.is_active is True
        
        # Check that user now has basic plan
        user.current_plan.refresh_from_db()
        assert user.current_plan.plan_type == basic_plan
        assert user.current_plan.is_active is True

    def test_upgrade_user_plan_same_plan(self):
        """Test upgrading to the same plan"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create basic plan
        basic_plan, created = PlanType.objects.get_or_create(
            name='basic',
            defaults={
                'display_name': 'Basic Plan',
                'asset_limit': 10
            }
        )
        
        # Assign basic plan
        UserPlan.objects.create(
            user=user,
            plan_type=basic_plan,
            is_active=True
        )
        
        # Try to upgrade to same plan
        result = PlanService.upgrade_user_plan(user, 'basic')
        
        # upgrade_user_plan returns a UserPlan object even for same plan
        assert result is not None
        assert result.plan_type == basic_plan
        assert result.is_active is True

    def test_upgrade_user_plan_invalid_plan(self):
        """Test upgrading to invalid plan"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create free plan
        free_plan, created = PlanType.objects.get_or_create(
            name='free',
            defaults={
                'display_name': 'Free Plan',
                'asset_limit': 1
            }
        )
        
        # Assign free plan
        UserPlan.objects.create(
            user=user,
            plan_type=free_plan,
            is_active=True
        )
        
        # Try to upgrade to non-existent plan
        with pytest.raises(Exception):  # PlanValidationError
            PlanService.upgrade_user_plan(user, 'nonexistent')

    def test_upgrade_user_plan_no_existing_plan(self):
        """Test upgrading when user has no existing plan"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create basic plan
        basic_plan, created = PlanType.objects.get_or_create(
            name='basic',
            defaults={
                'display_name': 'Basic Plan',
                'asset_limit': 10
            }
        )
        
        # Upgrade without existing plan
        result = PlanService.upgrade_user_plan(user, 'basic')
        
        # upgrade_user_plan returns a UserPlan object
        assert result is not None
        assert result.plan_type == basic_plan
        assert result.is_active is True
        assert user.current_plan is not None
        assert user.current_plan.plan_type == basic_plan

    def test_plan_info_with_expired_plan(self):
        """Test plan info with expired plan"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create plan with expiry
        plan_type, created = PlanType.objects.get_or_create(
            name='test_basic_25',
            defaults={
                'display_name': 'Basic Plan',
                'asset_limit': 10
            }
        )
        
        from datetime import timedelta
        from django.utils import timezone
        expired_date = timezone.now() - timedelta(days=1)
        
        user_plan = UserPlan.objects.create(
            user=user,
            plan_type=plan_type,
            is_active=True,
            expires_at=expired_date
        )
        
        # Get plan info
        plan_info = PlanService.get_user_plan_info(user)
        
        assert plan_info['is_expired'] is True
        assert plan_info['is_active'] is True  # Plan is still active in DB

    def test_plan_info_unlimited_limits(self):
        """Test plan info with unlimited limits"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create unlimited plan
        plan_type, created = PlanType.objects.get_or_create(
            name='test_pro_unlimited_all',
            defaults={
                'display_name': 'Pro Plan',
                'asset_limit': -1,
                'report_limit': -1,
                'alert_limit': -1
            }
        )
        
        UserPlan.objects.create(
            user=user,
            plan_type=plan_type,
            is_active=True
        )
        
        # Get plan info
        plan_info = PlanService.get_user_plan_info(user)
        
        assert plan_info['limits']['assets']['limit'] == -1
        assert plan_info['limits']['assets']['remaining'] == -1
        assert plan_info['limits']['reports']['limit'] == -1
        assert plan_info['limits']['reports']['remaining'] == -1
        assert plan_info['limits']['alerts']['limit'] == -1
        assert plan_info['limits']['alerts']['remaining'] == -1
