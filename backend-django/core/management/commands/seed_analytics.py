from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, time
from core.models import AnalyticsEvent, AnalyticsDaily
from core.analytics import rollup_day


class Command(BaseCommand):
    help = 'Seed sample analytics data for testing'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Seeding analytics data...')
        
        # Create sample events for the last 30 days
        today = timezone.now().date()
        
        for i in range(30):
            date = today - timedelta(days=i)
            
            # Create some sample events for each day
            events_to_create = []
            
            # Random number of events per day (0-10)
            import random
            num_events = random.randint(0, 10)
            
            for j in range(num_events):
                event_types = ['user_signup', 'asset_create', 'report_success', 'alert_send', 'collector_fail', 'report_fail']
                event = random.choice(event_types)
                
                # Create event with random timestamp within the day
                hour = random.randint(0, 23)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                created_at = timezone.datetime.combine(date, time(hour, minute, second))
                
                events_to_create.append(
                    AnalyticsEvent(
                        event=event,
                        created_at=created_at,
                        source=random.choice(['yad2', 'mavat', 'gov', 'gis']) if 'fail' in event else None,
                        error_code=random.choice(['timeout', 'auth_error', 'parse_error', 'network_error']) if 'fail' in event else None,
                        meta={'test': True}
                    )
                )
            
            # Bulk create events for this day
            if events_to_create:
                AnalyticsEvent.objects.bulk_create(events_to_create)
                self.stdout.write(f'✅ Created {len(events_to_create)} events for {date}')
            
            # Roll up the day's data
            rollup_day(date)
        
        self.stdout.write(
            self.style.SUCCESS('🎉 Successfully seeded analytics data!')
        )
