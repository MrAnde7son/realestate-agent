"""
Tests for CRM services
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import Asset
from crm.models import Contact, Lead, LeadStatus
from crm.services import notify_asset_change, send_report_to_contact
from unittest.mock import patch, MagicMock

User = get_user_model()


class CrmServicesTests(TestCase):
    """Tests for CRM services"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='crm_services_test@example.com',
            username='testuser',
            password='testpass123',
            role='broker'
        )
        
        self.asset = Asset.objects.create(
            street='רחוב הרצל',
            number=1,
            city='תל אביב',
            price=1000000,
            area=100,
            rooms=3,
            created_by=self.user
        )
    
    @patch('crm.services.send_email')
    def test_notify_asset_change_with_leads(self, mock_send_email):
        """Test asset change notification with leads"""
        # Create contacts and leads
        contact1 = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        contact2 = Contact.objects.create(
            owner=self.user,
            name='דוד לוי',
            email='david@example.com'
        )
        
        contact3 = Contact.objects.create(
            owner=self.user,
            name='שרה גולד',
            phone='050-1234567'
            # No email
        )
        
        # Create leads
        Lead.objects.create(
            contact=contact1,
            asset=self.asset,
            status='interested'
        )
        
        Lead.objects.create(
            contact=contact2,
            asset=self.asset,
            status='negotiating'
        )
        
        Lead.objects.create(
            contact=contact3,
            asset=self.asset,
            status='new'
        )
        
        # Test notification
        change_summary = "המחיר עודכן ל-1,200,000 ש\"ח"
        
        notify_asset_change(self.asset.id, change_summary)
        
        # Verify emails were sent only to contacts with email
        self.assertEqual(mock_send_email.call_count, 2)
        
        # Check first email
        first_call = mock_send_email.call_args_list[0]
        self.assertEqual(first_call[1]['to'], 'rut@example.com')
        self.assertEqual(first_call[1]['subject'], 'עדכון בנכס במעקב')
        self.assertIn('רות כהן', first_call[1]['body'])
        self.assertIn(change_summary, first_call[1]['body'])
        
        # Check second email
        second_call = mock_send_email.call_args_list[1]
        self.assertEqual(second_call[1]['to'], 'david@example.com')
        self.assertEqual(second_call[1]['subject'], 'עדכון בנכס במעקב')
        self.assertIn('דוד לוי', second_call[1]['body'])
        self.assertIn(change_summary, second_call[1]['body'])
    
    @patch('crm.services.send_email')
    def test_notify_asset_change_no_leads(self, mock_send_email):
        """Test asset change notification with no leads"""
        # Test notification with no leads
        change_summary = "המחיר עודכן ל-1,200,000 ש\"ח"
        
        notify_asset_change(self.asset.id, change_summary)
        
        # Verify no emails were sent
        mock_send_email.assert_not_called()
    
    @patch('crm.services.send_email')
    def test_notify_asset_change_no_email_contacts(self, mock_send_email):
        """Test asset change notification with contacts that have no email"""
        # Create contact without email
        contact = Contact.objects.create(
            owner=self.user,
            name='שרה גולד',
            phone='050-1234567'
            # No email
        )
        
        # Create lead
        Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='interested'
        )
        
        # Test notification
        change_summary = "המחיר עודכן ל-1,200,000 ש\"ח"
        
        notify_asset_change(self.asset.id, change_summary)
        
        # Verify no emails were sent
        mock_send_email.assert_not_called()
    
    @patch('crm.services.send_email')
    def test_notify_asset_change_different_assets(self, mock_send_email):
        """Test asset change notification for different assets"""
        # Create another asset
        other_asset = Asset.objects.create(
            street='רחוב דיזנגוף',
            number=10,
            city='תל אביב',
            price=1500000,
            area=120,
            rooms=4,
            created_by=self.user
        )
        
        # Create contact and lead for first asset
        contact1 = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        Lead.objects.create(
            contact=contact1,
            asset=self.asset,
            status='interested'
        )
        
        # Create contact and lead for second asset
        contact2 = Contact.objects.create(
            owner=self.user,
            name='דוד לוי',
            email='david@example.com'
        )
        
        Lead.objects.create(
            contact=contact2,
            asset=other_asset,
            status='interested'
        )
        
        # Test notification for first asset only
        change_summary = "המחיר עודכן ל-1,200,000 ש\"ח"
        
        notify_asset_change(self.asset.id, change_summary)
        
        # Verify only one email was sent (for first asset)
        self.assertEqual(mock_send_email.call_count, 1)
        
        # Check email content
        call = mock_send_email.call_args
        self.assertEqual(call[1]['to'], 'rut@example.com')
        self.assertIn('רות כהן', call[1]['body'])
    
    @patch('crm.services.build_branded_pdf')
    @patch('crm.services.send_email')
    def test_send_report_to_contact_success(self, mock_send_email, mock_build_pdf):
        """Test successful report sending to contact"""
        # Mock PDF generation
        mock_pdf_content = b"PDF_CONTENT_BYTES"
        mock_build_pdf.return_value = mock_pdf_content
        
        # Create contact and lead
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='interested'
        )
        
        # Test report sending
        report_payload = {
            'asset_id': self.asset.id,
            'contact_name': contact.name,
            'report_type': 'property_analysis'
        }
        
        send_report_to_contact(lead.id, report_payload)
        
        # Verify PDF was generated
        mock_build_pdf.assert_called_once_with(
            payload=report_payload,
            owner_id=self.user.id
        )
        
        # Verify email was sent
        mock_send_email.assert_called_once()
        call = mock_send_email.call_args
        
        self.assertEqual(call[1]['to'], 'rut@example.com')
        self.assertEqual(call[1]['subject'], 'דוח נדל"נר')
        self.assertEqual(call[1]['body'], 'מצורף דוח ממותג.')
        self.assertEqual(call[1]['attachments'], [('nadlaner-report.pdf', mock_pdf_content)])
    
    @patch('crm.services.build_branded_pdf')
    @patch('crm.services.send_email')
    def test_send_report_to_contact_no_email(self, mock_send_email, mock_build_pdf):
        """Test report sending to contact without email"""
        # Mock PDF generation
        mock_pdf_content = b"PDF_CONTENT_BYTES"
        mock_build_pdf.return_value = mock_pdf_content
        
        # Create contact without email
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            phone='050-1234567'
            # No email
        )
        
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='interested'
        )
        
        # Test report sending
        report_payload = {
            'asset_id': self.asset.id,
            'contact_name': contact.name,
            'report_type': 'property_analysis'
        }
        
        send_report_to_contact(lead.id, report_payload)
        
        # Verify PDF was generated
        mock_build_pdf.assert_called_once_with(
            payload=report_payload,
            owner_id=self.user.id
        )
        
        # Verify no email was sent
        mock_send_email.assert_not_called()
    
    @patch('crm.services.build_branded_pdf')
    @patch('crm.services.send_email')
    def test_send_report_to_contact_pdf_generation_error(self, mock_send_email, mock_build_pdf):
        """Test report sending when PDF generation fails"""
        # Mock PDF generation error
        mock_build_pdf.side_effect = Exception("PDF generation failed")
        
        # Create contact and lead
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='interested'
        )
        
        # Test report sending
        report_payload = {
            'asset_id': self.asset.id,
            'contact_name': contact.name,
            'report_type': 'property_analysis'
        }
        
        # Should not raise exception
        try:
            send_report_to_contact(lead.id, report_payload)
        except Exception as e:
            self.fail(f"send_report_to_contact raised an exception: {e}")
        
        # Verify PDF generation was attempted
        mock_build_pdf.assert_called_once()
        
        # Verify no email was sent
        mock_send_email.assert_not_called()
    
    @patch('crm.services.build_branded_pdf')
    @patch('crm.services.send_email')
    def test_send_report_to_contact_email_sending_error(self, mock_send_email, mock_build_pdf):
        """Test report sending when email sending fails"""
        # Mock PDF generation
        mock_pdf_content = b"PDF_CONTENT_BYTES"
        mock_build_pdf.return_value = mock_pdf_content
        
        # Mock email sending error
        mock_send_email.side_effect = Exception("Email sending failed")
        
        # Create contact and lead
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='interested'
        )
        
        # Test report sending
        report_payload = {
            'asset_id': self.asset.id,
            'contact_name': contact.name,
            'report_type': 'property_analysis'
        }
        
        # Should not raise exception
        try:
            send_report_to_contact(lead.id, report_payload)
        except Exception as e:
            self.fail(f"send_report_to_contact raised an exception: {e}")
        
        # Verify PDF was generated
        mock_build_pdf.assert_called_once()
        
        # Verify email sending was attempted
        mock_send_email.assert_called_once()
    
    def test_send_report_to_contact_invalid_lead_id(self):
        """Test report sending with invalid lead ID"""
        # Test with non-existent lead ID
        report_payload = {
            'asset_id': self.asset.id,
            'contact_name': 'Test Contact',
            'report_type': 'property_analysis'
        }
        
        # Should return False for non-existent lead
        result = send_report_to_contact(99999, report_payload)
        self.assertFalse(result)
    
    @patch('crm.services.send_email')
    def test_notify_asset_change_email_content(self, mock_send_email):
        """Test asset change notification email content"""
        # Create contact and lead
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='interested'
        )
        
        # Test notification with specific content
        change_summary = "המחיר עודכן ל-1,200,000 ש\"ח"
        
        notify_asset_change(self.asset.id, change_summary)
        
        # Verify email content
        mock_send_email.assert_called_once()
        call = mock_send_email.call_args
        
        self.assertEqual(call[1]['to'], 'rut@example.com')
        self.assertEqual(call[1]['subject'], 'עדכון בנכס במעקב')
        
        body = call[1]['body']
        self.assertIn('רות כהן', body)
        self.assertIn(change_summary, body)
        self.assertIn('נדל"נר', body)
        self.assertIn('היי', body)
    
    @patch('crm.services.build_branded_pdf')
    @patch('crm.services.send_email')
    def test_send_report_to_contact_payload_handling(self, mock_send_email, mock_build_pdf):
        """Test report sending payload handling"""
        # Mock PDF generation
        mock_pdf_content = b"PDF_CONTENT_BYTES"
        mock_build_pdf.return_value = mock_pdf_content
        
        # Create contact and lead
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='interested'
        )
        
        # Test with complex payload
        report_payload = {
            'asset_id': self.asset.id,
            'contact_name': contact.name,
            'report_type': 'property_analysis',
            'sections': ['overview', 'pricing', 'location'],
            'filters': {'price_range': [1000000, 2000000]},
            'metadata': {'generated_at': '2024-01-01T12:00:00Z'}
        }
        
        send_report_to_contact(lead.id, report_payload)
        
        # Verify PDF was generated with correct payload
        mock_build_pdf.assert_called_once_with(
            payload=report_payload,
            owner_id=self.user.id
        )
        
        # Verify email was sent
        mock_send_email.assert_called_once()
        call = mock_send_email.call_args
        
        self.assertEqual(call[1]['to'], 'rut@example.com')
        self.assertEqual(call[1]['subject'], 'דוח נדל"נר')
        self.assertEqual(call[1]['body'], 'מצורף דוח ממותג.')
        self.assertEqual(call[1]['attachments'], [('nadlaner-report.pdf', mock_pdf_content)])
    
    def test_notify_asset_change_performance(self):
        """Test asset change notification performance with many leads"""
        # Create many contacts and leads
        contacts = []
        leads = []
        
        for i in range(100):
            contact = Contact.objects.create(
                owner=self.user,
                name=f'Contact {i}',
                email=f'contact{i}@example.com'
            )
            contacts.append(contact)
            
            lead = Lead.objects.create(
                contact=contact,
                asset=self.asset,
                status='interested'
            )
            leads.append(lead)
        
        # Test notification performance
        with patch('crm.services.send_email') as mock_send_email:
            change_summary = "המחיר עודכן ל-1,200,000 ש\"ח"
            
            # This should not take too long
            import time
            start_time = time.time()
            notify_asset_change(self.asset.id, change_summary)
            end_time = time.time()
            
            # Should complete within reasonable time (less than 1 second)
            self.assertLess(end_time - start_time, 1.0)
            
            # Verify all emails were sent
            self.assertEqual(mock_send_email.call_count, 100)
    
    def test_send_report_to_contact_performance(self):
        """Test report sending performance"""
        # Create contact and lead
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='interested'
        )
        
        # Test report sending performance
        with patch('crm.services.build_branded_pdf') as mock_build_pdf, \
             patch('crm.services.send_email') as mock_send_email:
            
            mock_pdf_content = b"PDF_CONTENT_BYTES"
            mock_build_pdf.return_value = mock_pdf_content
            
            report_payload = {
                'asset_id': self.asset.id,
                'contact_name': contact.name,
                'report_type': 'property_analysis'
            }
            
            # This should not take too long
            import time
            start_time = time.time()
            send_report_to_contact(lead.id, report_payload)
            end_time = time.time()
            
            # Should complete within reasonable time (less than 1 second)
            self.assertLess(end_time - start_time, 1.0)
            
            # Verify PDF generation and email sending were called
            mock_build_pdf.assert_called_once()
            mock_send_email.assert_called_once()
