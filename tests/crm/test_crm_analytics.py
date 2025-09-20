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
            password='testpass123'
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
    
    @patch('crm.analytics.track_contact_created')
    def test_contact_created_event_tracking_no_email_phone(self, mock_track_contact_created):
        """Test contact created event tracking without email and phone"""
        data = {
            'name': 'רות כהן',
            'tags': ['VIP']
        }
        
        response = self.client.post('/api/crm/contacts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify event was tracked
        mock_track_event.assert_called_once()
        call_args = mock_track_event.call_args
        
        self.assertEqual(call_args[0][0], 'contact_created')
        self.assertEqual(call_args[0][1]['has_email'], False)
        self.assertEqual(call_args[0][1]['has_phone'], False)
        self.assertEqual(call_args[0][1]['tags_count'], 1)
    
    @patch('crm.models.track_event')
    def test_lead_created_event_tracking(self, mock_track_event):
        """Test lead created event tracking"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        data = {
            'contact_id': contact.id,
            'asset_id': self.asset.id,
            'status': 'new'
        }
        
        response = self.client.post('/api/crm/leads/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify event was tracked
        mock_track_event.assert_called_once()
        call_args = mock_track_event.call_args
        
        self.assertEqual(call_args[0][0], 'lead_created')
        self.assertEqual(call_args[0][1]['user_id'], self.user.id)
        self.assertEqual(call_args[0][1]['lead_id'], response.data['id'])
        self.assertEqual(call_args[0][1]['status'], 'new')
        self.assertEqual(call_args[0][1]['asset_id'], self.asset.id)
    
    @patch('crm.models.track_event')
    def test_lead_status_changed_event_tracking(self, mock_track_event):
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
        mock_track_event.assert_called_once()
        call_args = mock_track_event.call_args
        
        self.assertEqual(call_args[0][0], 'lead_status_changed')
        self.assertEqual(call_args[0][1]['user_id'], self.user.id)
        self.assertEqual(call_args[0][1]['lead_id'], lead.id)
        self.assertEqual(call_args[0][1]['from_status'], 'new')
        self.assertEqual(call_args[0][1]['to_status'], 'contacted')
    
    @patch('crm.models.track_event')
    def test_lead_report_sent_event_tracking(self, mock_track_event):
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
        mock_track_event.assert_called_once()
        call_args = mock_track_event.call_args
        
        self.assertEqual(call_args[0][0], 'lead_report_sent')
        self.assertEqual(call_args[0][1]['user_id'], self.user.id)
        self.assertEqual(call_args[0][1]['lead_id'], lead.id)
        self.assertEqual(call_args[0][1]['via'], 'email')
        self.assertEqual(call_args[0][1]['asset_id'], self.asset.id)
    
    @patch('crm.models.track_event')
    def test_asset_change_notified_event_tracking(self, mock_track_event):
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
        mock_track_event.assert_called_once()
        call_args = mock_track_event.call_args
        
        self.assertEqual(call_args[0][0], 'asset_change_notified')
        self.assertEqual(call_args[0][1]['user_id'], self.user.id)
        self.assertEqual(call_args[0][1]['asset_id'], self.asset.id)
        self.assertEqual(call_args[0][1]['leads_count'], 3)
        self.assertEqual(call_args[0][1]['change_summary'], change_summary)
    
    @patch('crm.models.track_event')
    def test_lead_note_added_event_tracking(self, mock_track_event):
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
        mock_track_event.assert_called_once()
        call_args = mock_track_event.call_args
        
        self.assertEqual(call_args[0][0], 'lead_note_added')
        self.assertEqual(call_args[0][1]['user_id'], self.user.id)
        self.assertEqual(call_args[0][1]['lead_id'], lead.id)
        self.assertEqual(call_args[0][1]['note_length'], len('נפגשנו, ביקשה דוח ממותג'))
    
    @patch('crm.models.track_event')
    def test_contact_updated_event_tracking(self, mock_track_event):
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
        mock_track_event.assert_called_once()
        call_args = mock_track_event.call_args
        
        self.assertEqual(call_args[0][0], 'contact_updated')
        self.assertEqual(call_args[0][1]['user_id'], self.user.id)
        self.assertEqual(call_args[0][1]['contact_id'], contact.id)
        self.assertEqual(call_args[0][1]['fields_changed'], ['name', 'phone', 'tags'])
    
    @patch('crm.models.track_event')
    def test_lead_deleted_event_tracking(self, mock_track_event):
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
        mock_track_event.assert_called_once()
        call_args = mock_track_event.call_args
        
        self.assertEqual(call_args[0][0], 'lead_deleted')
        self.assertEqual(call_args[0][1]['user_id'], self.user.id)
        self.assertEqual(call_args[0][1]['lead_id'], lead.id)
        self.assertEqual(call_args[0][1]['status'], 'new')
        self.assertEqual(call_args[0][1]['asset_id'], self.asset.id)
    
    @patch('crm.models.track_event')
    def test_contact_deleted_event_tracking(self, mock_track_event):
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
        mock_track_event.assert_called_once()
        call_args = mock_track_event.call_args
        
        self.assertEqual(call_args[0][0], 'contact_deleted')
        self.assertEqual(call_args[0][1]['user_id'], self.user.id)
        self.assertEqual(call_args[0][1]['contact_id'], contact.id)
        self.assertEqual(call_args[0][1]['leads_count'], 1)
    
    @patch('crm.models.track_event')
    def test_crm_search_event_tracking(self, mock_track_event):
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
        mock_track_event.assert_called_once()
        call_args = mock_track_event.call_args
        
        self.assertEqual(call_args[0][0], 'crm_search')
        self.assertEqual(call_args[0][1]['user_id'], self.user.id)
        self.assertEqual(call_args[0][1]['search_type'], 'contacts')
        self.assertEqual(call_args[0][1]['search_query'], 'רות')
        self.assertEqual(call_args[0][1]['results_count'], 1)
    
    @patch('crm.models.track_event')
    def test_crm_export_event_tracking(self, mock_track_event):
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
        mock_track_event.assert_called_once()
        call_args = mock_track_event.call_args
        
        self.assertEqual(call_args[0][0], 'crm_export')
        self.assertEqual(call_args[0][1]['user_id'], self.user.id)
        self.assertEqual(call_args[0][1]['export_type'], 'contacts')
        self.assertEqual(call_args[0][1]['records_count'], 1)
    
    def test_analytics_event_structure(self):
        """Test that analytics events have correct structure"""
        # This test verifies that the track_event function is called with correct parameters
        # without actually calling the real function
        
        with patch('crm.models.track_event') as mock_track_event:
            # Create contact
            data = {
                'name': 'רות כהן',
                'email': 'rut@example.com',
                'tags': ['VIP']
            }
            
            response = self.client.post('/api/crm/contacts/', data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Verify event structure
            mock_track_event.assert_called_once()
            call_args = mock_track_event.call_args
            
            event_name = call_args[0][0]
            event_props = call_args[0][1]
            
            # Verify event name
            self.assertIn(event_name, [
                'contact_created', 'contact_updated', 'contact_deleted',
                'lead_created', 'lead_status_changed', 'lead_note_added', 
                'lead_report_sent', 'lead_deleted',
                'asset_change_notified', 'crm_search', 'crm_export'
            ])
            
            # Verify required properties
            self.assertIn('user_id', event_props)
            self.assertEqual(event_props['user_id'], self.user.id)
            
            # Verify timestamp
            self.assertIn('timestamp', event_props)
            
            # Verify event-specific properties
            if event_name == 'contact_created':
                self.assertIn('contact_id', event_props)
                self.assertIn('has_email', event_props)
                self.assertIn('has_phone', event_props)
                self.assertIn('tags_count', event_props)
            elif event_name == 'lead_created':
                self.assertIn('lead_id', event_props)
                self.assertIn('status', event_props)
                self.assertIn('asset_id', event_props)
            elif event_name == 'lead_status_changed':
                self.assertIn('lead_id', event_props)
                self.assertIn('from_status', event_props)
                self.assertIn('to_status', event_props)
    
    def test_analytics_error_handling(self):
        """Test analytics error handling"""
        # Test that analytics errors don't break the main functionality
        with patch('crm.models.track_event', side_effect=Exception("Analytics error")):
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
        with patch('crm.models.track_event') as mock_track_event:
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
            self.assertEqual(mock_track_event.call_count, 3)
            
            # Verify all events have correct structure
            for call in mock_track_event.call_args_list:
                event_name = call[0][0]
                event_props = call[0][1]
                
                self.assertEqual(event_name, 'contact_created')
                self.assertIn('user_id', event_props)
                self.assertIn('contact_id', event_props)
                self.assertIn('timestamp', event_props)
