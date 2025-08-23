from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Ensure admin and demo users exist (safe for production)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of admin users even if they exist',
        )
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check if users exist, do not create them',
        )

    def handle(self, *args, **options):
        if options['check_only']:
            self.check_users()
            return
        
        with transaction.atomic():
            # Check if we have any users
            total_users = User.objects.count()
            
            if total_users > 0 and not options['force']:
                self.stdout.write(
                    self.style.WARNING(
                        f'Database has {total_users} existing users. '
                        'Use --force to recreate admin users.'
                    )
                )
                self.check_users()
                return
            
            # Create or update admin user
            admin_user, created = User.objects.get_or_create(
                email='admin@example.com',
                defaults={
                    'username': 'admin',
                    'first_name': 'מנהל',
                    'last_name': 'מערכת',
                    'company': 'נדל״נר',
                    'role': 'מנהל מערכת',
                    'is_superuser': True,
                    'is_staff': True,
                    'is_active': True
                }
            )
            
            if created:
                admin_user.set_password('admin123')
                admin_user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Admin user created: {admin_user.email}')
                )
            else:
                # Update existing user to ensure it's active and has correct permissions
                admin_user.is_active = True
                admin_user.is_superuser = True
                admin_user.is_staff = True
                admin_user.save()
                self.stdout.write(f'✓ Admin user updated: {admin_user.email}')
            
            # Create or update demo user
            demo_user, created = User.objects.get_or_create(
                email='demo@example.com',
                defaults={
                    'username': 'demo',
                    'first_name': 'משתמש',
                    'last_name': 'דמו',
                    'company': 'נדל״ן דמו בע״מ',
                    'role': 'מתווך נדל״ן',
                    'is_active': True
                }
            )
            
            if created:
                demo_user.set_password('demo123')
                demo_user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Demo user created: {demo_user.email}')
                )
            else:
                # Update existing user to ensure it's active
                demo_user.is_active = True
                demo_user.save()
                self.stdout.write(f'✓ Demo user updated: {demo_user.email}')
            
            self.stdout.write(
                self.style.SUCCESS('\n🎉 Admin users ensured successfully!')
            )

    def check_users(self):
        """Check the status of admin users."""
        admin_user = User.objects.filter(email='admin@example.com').first()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        self.stdout.write('\n📊 User Status:')
        self.stdout.write('=' * 30)
        
        if admin_user:
            status = '✓ Active' if admin_user.is_active else '⚠ Inactive'
            superuser = '✓ Superuser' if admin_user.is_superuser else '✗ Not Superuser'
            self.stdout.write(f'Admin: {admin_user.email} - {status} - {superuser}')
        else:
            self.stdout.write(self.style.ERROR('Admin: ✗ Missing'))
        
        if demo_user:
            status = '✓ Active' if demo_user.is_active else '⚠ Inactive'
            self.stdout.write(f'Demo: {demo_user.email} - {status}')
        else:
            self.stdout.write(self.style.ERROR('Demo: ✗ Missing'))
        
        total_users = User.objects.count()
        self.stdout.write(f'\nTotal users in system: {total_users}')
        
        if total_users > 2:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠ Database has {total_users - 2} additional users '
                    '(likely client data)'
                )
            )
