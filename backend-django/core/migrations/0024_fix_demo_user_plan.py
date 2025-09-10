from django.db import migrations
from decimal import Decimal


def fix_demo_user_plan(apps, schema_editor):
    """Change demo user from basic plan to free plan."""
    User = apps.get_model('core', 'User')
    PlanType = apps.get_model('core', 'PlanType')
    
    try:
        # Get or create free plan
        free_plan, _ = PlanType.objects.get_or_create(
            name='free',
            defaults={
                'display_name': 'Free Plan',
                'description': 'Free plan for basic users',
                'price': Decimal('0.00'),
                'currency': 'ILS',
                'billing_period': 'monthly',
                'asset_limit': 5,
                'report_limit': 10,
                'alert_limit': 5,
                'advanced_analytics': False,
                'data_export': False,
                'api_access': False,
                'priority_support': False,
                'custom_reports': False,
                'is_active': True
            }
        )
        
        # Update demo user to free plan
        try:
            demo_user = User.objects.get(email='demo@example.com')
            # Remove any existing plans
            demo_user.user_plans.all().delete()
            # Create new free plan
            demo_user.user_plans.create(
                plan_type=free_plan,
                is_active=True,
                auto_renew=True
            )
            print("✓ Changed demo@example.com to Free plan")
        except User.DoesNotExist:
            print("⚠ Demo user not found, skipping plan assignment")
            
    except Exception as e:
        print(f"⚠ Error updating demo user plan: {e}")


def reverse_fix_demo_user_plan(apps, schema_editor):
    """Revert demo user back to basic plan."""
    User = apps.get_model('core', 'User')
    PlanType = apps.get_model('core', 'PlanType')
    
    try:
        # Get basic plan
        basic_plan = PlanType.objects.get(name='basic')
        
        # Update demo user to basic plan
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user:
            # Remove any existing plans
            demo_user.user_plans.all().delete()
            # Create new basic plan
            demo_user.user_plans.create(
                plan_type=basic_plan,
                is_active=True,
                auto_renew=True
            )
            print("✓ Reverted demo@example.com to Basic plan")
            
    except Exception as e:
        print(f"⚠ Error reverting demo user plan: {e}")


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0023_assign_user_plans'),
    ]

    operations = [
        migrations.RunPython(fix_demo_user_plan, reverse_fix_demo_user_plan),
    ]
