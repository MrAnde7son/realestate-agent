"""
Test cases for plan-related models (PlanType, UserPlan, User plan methods)
"""

import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import datetime, timedelta

from core.models import PlanType, UserPlan, Asset

User = get_user_model()


@pytest.mark.django_db
class TestPlanTypeModel:
    """Test cases for PlanType model"""

    def test_create_plan_type(self):
        """Test creating a plan type"""
        plan_type = PlanType.objects.create(
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
        
        assert plan_type.name == 'free'
        assert plan_type.display_name == 'Free Plan'
        assert plan_type.price == Decimal('0.00')
        assert plan_type.asset_limit == 5
        assert plan_type.is_active is True
        assert str(plan_type) == 'Free Plan (free)'

    def test_plan_type_choices(self):
        """Test plan type choices validation"""
        # Valid choices
        for choice in ['free', 'basic', 'pro']:
            plan_type = PlanType.objects.create(
                name=choice,
                display_name=f'{choice.title()} Plan',
                asset_limit=5
            )
            assert plan_type.name == choice

    def test_plan_type_defaults(self):
        """Test plan type default values"""
        plan_type = PlanType.objects.create(
            name='test',
            display_name='Test Plan'
        )
        
        assert plan_type.price == Decimal('0.00')
        assert plan_type.currency == 'ILS'
        assert plan_type.billing_period == 'monthly'
        assert plan_type.asset_limit == 5
        assert plan_type.report_limit == 10
        assert plan_type.alert_limit == 5
        assert plan_type.advanced_analytics is False
        assert plan_type.data_export is False
        assert plan_type.api_access is False
        assert plan_type.priority_support is False
        assert plan_type.custom_reports is False
        assert plan_type.is_active is True

    def test_plan_type_unique_name(self):
        """Test that plan type names must be unique"""
        PlanType.objects.create(
            name='free',
            display_name='Free Plan'
        )
        
        with pytest.raises(Exception):  # IntegrityError or ValidationError
            PlanType.objects.create(
                name='free',
                display_name='Another Free Plan'
            )


@pytest.mark.django_db
class TestUserPlanModel:
    """Test cases for UserPlan model"""

    def test_create_user_plan(self):
        """Test creating a user plan"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        plan_type = PlanType.objects.create(
            name='basic',
            display_name='Basic Plan',
            asset_limit=25
        )
        
        user_plan = UserPlan.objects.create(
            user=user,
            plan_type=plan_type,
            is_active=True,
            auto_renew=True
        )
        
        assert user_plan.user == user
        assert user_plan.plan_type == plan_type
        assert user_plan.is_active is True
        assert user_plan.auto_renew is True
        assert user_plan.assets_used == 0
        assert user_plan.reports_used == 0
        assert user_plan.alerts_used == 0

    def test_user_plan_defaults(self):
        """Test user plan default values"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        plan_type = PlanType.objects.create(
            name='free',
            display_name='Free Plan'
        )
        
        user_plan = UserPlan.objects.create(
            user=user,
            plan_type=plan_type
        )
        
        assert user_plan.is_active is True
        assert user_plan.auto_renew is True
        assert user_plan.assets_used == 0
        assert user_plan.reports_used == 0
        assert user_plan.alerts_used == 0
        assert user_plan.started_at is not None
        assert user_plan.expires_at is None

    def test_user_plan_expired(self):
        """Test user plan expiration logic"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        plan_type = PlanType.objects.create(
            name='basic',
            display_name='Basic Plan'
        )
        
        # Create expired plan
        expired_date = datetime.now() - timedelta(days=1)
        user_plan = UserPlan.objects.create(
            user=user,
            plan_type=plan_type,
            expires_at=expired_date
        )
        
        assert user_plan.is_expired() is True
        
        # Create non-expired plan
        future_date = datetime.now() + timedelta(days=30)
        user_plan_future = UserPlan.objects.create(
            user=user,
            plan_type=plan_type,
            expires_at=future_date
        )
        
        assert user_plan_future.is_expired() is False

    def test_user_plan_can_use_feature(self):
        """Test feature usage validation"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        plan_type = PlanType.objects.create(
            name='basic',
            display_name='Basic Plan',
            asset_limit=25,
            advanced_analytics=True,
            data_export=True
        )
        
        user_plan = UserPlan.objects.create(
            user=user,
            plan_type=plan_type,
            assets_used=10
        )
        
        # Test asset limit
        assert user_plan.can_use_feature('assets', 10) is True  # 10 + 10 = 20 < 25
        assert user_plan.can_use_feature('assets', 20) is False  # 10 + 20 = 30 > 25
        
        # Test unlimited features
        assert user_plan.can_use_feature('advanced_analytics') is True
        assert user_plan.can_use_feature('data_export') is True

    def test_user_plan_get_remaining_assets(self):
        """Test remaining assets calculation"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        plan_type = PlanType.objects.create(
            name='basic',
            display_name='Basic Plan',
            asset_limit=25
        )
        
        user_plan = UserPlan.objects.create(
            user=user,
            plan_type=plan_type,
            assets_used=10
        )
        
        assert user_plan.get_remaining_assets() == 15  # 25 - 10

    def test_user_plan_unlimited_assets(self):
        """Test unlimited assets handling"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        plan_type = PlanType.objects.create(
            name='pro',
            display_name='Pro Plan',
            asset_limit=-1  # Unlimited
        )
        
        user_plan = UserPlan.objects.create(
            user=user,
            plan_type=plan_type,
            assets_used=100
        )
        
        assert user_plan.get_remaining_assets() == -1  # Unlimited
        assert user_plan.can_use_feature('assets', 1000) is True


