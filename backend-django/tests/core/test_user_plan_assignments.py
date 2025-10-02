"""
Test cases for user plan assignments
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal

from core.models import PlanType, UserPlan
from core.plan_service import PlanService

User = get_user_model()


@pytest.mark.django_db
class TestUserPlanAssignments:
    """Test cases for specific user plan assignments"""

    def test_admin_user_has_pro_plan(self):
        """Test that admin@example.com has pro plan"""
        try:
            admin_user = User.objects.get(email='admin@example.com')
            
            # Check that admin has a plan
            assert admin_user.current_plan is not None
            
            # Check that it's the pro plan
            assert admin_user.current_plan.plan_type.name == 'pro'
            assert admin_user.current_plan.plan_type.display_name == 'Pro Plan'
            
            # Check pro plan features
            plan_type = admin_user.current_plan.plan_type
            assert plan_type.asset_limit == -1  # Unlimited
            assert plan_type.api_access is True
            assert plan_type.advanced_analytics is True
            assert plan_type.data_export is True
            assert plan_type.priority_support is True
            assert plan_type.custom_reports is True
            
            # Check that admin can create unlimited assets
            assert admin_user.can_create_asset() is True
            
        except User.DoesNotExist:
            pytest.skip("Admin user not found - may not be created in test environment")

    def test_demo_user_has_free_plan(self):
        """Test that demo@example.com has free plan"""
        try:
            PlanService.get_or_create_plan_types()
            demo_user = User.objects.get(email='demo@example.com')
            
            # Check that demo has a plan
            assert demo_user.current_plan is not None
            
            # Check that it's the free plan
            assert demo_user.current_plan.plan_type.name == 'free'
            assert demo_user.current_plan.plan_type.display_name == 'חבילה חינמית'
            
            # Check free plan features
            plan_type = demo_user.current_plan.plan_type
            assert plan_type.asset_limit == 1
            assert plan_type.api_access is False
            assert plan_type.advanced_analytics is False
            assert plan_type.data_export is False
            assert plan_type.priority_support is False
            assert plan_type.custom_reports is False
            
            # Check that demo can create assets up to limit
            assert demo_user.can_create_asset() is True
            
        except User.DoesNotExist:
            pytest.skip("Demo user not found - may not be created in test environment")

    def test_admin_user_plan_limits(self):
        """Test admin user plan limits and features"""
        try:
            admin_user = User.objects.get(email='admin@example.com')
            plan_info = admin_user.current_plan.plan_type
            
            # Test asset limits
            assert admin_user.get_asset_limit() == -1  # Unlimited
            
            # Test feature access
            assert plan_info.advanced_analytics is True
            assert plan_info.data_export is True
            assert plan_info.api_access is True
            assert plan_info.priority_support is True
            assert plan_info.custom_reports is True
            
            # Test unlimited asset creation
            # Even with many assets, should still be able to create more
            assert admin_user.can_create_asset() is True
            
        except User.DoesNotExist:
            pytest.skip("Admin user not found - may not be created in test environment")

    def test_demo_user_plan_limits(self):
        """Test demo user plan limits and features"""
        try:
            PlanService.get_or_create_plan_types()
            demo_user = User.objects.get(email='demo@example.com')
            plan_info = demo_user.current_plan.plan_type
            
            # Test asset limits (free plan has 1 asset)
            assert demo_user.get_asset_limit() == 1
            
            # Test feature access (free plan has no advanced features)
            assert plan_info.advanced_analytics is False
            assert plan_info.data_export is False
            assert plan_info.api_access is False
            assert plan_info.priority_support is False
            assert plan_info.custom_reports is False
            
            # Test limited asset creation
            # Should be able to create assets up to limit
            assert demo_user.can_create_asset() is True
            
        except User.DoesNotExist:
            pytest.skip("Demo user not found - may not be created in test environment")

    def test_plan_assignments_are_active(self):
        """Test that assigned plans are active"""
        try:
            admin_user = User.objects.get(email='admin@example.com')
            demo_user = User.objects.get(email='demo@example.com')
            
            # Check that both users have active plans
            assert admin_user.current_plan.is_active is True
            assert demo_user.current_plan.is_active is True
            
            # Check that plans are not expired
            assert admin_user.current_plan.is_expired() is False
            assert demo_user.current_plan.is_expired() is False
            
        except User.DoesNotExist:
            pytest.skip("Users not found - may not be created in test environment")

    def test_plan_assignments_have_correct_pricing(self):
        """Test that assigned plans have correct pricing"""
        try:
            admin_user = User.objects.get(email='admin@example.com')
            demo_user = User.objects.get(email='demo@example.com')
            
            # Check admin plan pricing
            admin_plan = admin_user.current_plan.plan_type
            assert admin_plan.price == Decimal('299.00')
            assert admin_plan.currency == 'ILS'
            assert admin_plan.billing_period == 'monthly'
            
            # Check demo plan pricing (free plan)
            demo_plan = demo_user.current_plan.plan_type
            assert demo_plan.price == Decimal('0.00')
            assert demo_plan.currency == 'ILS'
            assert demo_plan.billing_period == 'monthly'
            
        except User.DoesNotExist:
            pytest.skip("Users not found - may not be created in test environment")

    def test_plan_assignments_usage_tracking(self):
        """Test that plan assignments have proper usage tracking"""
        try:
            PlanService.get_or_create_plan_types()
            admin_user = User.objects.get(email='admin@example.com')
            demo_user = User.objects.get(email='demo@example.com')
            
            # Check initial usage counts
            assert admin_user.current_plan.assets_used == 0
            assert admin_user.current_plan.reports_used == 0
            assert admin_user.current_plan.alerts_used == 0
            
            assert demo_user.current_plan.assets_used == 0
            assert demo_user.current_plan.reports_used == 0
            assert demo_user.current_plan.alerts_used == 0
            
            # Check remaining assets calculation
            assert admin_user.current_plan.get_remaining_assets() == -1  # Unlimited
            assert demo_user.current_plan.get_remaining_assets() == 1  # Free plan limit
            
        except User.DoesNotExist:
            pytest.skip("Users not found - may not be created in test environment")

    def test_plan_assignments_auto_renew(self):
        """Test that assigned plans have auto-renew enabled"""
        try:
            admin_user = User.objects.get(email='admin@example.com')
            demo_user = User.objects.get(email='demo@example.com')
            
            # Check auto-renew settings
            assert admin_user.current_plan.auto_renew is True
            assert demo_user.current_plan.auto_renew is True
            
        except User.DoesNotExist:
            pytest.skip("Users not found - may not be created in test environment")
