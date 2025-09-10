"""
Management command to initialize plan types.
"""
from django.core.management.base import BaseCommand
from core.plan_service import PlanService


class Command(BaseCommand):
    help = 'Initialize plan types in the database'

    def handle(self, *args, **options):
        self.stdout.write('Initializing plan types...')
        
        try:
            created_plans = PlanService.get_or_create_plan_types()
            
            if created_plans:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created {len(created_plans)} plan types:'
                    )
                )
                for plan in created_plans:
                    self.stdout.write(f'  - {plan.display_name} ({plan.name})')
            else:
                self.stdout.write(
                    self.style.WARNING('All plan types already exist')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error initializing plans: {e}')
            )
            raise
