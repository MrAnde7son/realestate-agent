"""
Analytics and event tracking tests for CRM functionality
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Asset
from crm.models import Contact, Lead, LeadStatus
from unittest.mock import patch, MagicMock

User = get_user_model()


class CrmAnalyticsTests(TestCase):
    """Analytics and event tracking tests for CRM functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='crm_analytics_test@example.com',
            username='crm_analytics_test',
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
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    @patch('crm.models.track_contact_created')
    def test_contact_created_event_tracking(self, mock_track_contact_created):
        """Test contact created event tracking"""
        data = {
            'name': 'רות כהן',
            'email': 'rut@example.com',
            'phone': '050-1234567',
            'tags': ['VIP', 'משקיע']
        }
        
        response = self.client.post('/api/crm/contacts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify event was tracked
        mock_track_contact_created.assert_called_once()
        call_args = mock_track_contact_created.call_args
        
        # Check the contact object and user_id were passed
        contact_obj = call_args[0][0]
        user_id = call_args[0][1]
        self.assertEqual(user_id, self.user.id)
        self.assertEqual(contact_obj.name, 'רות כהן')
    
    @patch('crm.models.track_contact_created')
    def test_contact_created_event_tracking_no_email_phone(self, mock_track_contact_created):
        """Test contact created event tracking without email and phone"""
        data = {
            'name': 'רות כהן',
            'tags': ['VIP']
        }
        
        response = self.client.post('/api/crm/contacts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify event was tracked
        mock_track_contact_created.assert_called_once()
        call_args = mock_track_contact_created.call_args
        
        contact_obj = call_args[0][0]
        user_id = call_args[0][1]
        self.assertEqual(user_id, self.user.id)
        self.assertIsNotNone(contact_obj)
    
    @patch('crm.models.track_lead_created')
    def test_lead_created_event_tracking(self, mock_track_lead_created):
        """Test lead created event tracking"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        data = {
            'contact_id_write': contact.id,
            'asset_id': self.asset.id,
            'status': 'new'
        }
        
        response = self.client.post('/api/crm/leads/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify event was tracked
        mock_track_lead_created.assert_called_once()
        call_args = mock_track_lead_created.call_args
        
        lead_obj = call_args[0][0]
        user_id = call_args[0][1]
        self.assertEqual(user_id, self.user.id)
        self.assertIsNotNone(lead_obj)
    
    @patch('crm.models.track_lead_status_changed')
    def test_lead_status_changed_event_tracking(self, mock_track_lead_status_changed):
        """Test lead status changed event tracking"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new'
        )
        
        # Change status
        data = {'status': 'contacted'}
        response = self.client.post(f'/api/crm/leads/{lead.id}/set_status/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify event was tracked
        mock_track_lead_status_changed.assert_called_once()
        call_args = mock_track_lead_status_changed.call_args
        
        lead_obj = call_args[0][0]
        user_id = call_args[0][1]
        from_status = call_args[0][2]
        to_status = call_args[0][3]
        self.assertEqual(user_id, self.user.id)
        self.assertEqual(from_status, 'new')
        self.assertEqual(to_status, 'contacted')
        self.assertIsNotNone(lead_obj)
    
    @patch('crm.analytics.track_lead_report_sent')
    def test_lead_report_sent_event_tracking(self, mock_track_lead_report_sent):
        """Test lead report sent event tracking"""
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
        
        # Send report
        response = self.client.post(f'/api/crm/leads/{lead.id}/send_report/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify event was tracked
        mock_track_lead_report_sent.assert_called_once()
        call_args = mock_track_lead_report_sent.call_args
        
        lead_obj = call_args[0][0]
        user_id = call_args[0][1]
        via = call_args[0][2]
        self.assertEqual(user_id, self.user.id)
        self.assertEqual(via, 'email')
        self.assertIsNotNone(lead_obj)
    
    @patch('crm.services.track_asset_change_notified')
    def test_asset_change_notified_event_tracking(self, mock_track_asset_change_notified):
        """Test asset change notified event tracking"""
        # Create multiple leads for the asset
        contacts = [
            {'name': 'רות כהן', 'email': 'rut@example.com'},
            {'name': 'דוד לוי', 'email': 'david@example.com'},
            {'name': 'שרה גולד', 'email': 'sara@example.com'}
        ]
        
        for contact_data in contacts:
            contact = Contact.objects.create(owner=self.user, **contact_data)
            Lead.objects.create(
                contact=contact,
                asset=self.asset,
                status='interested'
            )
        
        # Simulate asset change notification
        from crm.services import notify_asset_change
        change_summary = "המחיר עודכן ל-1,200,000 ש\"ח"
        
        notify_asset_change(self.asset.id, change_summary)
        
        # Verify event was tracked
        mock_track_asset_change_notified.assert_called_once()
        call_args = mock_track_asset_change_notified.call_args
        
        asset_obj = call_args[0][0]
        user_id = call_args[0][1]
        leads_count = call_args[0][2]
        change_summary = call_args[0][3]
        self.assertEqual(user_id, self.user.id)
        self.assertEqual(leads_count, 3)
        self.assertIsNotNone(asset_obj)
    
    @patch('crm.analytics.track_lead_note_added')
    def test_lead_note_added_event_tracking(self, mock_track_lead_note_added):
        """Test lead note added event tracking"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new'
        )
        
        # Add note
        data = {'text': 'נפגשנו, ביקשה דוח ממותג'}
        response = self.client.post(f'/api/crm/leads/{lead.id}/add_note/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify event was tracked
        mock_track_lead_note_added.assert_called_once()
        call_args = mock_track_lead_note_added.call_args
        
        lead_obj = call_args[0][0]
        user_id = call_args[0][1]
        note_text = call_args[0][2]
        self.assertEqual(user_id, self.user.id)
        self.assertEqual(note_text, 'נפגשנו, ביקשה דוח ממותג')
        self.assertIsNotNone(lead_obj)
    
    @patch('crm.models.track_contact_updated')
    def test_contact_updated_event_tracking(self, mock_track_contact_updated):
        """Test contact updated event tracking"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Update contact
        data = {
            'name': 'רות כהן-לוי',
            'email': 'rut@example.com',
            'phone': '050-1234567',
            'tags': ['VIP', 'משקיע']
        }
        
        response = self.client.put(f'/api/crm/contacts/{contact.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify event was tracked
        mock_track_contact_updated.assert_called_once()
        call_args = mock_track_contact_updated.call_args
        
        contact_obj = call_args[0][0]
        user_id = call_args[0][1]
        changed_fields = call_args[0][2]
        self.assertEqual(user_id, self.user.id)
        self.assertIn('name', changed_fields)
        self.assertIsNotNone(contact_obj)
    
    @patch('crm.models.track_lead_deleted')
    def test_lead_deleted_event_tracking(self, mock_track_lead_deleted):
        """Test lead deleted event tracking"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new'
        )
        
        # Delete lead
        response = self.client.delete(f'/api/crm/leads/{lead.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify event was tracked
        mock_track_lead_deleted.assert_called_once()
        call_args = mock_track_lead_deleted.call_args
        
        lead_obj = call_args[0][0]
        user_id = call_args[0][1]
        self.assertEqual(user_id, self.user.id)
        self.assertIsNotNone(lead_obj)
    
    @patch('crm.models.track_contact_deleted')
    def test_contact_deleted_event_tracking(self, mock_track_contact_deleted):
        """Test contact deleted event tracking"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Create lead for contact
        Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new'
        )
        
        # Delete contact
        response = self.client.delete(f'/api/crm/contacts/{contact.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify event was tracked
        mock_track_contact_deleted.assert_called_once()
        call_args = mock_track_contact_deleted.call_args
        
        contact_obj = call_args[0][0]
        user_id = call_args[0][1]
        leads_count = call_args[0][2]
        self.assertEqual(user_id, self.user.id)
        self.assertEqual(leads_count, 1)
        self.assertIsNotNone(contact_obj)
    
    @patch('crm.views.track_crm_search')
    def test_crm_search_event_tracking(self, mock_track_crm_search):
        """Test CRM search event tracking"""
        # Create test contacts
        Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        Contact.objects.create(
            owner=self.user,
            name='דוד לוי',
            email='david@example.com'
        )
        
        # Search contacts
        response = self.client.get('/api/crm/contacts/search/?q=רות')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify event was tracked
        mock_track_crm_search.assert_called_once()
        call_args = mock_track_crm_search.call_args
        
        user_id = call_args[0][0]
        search_type = call_args[0][1]
        query = call_args[0][2]
        results_count = call_args[0][3]
        self.assertEqual(user_id, self.user.id)
        self.assertEqual(search_type, 'contacts')
        self.assertEqual(query, 'רות')
        self.assertEqual(results_count, 1)
    
    @patch('crm.views.track_crm_export')
    def test_crm_export_event_tracking(self, mock_track_crm_export):
        """Test CRM export event tracking"""
        # Create test data
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new'
        )
        
        # Export contacts
        response = self.client.get('/api/crm/contacts/export/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify event was tracked
        mock_track_crm_export.assert_called_once()
        call_args = mock_track_crm_export.call_args
        
        user_id = call_args[0][0]
        export_type = call_args[0][1]
        count = call_args[0][2]
        self.assertEqual(user_id, self.user.id)
        self.assertEqual(export_type, 'contacts')
        self.assertEqual(count, 1)
    
    def test_analytics_event_structure(self):
        """Test that analytics events have correct structure"""
        # This test verifies that the track_contact_created function is called with correct parameters
        # without actually calling the real function
    
        with patch('crm.models.track_contact_created') as mock_track_contact_created:
            # Create contact
            data = {
                'name': 'רות כהן',
                'email': 'rut@example.com',
                'tags': ['VIP']
            }
            
            response = self.client.post('/api/crm/contacts/', data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Verify event structure
            mock_track_contact_created.assert_called_once()
            call_args = mock_track_contact_created.call_args
            
            contact_obj = call_args[0][0]
            user_id = call_args[0][1]
            
            # Verify function was called with correct parameters
            self.assertIsNotNone(contact_obj)
            self.assertEqual(user_id, self.user.id)
    
    def test_analytics_error_handling(self):
        """Test analytics error handling"""
        # Test that analytics errors don't break the main functionality
        with patch('crm.models.track_contact_created', side_effect=Exception("Analytics error")):
            # Create contact - should still work despite analytics error
            data = {
                'name': 'רות כהן',
                'email': 'rut@example.com'
            }
            
            response = self.client.post('/api/crm/contacts/', data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Verify contact was created
            contact = Contact.objects.get(email='rut@example.com')
            self.assertEqual(contact.name, 'רות כהן')
    
    def test_analytics_batch_events(self):
        """Test analytics batch events"""
        with patch('crm.models.track_contact_created') as mock_track_contact_created:
            # Create multiple contacts quickly
            contacts_data = [
                {'name': 'רות כהן', 'email': 'rut@example.com'},
                {'name': 'דוד לוי', 'email': 'david@example.com'},
                {'name': 'שרה גולד', 'email': 'sara@example.com'}
            ]
            
            for data in contacts_data:
                response = self.client.post('/api/crm/contacts/', data)
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Verify all events were tracked
            self.assertEqual(mock_track_contact_created.call_count, 3)
            
            # Verify all events have correct structure
            for call in mock_track_contact_created.call_args_list:
                contact_obj = call[0][0]
                user_id = call[0][1]
                
                self.assertIsNotNone(contact_obj)
                self.assertEqual(user_id, self.user.id)
