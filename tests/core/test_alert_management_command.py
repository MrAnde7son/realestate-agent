"""
Test Django management command for alert system.
"""

import os
from io import StringIO
from django.core.management import call_command
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

User = get_user_model()


class TestAlertManagementCommand(TestCase):
    """Test the test_alerts management command."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            phone="+972501234567",
            notify_email=True,
            notify_whatsapp=True
        )
    
    def test_command_without_arguments(self):
        """Test command without arguments."""
        out = StringIO()
        
        with patch.dict(os.environ, {
            "RESEND_API_KEY": "test_key",
            "RESEND_FROM": "test@example.com",
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_WHATSAPP_FROM": "whatsapp:+14155238886"
        }):
            with patch('orchestration.alerts.EmailAlert.send') as mock_email:
                with patch('orchestration.alerts.WhatsAppAlert.send') as mock_whatsapp:
                    call_command('test_alerts', stdout=out)
                    
                    # Check that both email and WhatsApp were called
                    mock_email.assert_called()
                    mock_whatsapp.assert_called()
    
    def test_command_with_email_argument(self):
        """Test command with specific email."""
        out = StringIO()
        
        with patch.dict(os.environ, {
            "RESEND_API_KEY": "test_key",
            "RESEND_FROM": "test@example.com"
        }):
            with patch('orchestration.alerts.EmailAlert.send') as mock_email:
                call_command('test_alerts', '--email', 'custom@example.com', stdout=out)
                
                mock_email.assert_called()
    
    def test_command_with_phone_argument(self):
        """Test command with specific phone."""
        out = StringIO()
        
        with patch.dict(os.environ, {
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_WHATSAPP_FROM": "whatsapp:+14155238886"
        }):
            with patch('orchestration.alerts.WhatsAppAlert.send') as mock_whatsapp:
                call_command('test_alerts', '--phone', '+972501234567', stdout=out)
                
                mock_whatsapp.assert_called()
    
    def test_command_with_user_id_argument(self):
        """Test command with specific user ID."""
        out = StringIO()
        
        with patch.dict(os.environ, {
            "RESEND_API_KEY": "test_key",
            "RESEND_FROM": "test@example.com",
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_WHATSAPP_FROM": "whatsapp:+14155238886"
        }):
            with patch('core.management.commands.test_alerts.create_notifier_for_user') as mock_create:
                mock_notifier = MagicMock()
                mock_notifier.alerts = [MagicMock(), MagicMock()]
                mock_create.return_value = mock_notifier
                
                call_command('test_alerts', '--user-id', str(self.user.id), stdout=out)
                
                mock_create.assert_called()
    
    def test_command_environment_config_display(self):
        """Test that environment configuration is displayed."""
        out = StringIO()
        
        with patch.dict(os.environ, {
            "RESEND_API_KEY": "test_key_12345",
            "RESEND_FROM": "test@example.com",
            "TWILIO_ACCOUNT_SID": "test_sid_67890",
            "TWILIO_AUTH_TOKEN": "test_token_abcdef",
            "TWILIO_WHATSAPP_FROM": "whatsapp:+14155238886"
        }):
            call_command('test_alerts', stdout=out)
            
            output = out.getvalue()
            
            # Check that environment variables are displayed
            assert "RESEND_API_KEY" in output
            assert "TWILIO_ACCOUNT_SID" in output
            assert "TWILIO_AUTH_TOKEN" in output
            assert "TWILIO_WHATSAPP_FROM" in output
    
    def test_command_missing_environment_variables(self):
        """Test command with missing environment variables."""
        out = StringIO()
        
        with patch.dict(os.environ, {}, clear=True):
            call_command('test_alerts', stdout=out)
            
            output = out.getvalue()
            
            # Check that missing variables are indicated
            assert "Not set" in output
    
    def test_command_creates_test_user(self):
        """Test that command creates test user when none exists."""
        out = StringIO()
        
        # Delete the test user
        User.objects.filter(email="test@example.com").delete()
        
        with patch.dict(os.environ, {
            "RESEND_API_KEY": "test_key",
            "RESEND_FROM": "test@example.com",
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_WHATSAPP_FROM": "whatsapp:+14155238886"
        }):
            with patch('orchestration.alerts.EmailAlert.send'):
                with patch('orchestration.alerts.WhatsAppAlert.send'):
                    call_command('test_alerts', stdout=out)
                    
                    # Check that test user was created
                    test_user = User.objects.filter(email="test@example.com").first()
                    assert test_user is not None
                    assert test_user.notify_email is True
                    assert test_user.notify_whatsapp is True