@pytest.mark.django_db
class TestUserPlanMethods:
    """Test cases for User model plan-related methods"""

    def test_user_current_plan_property(self):
        """Test user current_plan property"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # No plan initially
        assert user.current_plan is None
        
        # Create active plan
        plan_type = PlanType.objects.create(
            name='basic',
            display_name='Basic Plan'
        )
        
        user_plan = UserPlan.objects.create(
            user=user,
            plan_type=plan_type,
            is_active=True
        )
        
        assert user.current_plan == user_plan

    def test_user_get_asset_limit(self):
        """Test user get_asset_limit method"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # No plan - should return default limit
        assert user.get_asset_limit() == 5
        
        # With plan
        plan_type = PlanType.objects.create(
            name='basic',
            display_name='Basic Plan',
            asset_limit=25
        )
        
        UserPlan.objects.create(
            user=user,
            plan_type=plan_type,
            is_active=True
        )
        
        assert user.get_asset_limit() == 25

    def test_user_can_create_asset(self):
        """Test user can_create_asset method"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # No plan - should allow up to 5 assets
        assert user.can_create_asset() is True
        
        # Create 5 assets
        for i in range(5):
            Asset.objects.create(
                address=f"Test Address {i}",
                city="Test City",
                price=100000,
                rooms=3,
                created_by=user
            )
        
        # Should not allow more assets without plan
        assert user.can_create_asset() is False
        
        # Create basic plan
        plan_type = PlanType.objects.create(
            name='basic',
            display_name='Basic Plan',
            asset_limit=25
        )
        
        UserPlan.objects.create(
            user=user,
            plan_type=plan_type,
            is_active=True
        )
        
        # Should allow more assets with plan
        assert user.can_create_asset() is True

    def test_user_can_create_asset_with_plan_limits(self):
        """Test user can_create_asset with plan limits"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create basic plan with limit of 10
        plan_type = PlanType.objects.create(
            name='basic',
            display_name='Basic Plan',
            asset_limit=10
        )
        
        UserPlan.objects.create(
            user=user,
            plan_type=plan_type,
            is_active=True
        )
        
        # Create 10 assets
        for i in range(10):
            Asset.objects.create(
                address=f"Test Address {i}",
                city="Test City",
                price=100000,
                rooms=3,
                created_by=user
            )
        
        # Should not allow more assets
        assert user.can_create_asset() is False

    def test_user_can_create_asset_unlimited_plan(self):
        """Test user can_create_asset with unlimited plan"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create pro plan with unlimited assets
        plan_type = PlanType.objects.create(
            name='pro',
            display_name='Pro Plan',
            asset_limit=-1  # Unlimited
        )
        
        UserPlan.objects.create(
            user=user,
            plan_type=plan_type,
            is_active=True
        )
        
        # Create many assets
        for i in range(100):
            Asset.objects.create(
                address=f"Test Address {i}",
                city="Test City",
                price=100000,
                rooms=3,
                created_by=user
            )
        
        # Should still allow more assets
        assert user.can_create_asset() is True

    def test_user_multiple_plans_only_active_matters(self):
        """Test that only active plans are considered"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create inactive plan
        plan_type_inactive = PlanType.objects.create(
            name='free',
            display_name='Free Plan',
            asset_limit=5
        )
        
        UserPlan.objects.create(
            user=user,
            plan_type=plan_type_inactive,
            is_active=False
        )
        
        # Create active plan
        plan_type_active = PlanType.objects.create(
            name='basic',
            display_name='Basic Plan',
            asset_limit=25
        )
        
        UserPlan.objects.create(
            user=user,
            plan_type=plan_type_active,
            is_active=True
        )
        
        # Should use active plan limits
        assert user.get_asset_limit() == 25
        assert user.current_plan.plan_type == plan_type_active
