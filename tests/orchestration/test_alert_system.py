"""
Test suite for the alert system.
Tests both email and WhatsApp alert functionality.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from orchestration.alerts import EmailAlert, WhatsAppAlert, create_notifier_for_user, create_notifier_for_alert_rule


class TestEmailAlert:
    """Test email alert functionality."""
    
    def test_email_alert_initialization(self):
        """Test EmailAlert initialization."""
        alert = EmailAlert("test@example.com")
        assert alert.to_email == "test@example.com"
        assert alert.host == os.getenv("SMTP_HOST")
        assert alert.user == os.getenv("SMTP_USER")
        assert alert.password == os.getenv("SMTP_PASSWORD")
        assert alert.from_email == os.getenv("EMAIL_FROM", os.getenv("SMTP_USER"))
    
    def test_email_alert_sendgrid_success(self):
        """Test email alert with SendGrid."""
        with patch.dict(os.environ, {"SENDGRID_API_KEY": "test_key", "EMAIL_FROM": "test@example.com"}):
            with patch('orchestration.alerts.sendgrid') as mock_sendgrid:
                with patch('orchestration.alerts.Mail') as mock_mail:
                    mock_client = MagicMock()
                    mock_sendgrid.SendGridAPIClient.return_value = mock_client
                    mock_mail.return_value = MagicMock()
                    
                    alert = EmailAlert("test@example.com")
                    alert.send("Test message")
                    
                    mock_client.send.assert_called_once()
    
    def test_email_alert_smtp_fallback(self):
        """Test email alert with SMTP fallback."""
        with patch.dict(os.environ, {
            "SENDGRID_API_KEY": "",
            "SMTP_HOST": "smtp.gmail.com",
            "SMTP_USER": "test@gmail.com",
            "SMTP_PASSWORD": "test_password",
            "EMAIL_FROM": "test@gmail.com"
        }):
            with patch('smtplib.SMTP') as mock_smtp:
                mock_server = MagicMock()
                mock_smtp.return_value.__enter__.return_value = mock_server
                
                alert = EmailAlert("test@example.com")
                alert.send("Test message")
                
                mock_server.starttls.assert_called_once()
                mock_server.login.assert_called_once()
                mock_server.sendmail.assert_called_once()
    
    def test_email_alert_no_config(self):
        """Test email alert with no configuration."""
        with patch.dict(os.environ, {
            "SENDGRID_API_KEY": "",
            "SMTP_HOST": "",
            "SMTP_USER": "",
            "SMTP_PASSWORD": "",
            "EMAIL_FROM": ""
        }):
            alert = EmailAlert("test@example.com")
            # Should not raise an exception, just skip sending
            alert.send("Test message")


class TestWhatsAppAlert:
    """Test WhatsApp alert functionality."""
    
    def test_whatsapp_alert_initialization(self):
        """Test WhatsAppAlert initialization."""
        alert = WhatsAppAlert("+972501234567")
        assert alert.to_number == "+972501234567"
        assert alert.account_sid == os.getenv("TWILIO_ACCOUNT_SID")
        assert alert.auth_token == os.getenv("TWILIO_AUTH_TOKEN")
        assert alert.from_number == os.getenv("TWILIO_WHATSAPP_FROM")
    
    def test_whatsapp_alert_success(self):
        """Test WhatsApp alert success."""
        with patch.dict(os.environ, {
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_WHATSAPP_FROM": "whatsapp:+14155238886"
        }):
            with patch('orchestration.alerts.Client') as mock_client:
                mock_twilio = MagicMock()
                mock_client.return_value = mock_twilio
                
                alert = WhatsAppAlert("+972501234567")
                alert.send("Test message")
                
                mock_twilio.messages.create.assert_called_once()
    
    def test_whatsapp_alert_no_config(self):
        """Test WhatsApp alert with no configuration."""
        with patch.dict(os.environ, {
            "TWILIO_ACCOUNT_SID": "",
            "TWILIO_AUTH_TOKEN": "",
            "TWILIO_WHATSAPP_FROM": ""
        }):
            alert = WhatsAppAlert("+972501234567")
            # Should not raise an exception, just skip sending
            alert.send("Test message")


class TestNotifier:
    """Test notifier functionality."""
    
    def test_create_notifier_for_user(self):
        """Test creating notifier for user."""
        # Mock user object
        user = MagicMock()
        user.email = "test@example.com"
        user.phone = "+972501234567"
        user.notify_email = True
        user.notify_whatsapp = True
        
        criteria = {"city": "5000", "rooms": "4"}
        
        with patch.dict(os.environ, {
            "SENDGRID_API_KEY": "test_key",
            "EMAIL_FROM": "test@example.com",
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_WHATSAPP_FROM": "whatsapp:+14155238886"
        }):
            notifier = create_notifier_for_user(user, criteria)
            
            assert notifier is not None
            assert notifier.criteria == criteria
            assert len(notifier.alerts) == 2  # Email + WhatsApp
    
    def test_create_notifier_for_user_email_only(self):
        """Test creating notifier for user with email only."""
        user = MagicMock()
        user.email = "test@example.com"
        user.phone = "+972501234567"
        user.notify_email = True
        user.notify_whatsapp = False
        
        criteria = {"city": "5000", "rooms": "4"}
        
        with patch.dict(os.environ, {
            "SENDGRID_API_KEY": "test_key",
            "EMAIL_FROM": "test@example.com"
        }):
            notifier = create_notifier_for_user(user, criteria)
            
            assert notifier is not None
            assert len(notifier.alerts) == 1  # Email only
    
    def test_create_notifier_for_user_no_channels(self):
        """Test creating notifier for user with no channels enabled."""
        user = MagicMock()
        user.email = "test@example.com"
        user.phone = "+972501234567"
        user.notify_email = False
        user.notify_whatsapp = False
        
        criteria = {"city": "5000", "rooms": "4"}
        
        notifier = create_notifier_for_user(user, criteria)
        
        assert notifier is None
    
    def test_create_notifier_for_alert_rule(self):
        """Test creating notifier for alert rule."""
        # Mock alert rule object
        alert_rule = MagicMock()
        alert_rule.channels = ["email", "whatsapp"]
        alert_rule.params = {"city": "5000", "rooms": "4"}
        
        user = MagicMock()
        user.email = "test@example.com"
        user.phone = "+972501234567"
        alert_rule.user = user
        
        with patch.dict(os.environ, {
            "SENDGRID_API_KEY": "test_key",
            "EMAIL_FROM": "test@example.com",
            "TWILIO_ACCOUNT_SID": "test_sid",
            "TWILIO_AUTH_TOKEN": "test_token",
            "TWILIO_WHATSAPP_FROM": "whatsapp:+14155238886"
        }):
            notifier = create_notifier_for_alert_rule(alert_rule)
            
            assert notifier is not None
            assert notifier.criteria == alert_rule.params
            assert len(notifier.alerts) == 2  # Email + WhatsApp


class TestAlertIntegration:
    """Test alert system integration."""
    
    def test_notifier_message_format(self):
        """Test notifier message formatting."""
        from orchestration.alerts import Notifier, EmailAlert
        
        # Mock listing object
        listing = MagicMock()
        listing.title = "דירה 4 חדרים בתל אביב"
        listing.price = "2,500,000 ₪"
        listing.url = "https://example.com/listing/123"
        
        # Create notifier with email alert
        alert = EmailAlert("test@example.com")
        notifier = Notifier({}, [alert])
        
        # Mock the alert.send method
        with patch.object(alert, 'send') as mock_send:
            notifier.notify(listing)
            
            # Check that send was called with properly formatted message
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            
            assert "🏠 נכס חדש נמצא!" in call_args
            assert "דירה 4 חדרים בתל אביב" in call_args
            assert "2,500,000 ₪" in call_args
            assert "https://example.com/listing/123" in call_args
            assert "נדלנר - מערכת התראות נדלן" in call_args
    
    def test_notifier_criteria_matching(self):
        """Test notifier criteria matching."""
        from orchestration.alerts import Notifier, EmailAlert
        
        # Mock listing object
        listing = MagicMock()
        listing.city = "5000"
        listing.rooms = "4"
        listing.title = "Test Property"
        
        # Create notifier with matching criteria
        alert = EmailAlert("test@example.com")
        notifier = Notifier({"city": "5000", "rooms": "4"}, [alert])
        
        with patch.object(alert, 'send') as mock_send:
            notifier.notify(listing)
            mock_send.assert_called_once()
        
        # Test with non-matching criteria
        notifier = Notifier({"city": "5000", "rooms": "3"}, [alert])
        
        with patch.object(alert, 'send') as mock_send:
            notifier.notify(listing)
            mock_send.assert_not_called()


def test_environment_configuration():
    """Test environment configuration validation."""
    required_vars = [
        "EMAIL_FROM",
        "SENDGRID_API_KEY",
        "TWILIO_ACCOUNT_SID", 
        "TWILIO_AUTH_TOKEN",
        "TWILIO_WHATSAPP_FROM"
    ]
    
    optional_vars = [
        "SMTP_HOST",
        "SMTP_USER", 
        "SMTP_PASSWORD",
        "ALERT_DEFAULT_EMAIL",
        "ALERT_DEFAULT_WHATSAPP_TO"
    ]
    
    # Test that we can check for environment variables
    for var in required_vars + optional_vars:
        value = os.getenv(var)
        # Just test that the function doesn't crash
        assert isinstance(value, (str, type(None)))


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
