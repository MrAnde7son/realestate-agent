from django.core.management.base import BaseCommand
from core.tasks import rollup_analytics


class Command(BaseCommand):
    help = 'Run analytics rollup to aggregate events into daily summaries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to rollup (YYYY-MM-DD). Defaults to today.',
        )

    def handle(self, *args, **options):
        if options['date']:
            from datetime import datetime
            from core.analytics import rollup_day
            date = datetime.strptime(options['date'], '%Y-%m-%d').date()
            rollup_day(date)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully rolled up analytics for {date}')
            )
        else:
            rollup_analytics.run()
            self.stdout.write(
                self.style.SUCCESS('Successfully rolled up analytics for today')
            )
