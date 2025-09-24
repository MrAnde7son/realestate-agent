from django.db import migrations
from core.plan_service import PlanService


def assign_user_plans(apps, schema_editor):
    """Assign specific plans to admin and demo users."""
    User = apps.get_model('core', 'User')
    PlanType = apps.get_model('core', 'PlanType')
    
    try:
        # Get or create plan types
        pro_plan, _ = PlanType.objects.get_or_create(
            name='pro',
            defaults={
                'display_name': 'Pro Plan',
                'description': 'Professional plan for power users',
                'price': 299.00,
                'currency': 'ILS',
                'billing_period': 'monthly',
                'asset_limit': -1,  # Unlimited
                'report_limit': -1,
                'alert_limit': -1,
                'advanced_analytics': True,
                'data_export': True,
                'api_access': True,
                'priority_support': True,
                'custom_reports': True,
                'is_active': True
            }
        )
        
        basic_plan, _ = PlanType.objects.get_or_create(
            name='basic',
            defaults={
                'display_name': 'Basic Plan',
                'description': 'Basic plan for advanced users',
                'price': 149.00,
                'currency': 'ILS',
                'billing_period': 'monthly',
                'asset_limit': 10,
                'report_limit': 50,
                'alert_limit': 25,
                'advanced_analytics': True,
                'data_export': True,
                'api_access': False,
                'priority_support': False,
                'custom_reports': False,
                'is_active': True
            }
        )
        
        # Assign pro plan to admin user
        try:
            admin_user = User.objects.get(email='admin@example.com')
            # Remove any existing plans
            admin_user.user_plans.all().delete()
            # Create new pro plan
            admin_user.user_plans.create(
                plan_type=pro_plan,
                is_active=True,
                auto_renew=True
            )
            print("✓ Assigned Pro plan to admin@example.com")
        except User.DoesNotExist:
            print("⚠ Admin user not found, skipping plan assignment")
        
        # Assign basic plan to demo user
        try:
            demo_user = User.objects.get(email='demo@example.com')
            # Remove any existing plans
            demo_user.user_plans.all().delete()
            # Create new basic plan
            demo_user.user_plans.create(
                plan_type=basic_plan,
                is_active=True,
                auto_renew=True
            )
            print("✓ Assigned Basic plan to demo@example.com")
        except User.DoesNotExist:
            print("⚠ Demo user not found, skipping plan assignment")
            
    except Exception as e:
        print(f"⚠ Error assigning user plans: {e}")


def reverse_assign_user_plans(apps, schema_editor):
    """Remove user plans (but keep the users)."""
    User = apps.get_model('core', 'User')
    
    try:
        # Remove plans from admin user
        admin_user = User.objects.filter(email='admin@example.com').first()
        if admin_user:
            admin_user.user_plans.all().delete()
            print("✓ Removed plan from admin@example.com")
        
        # Remove plans from demo user
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user:
            demo_user.user_plans.all().delete()
            print("✓ Removed plan from demo@example.com")
            
    except Exception as e:
        print(f"⚠ Error removing user plans: {e}")


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0022_plantype_userplan_and_more'),
    ]

    operations = [
        migrations.RunPython(assign_user_plans, reverse_assign_user_plans),
    ]
