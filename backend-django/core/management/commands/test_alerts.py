"""
Django management command to test alert functionality.
Usage: python manage.py test_alerts
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from orchestration.alerts import EmailAlert, WhatsAppAlert, create_notifier_for_user
import os

User = get_user_model()


class Command(BaseCommand):
    help = 'Test alert system functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to test with',
            default=None
        )
        parser.add_argument(
            '--phone',
            type=str,
            help='Phone number to test with',
            default=None
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID to test notifier creation',
            default=None
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🧪 Testing Alert System...\n'))

        # Test environment configuration
        self.test_environment_config()

        # Test email alert
        if options['email']:
            self.test_email_alert(options['email'])
        else:
            self.test_email_alert()

        # Test WhatsApp alert
        if options['phone']:
            self.test_whatsapp_alert(options['phone'])
        else:
            self.test_whatsapp_alert()

        # Test user notifier
        if options['user_id']:
            self.test_user_notifier(options['user_id'])
        else:
            self.test_user_notifier()

        self.stdout.write(self.style.SUCCESS('\n🏁 Alert System Tests Complete!'))

    def test_environment_config(self):
        """Test environment configuration."""
        self.stdout.write('📋 Environment Configuration:')
        
        config_vars = {
            'EMAIL_FROM': os.getenv('EMAIL_FROM'),
            'SENDGRID_API_KEY': os.getenv('SENDGRID_API_KEY'),
            'TWILIO_ACCOUNT_SID': os.getenv('TWILIO_ACCOUNT_SID'),
            'TWILIO_AUTH_TOKEN': os.getenv('TWILIO_AUTH_TOKEN'),
            'TWILIO_WHATSAPP_FROM': os.getenv('TWILIO_WHATSAPP_FROM'),
        }
        
        for var, value in config_vars.items():
            if value:
                self.stdout.write(f'  ✅ {var}: {"*" * min(len(value), 10)}...')
            else:
                self.stdout.write(self.style.WARNING(f'  ❌ {var}: Not set'))
        
        self.stdout.write('')

    def test_email_alert(self, email=None):
        """Test email alert functionality."""
        self.stdout.write('📧 Testing Email Alert...')
        
        if not email:
            email = os.getenv('ALERT_DEFAULT_EMAIL', 'test@example.com')
        
        alert = EmailAlert(email)
        
        test_message = """
        🏠 נכס חדש נמצא!
        
        📍 דירה 4 חדרים בתל אביב
        💰 מחיר: 2,500,000 ₪
        🔗 קישור: https://example.com/listing/123
        
        נדלנר - מערכת התראות נדלן
        """
        
        try:
            alert.send(test_message)
            self.stdout.write(self.style.SUCCESS('  ✅ Email alert sent successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Email alert failed: {e}'))

    def test_whatsapp_alert(self, phone=None):
        """Test WhatsApp alert functionality."""
        self.stdout.write('📱 Testing WhatsApp Alert...')
        
        if not phone:
            phone = os.getenv('ALERT_DEFAULT_WHATSAPP_TO', '+972501234567')
        
        alert = WhatsAppAlert(phone)
        
        test_message = """
        🏠 נכס חדש נמצא!
        
        📍 דירה 4 חדרים בתל אביב
        💰 מחיר: 2,500,000 ₪
        🔗 קישור: https://example.com/listing/123
        
        נדלנר - מערכת התראות נדלן
        """
        
        try:
            alert.send(test_message)
            self.stdout.write(self.style.SUCCESS('  ✅ WhatsApp alert sent successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ WhatsApp alert failed: {e}'))

    def test_user_notifier(self, user_id=None):
        """Test creating a notifier for a user."""
        self.stdout.write('👤 Testing User Notifier...')
        
        try:
            if user_id:
                user = User.objects.get(id=user_id)
            else:
                user = User.objects.filter(email__icontains="test").first()
                if not user:
                    self.stdout.write('  ⚠️  No test user found, creating one...')
                    user = User.objects.create_user(
                        username="testuser",
                        email="test@example.com",
                        phone="+972501234567",
                        notify_email=True,
                        notify_whatsapp=True
                    )
            
            # Create notifier
            criteria = {"city": "5000", "rooms": "4"}
            notifier = create_notifier_for_user(user, criteria)
            
            if notifier:
                self.stdout.write(self.style.SUCCESS('  ✅ User notifier created successfully'))
                self.stdout.write(f'     - Email enabled: {user.notify_email}')
                self.stdout.write(f'     - WhatsApp enabled: {user.notify_whatsapp}')
                self.stdout.write(f'     - Number of alert channels: {len(notifier.alerts)}')
            else:
                self.stdout.write(self.style.WARNING('  ⚠️  No notifier created (user may not have notification channels enabled)'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ User notifier test failed: {e}'))
