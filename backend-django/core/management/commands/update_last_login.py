from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Update last_login field for users who have logged in but have null last_login'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find users with null last_login but who have been active recently
        # (e.g., have updated_at within last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        
        users_to_update = User.objects.filter(
            last_login__isnull=True,
            updated_at__gte=thirty_days_ago
        )
        
        count = users_to_update.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('No users found with null last_login that need updating.')
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would update {count} users:')
            )
            for user in users_to_update:
                self.stdout.write(f'  - {user.email} (updated: {user.updated_at})')
        else:
            # Update last_login to updated_at for these users
            updated_count = 0
            for user in users_to_update:
                user.last_login = user.updated_at
                user.save(update_fields=['last_login'])
                updated_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated last_login for {updated_count} users.')
            )
