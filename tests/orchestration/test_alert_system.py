"""Tests for the orchestration alert utilities."""

import os
from unittest.mock import MagicMock, patch

import pytest

from orchestration.alerts import EmailAlert, WhatsAppAlert, create_notifier_for_alert_rule, create_notifier_for_user


class TestEmailAlert:
    """Test email alert functionality."""
    
    def test_email_alert_initialization(self):
        """Test EmailAlert initialization."""
        with patch.dict(os.environ, {"RESEND_FROM": "alerts@example.com"}):
            alert = EmailAlert("test@example.com")
        assert alert.to_email == "test@example.com"
        assert alert.from_email == "alerts@example.com"

    def test_email_alert_resend_sdk_success(self):
        """The alert sends mail via the Resend SDK when available."""

        with patch.dict(os.environ, {"RESEND_API_KEY": "test_key", "RESEND_FROM": "alerts@example.com"}):
            with patch("orchestration.alerts.resend") as mock_resend:
                mock_resend.Emails.send.return_value = {"id": "email_123"}
                alert = EmailAlert("test@example.com")
                alert.send("Test message")
                mock_resend.Emails.send.assert_called_once()

    def test_email_alert_resend_rest_fallback(self):
        """When the SDK is not available the REST client is used."""

        with patch.dict(os.environ, {"RESEND_API_KEY": "test_key", "RESEND_FROM": "alerts@example.com"}):
            with patch("orchestration.alerts.resend", None):
                with patch("orchestration.alerts.requests.post") as mock_post:
                    mock_response = MagicMock()
                    mock_response.ok = True
                    mock_response.json.return_value = {"id": "email_456"}
                    mock_post.return_value = mock_response

                    alert = EmailAlert("test@example.com")
                    alert.send("Test message")

                    mock_post.assert_called_once()

    def test_email_alert_console_fallback(self, capsys):
        """Console fallback is used when the API key is missing."""

        with patch.dict(os.environ, {"EMAIL_FALLBACK_TO_CONSOLE": "true", "RESEND_API_KEY": "", "RESEND_FROM": "alerts@example.com"}):
            alert = EmailAlert("test@example.com")
            alert.send("Test message")

        captured = capsys.readouterr()
        assert "[EMAIL:CONSOLE]" in captured.out


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
            "RESEND_API_KEY": "test_key",
            "RESEND_FROM": "test@example.com",
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
            "RESEND_API_KEY": "test_key",
            "RESEND_FROM": "test@example.com"
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
            "RESEND_API_KEY": "test_key",
            "RESEND_FROM": "test@example.com",
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
        "RESEND_FROM",
        "RESEND_API_KEY",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_WHATSAPP_FROM"
    ]

    optional_vars = [
        "RESEND_REPLY_TO",
        "RESEND_SANDBOX",
        "EMAIL_FALLBACK_TO_CONSOLE",
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
