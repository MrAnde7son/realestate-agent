"""
Plan validation and management service.
"""
import logging
from typing import Optional, Dict, Any
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import PlanType, UserPlan
from .constants import PLAN_LIMITS, PLAN_DISPLAY_NAMES, PLAN_DESCRIPTIONS

logger = logging.getLogger(__name__)
User = get_user_model()


class PlanValidationError(Exception):
    """Exception raised when plan validation fails."""
    pass


class PlanService:
    """Service for managing user plans and validating limits."""
    
    @staticmethod
    def get_or_create_plan_types():
        """Create plan types if they don't exist."""
        created_plans = []
        
        for plan_name, limits in PLAN_LIMITS.items():
            plan_type, created = PlanType.objects.get_or_create(
                name=plan_name,
                defaults={
                    'display_name': PLAN_DISPLAY_NAMES.get(plan_name, plan_name.title()),
                    'description': PLAN_DESCRIPTIONS.get(plan_name, ''),
                    'price': 0 if plan_name == 'free' else (149 if plan_name == 'basic' else 299),
                    'currency': 'ILS',
                    'billing_period': 'monthly',
                    **limits
                }
            )
            if created:
                created_plans.append(plan_type)
                logger.info(f"Created plan type: {plan_type.name}")
        
        return created_plans
    
    @staticmethod
    def assign_free_plan_to_user(user: User) -> UserPlan:
        """Assign free plan to a new user."""
        try:
            free_plan = PlanType.objects.get(name='free')
        except PlanType.DoesNotExist:
            # Create plan types if they don't exist
            PlanService.get_or_create_plan_types()
            free_plan = PlanType.objects.get(name='free')
        
        # Deactivate any existing active plans
        UserPlan.objects.filter(user=user, is_active=True).update(is_active=False)
        
        # Create new free plan
        user_plan = UserPlan.objects.create(
            user=user,
            plan_type=free_plan,
            is_active=True
        )
        
        logger.info(f"Assigned free plan to user: {user.email}")
        return user_plan
    
    @staticmethod
    def validate_asset_creation(user: User) -> Dict[str, Any]:
        """Validate if user can create a new asset."""
        try:
            user_plan = user.current_plan
            if not user_plan:
                # User has no plan, assign free plan
                user_plan = PlanService.assign_free_plan_to_user(user)
            
            # Check if plan is expired
            if user_plan.is_expired():
                return {
                    'can_create': False,
                    'error': 'plan_expired',
                    'message': 'Your plan has expired. Please renew your subscription.',
                    'current_plan': user_plan.plan_type.name,
                    'asset_limit': user_plan.plan_type.asset_limit,
                    'assets_used': user_plan.assets_used
                }
            
            # Check asset limit
            asset_limit = user_plan.plan_type.asset_limit
            assets_used = user.created_assets.count()
            
            if asset_limit == -1:  # Unlimited
                return {
                    'can_create': True,
                    'current_plan': user_plan.plan_type.name,
                    'asset_limit': -1,
                    'assets_used': assets_used,
                    'remaining': -1
                }
            
            if assets_used >= asset_limit:
                return {
                    'can_create': False,
                    'error': 'asset_limit_exceeded',
                    'message': f'You have reached your asset limit of {asset_limit}. Please upgrade your plan to add more assets.',
                    'current_plan': user_plan.plan_type.name,
                    'asset_limit': asset_limit,
                    'assets_used': assets_used,
                    'remaining': 0
                }
            
            return {
                'can_create': True,
                'current_plan': user_plan.plan_type.name,
                'asset_limit': asset_limit,
                'assets_used': assets_used,
                'remaining': asset_limit - assets_used
            }
            
        except Exception as e:
            logger.error(f"Error validating asset creation for user {user.email}: {e}")
            return {
                'can_create': False,
                'error': 'validation_error',
                'message': 'An error occurred while validating your plan. Please try again.',
                'current_plan': 'unknown',
                'asset_limit': 5,
                'assets_used': 0
            }
    
    @staticmethod
    def update_asset_usage(user: User, delta: int = 1):
        """Update asset usage count for user."""
        try:
            user_plan = user.current_plan
            if user_plan:
                user_plan.assets_used = max(0, user_plan.assets_used + delta)
                user_plan.save(update_fields=['assets_used'])
                logger.info(f"Updated asset usage for user {user.email}: {user_plan.assets_used}")
        except Exception as e:
            logger.error(f"Error updating asset usage for user {user.email}: {e}")
    
    @staticmethod
    def get_user_plan_info(user: User) -> Dict[str, Any]:
        """Get comprehensive plan information for user."""
        try:
            user_plan = user.current_plan
            if not user_plan:
                # User has no plan, assign free plan
                user_plan = PlanService.assign_free_plan_to_user(user)
            
            plan_type = user_plan.plan_type
            assets_used = user.created_assets.count()
            
            return {
                'plan_name': plan_type.name,
                'display_name': plan_type.display_name,
                'description': plan_type.description,
                'price': float(plan_type.price),
                'currency': plan_type.currency,
                'billing_period': plan_type.billing_period,
                'is_active': user_plan.is_active,
                'is_expired': user_plan.is_expired(),
                'expires_at': user_plan.expires_at.isoformat() if user_plan.expires_at else None,
                'limits': {
                    'assets': {
                        'limit': plan_type.asset_limit,
                        'used': assets_used,
                        'remaining': plan_type.asset_limit - assets_used if plan_type.asset_limit != -1 else -1
                    },
                    'reports': {
                        'limit': plan_type.report_limit,
                        'used': user_plan.reports_used,
                        'remaining': plan_type.report_limit - user_plan.reports_used if plan_type.report_limit != -1 else -1
                    },
                    'alerts': {
                        'limit': plan_type.alert_limit,
                        'used': user_plan.alerts_used,
                        'remaining': plan_type.alert_limit - user_plan.alerts_used if plan_type.alert_limit != -1 else -1
                    }
                },
                'features': {
                    'advanced_analytics': plan_type.advanced_analytics,
                    'data_export': plan_type.data_export,
                    'api_access': plan_type.api_access,
                    'priority_support': plan_type.priority_support,
                    'custom_reports': plan_type.custom_reports,
                }
            }
        except Exception as e:
            logger.error(f"Error getting plan info for user {user.email}: {e}")
            return {
                'plan_name': 'free',
                'display_name': 'Free Plan',
                'description': 'Default free plan',
                'price': 0.0,
                'currency': 'ILS',
                'billing_period': 'monthly',
                'is_active': True,
                'is_expired': False,
                'expires_at': None,
                'limits': {
                    'assets': {'limit': 5, 'used': 0, 'remaining': 5},
                    'reports': {'limit': 10, 'used': 0, 'remaining': 10},
                    'alerts': {'limit': 5, 'used': 0, 'remaining': 5}
                },
                'features': {
                    'advanced_analytics': False,
                    'data_export': False,
                    'api_access': False,
                    'priority_support': False,
                    'custom_reports': False,
                }
            }
    
    @staticmethod
    def upgrade_user_plan(user: User, new_plan_name: str) -> UserPlan:
        """Upgrade user to a new plan."""
        try:
            new_plan_type = PlanType.objects.get(name=new_plan_name)
            
            # Deactivate current plan
            UserPlan.objects.filter(user=user, is_active=True).update(is_active=False)
            
            # Create new plan
            user_plan = UserPlan.objects.create(
                user=user,
                plan_type=new_plan_type,
                is_active=True
            )
            
            logger.info(f"Upgraded user {user.email} to plan: {new_plan_name}")
            return user_plan
            
        except PlanType.DoesNotExist:
            raise PlanValidationError(f"Plan '{new_plan_name}' does not exist")
        except Exception as e:
            logger.error(f"Error upgrading user {user.email} to plan {new_plan_name}: {e}")
            raise PlanValidationError(f"Failed to upgrade plan: {str(e)}")
