"""
Integration tests for CRM functionality
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Asset
from crm.models import Contact, Lead, LeadStatus
from crm.services import notify_asset_change, send_report_to_contact

User = get_user_model()


class CrmIntegrationTests(TestCase):
    """Integration tests for CRM functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='crm_integration_test@example.com',
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
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_full_contact_lead_workflow(self):
        """Test complete contact to lead workflow"""
        # 1. Create contact
        contact_data = {
            'name': 'רות כהן',
            'email': 'rut@example.com',
            'phone': '050-1234567',
            'tags': ['VIP', 'משקיע']
        }
        
        response = self.client.post('/api/crm/contacts/', contact_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        contact_id = response.data['id']
        
        # 2. Create lead
        lead_data = {
            'contact_id_write': contact_id,
            'asset_id': self.asset.id,
            'status': 'new'
        }
        
        response = self.client.post('/api/crm/leads/', lead_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        lead_id = response.data['id']
        
        # 3. Update lead status
        response = self.client.post(f'/api/crm/leads/{lead_id}/set_status/', {'status': 'contacted'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 4. Add notes
        response = self.client.post(f'/api/crm/leads/{lead_id}/add_note/', {'text': 'נפגשנו, ביקשה דוח ממותג'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 5. Send report
        response = self.client.post(f'/api/crm/leads/{lead_id}/send_report/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 6. Verify final state
        lead = Lead.objects.get(id=lead_id)
        self.assertEqual(lead.status, 'contacted')
        self.assertEqual(len(lead.notes), 1)
        self.assertEqual(lead.notes[0]['text'], 'נפגשנו, ביקשה דוח ממותג')
    
    def test_asset_change_notification(self):
        """Test asset change notification to leads"""
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
        
        # Simulate asset change notification
        change_summary = "המחיר עודכן ל-1,200,000 ש\"ח"
        
        # This should not raise an exception
        try:
            notify_asset_change(self.asset.id, change_summary)
        except Exception as e:
            self.fail(f"notify_asset_change raised an exception: {e}")
    
    def test_report_sending_integration(self):
        """Test report sending integration"""
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
        
        # This should not raise an exception
        try:
            send_report_to_contact(lead.id, report_payload)
        except Exception as e:
            self.fail(f"send_report_to_contact raised an exception: {e}")
    
    def test_contact_search_and_filtering(self):
        """Test contact search and filtering integration"""
        # Create multiple contacts
        contacts_data = [
            {'name': 'רות כהן', 'email': 'rut@example.com', 'tags': ['VIP']},
            {'name': 'דוד לוי', 'email': 'david@example.com', 'tags': ['משקיע']},
            {'name': 'שרה גולד', 'email': 'sara@example.com', 'tags': ['VIP', 'חוזר']},
            {'name': 'יוסי כהן', 'email': 'yossi@example.com', 'tags': ['חדש']}
        ]
        
        for data in contacts_data:
            response = self.client.post('/api/crm/contacts/', data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test search by name
        response = self.client.get('/api/crm/contacts/search/?q=כהן')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # רות כהן and יוסי כהן
        
        # Test search by email
        response = self.client.get('/api/crm/contacts/search/?q=david@example.com')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test search by tag
        response = self.client.get('/api/crm/contacts/search/?q=VIP')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # רות כהן and שרה גולד
    
    def test_lead_status_workflow_integration(self):
        """Test complete lead status workflow integration"""
        # Create contact and lead
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
        
        # Test complete status workflow
        statuses = [
            ('new', 'contacted'),
            ('contacted', 'interested'),
            ('interested', 'negotiating'),
            ('negotiating', 'closed-won')
        ]
        
        for from_status, to_status in statuses:
            # Verify current status
            lead.refresh_from_db()
            self.assertEqual(lead.status, from_status)
            
            # Update to next status
            response = self.client.post(f'/api/crm/leads/{lead.id}/set_status/', {'status': to_status})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Verify status was updated
            lead.refresh_from_db()
            self.assertEqual(lead.status, to_status)
    
    def test_lead_notes_timeline_integration(self):
        """Test lead notes timeline integration"""
        # Create contact and lead
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
        
        # Add multiple notes over time
        notes = [
            'יצרתי קשר ראשוני',
            'שלחתי דוח ממותג',
            'נפגשנו פנים אל פנים',
            'התחלנו במשא ומתן',
            'הגענו להסכמה'
        ]
        
        for note_text in notes:
            response = self.client.post(f'/api/crm/leads/{lead.id}/add_note/', {'text': note_text})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify all notes were added in correct order
        lead.refresh_from_db()
        self.assertEqual(len(lead.notes), 5)
        
        for i, note in enumerate(lead.notes):
            self.assertEqual(note['text'], notes[i])
    
    def test_asset_leads_panel_integration(self):
        """Test asset leads panel integration"""
        # Create multiple contacts and leads for the same asset
        contacts = [
            {'name': 'רות כהן', 'email': 'rut@example.com'},
            {'name': 'דוד לוי', 'email': 'david@example.com'},
            {'name': 'שרה גולד', 'email': 'sara@example.com'}
        ]
        
        lead_ids = []
        for contact_data in contacts:
            # Create contact
            response = self.client.post('/api/crm/contacts/', contact_data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            contact_id = response.data['id']
            
            # Create lead
            lead_data = {
                'contact_id_write': contact_id,
                'asset_id': self.asset.id,
                'status': 'new'
            }
            
            response = self.client.post('/api/crm/leads/', lead_data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            lead_ids.append(response.data['id'])
        
        # Test getting all leads for asset
        response = self.client.get(f'/api/crm/leads/by_asset/?asset_id={self.asset.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        # Verify all contacts are included
        contact_names = [lead['contact']['name'] for lead in response.data]
        expected_names = ['רות כהן', 'דוד לוי', 'שרה גולד']
        self.assertEqual(set(contact_names), set(expected_names))
    
    def test_contact_lead_association_integration(self):
        """Test contact-lead association integration"""
        # Create contact
        contact_data = {
            'name': 'רות כהן',
            'email': 'rut@example.com',
            'phone': '050-1234567',
            'tags': ['VIP', 'משקיע']
        }
        
        response = self.client.post('/api/crm/contacts/', contact_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        contact_id = response.data['id']
        
        # Create multiple leads for the same contact
        assets = [
            {'street': 'רחוב הרצל', 'number': 1, 'city': 'תל אביב', 'price': 1000000, 'area': 100, 'rooms': 3},
            {'street': 'רחוב דיזנגוף', 'number': 10, 'city': 'תל אביב', 'price': 1500000, 'area': 120, 'rooms': 4},
            {'street': 'רחוב אלנבי', 'number': 20, 'city': 'תל אביב', 'price': 2000000, 'area': 150, 'rooms': 5}
        ]
        
        asset_ids = []
        for asset_data in assets:
            asset = Asset.objects.create(created_by=self.user, **asset_data)
            asset_ids.append(asset.id)
            
            # Create lead
            lead_data = {
                'contact_id_write': contact_id,
                'asset_id': asset.id,
                'status': 'new'
            }
            
            response = self.client.post('/api/crm/leads/', lead_data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test getting all leads for contact
        response = self.client.get(f'/api/crm/contacts/{contact_id}/leads/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        # Verify all assets are included
        asset_ids_in_response = [lead['asset']['id'] for lead in response.data]
        self.assertEqual(set(asset_ids_in_response), set(asset_ids))
    
    def test_crm_permissions_integration(self):
        """Test CRM permissions integration"""
        # Create another user
        other_user = User.objects.create_user(
            email='crm_integration_other@example.com',
            username='otheruser',
            password='testpass123',
            role='broker'
        )
        
        # Create contact for first user
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Create lead for first user
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new'
        )
        
        # Switch to other user
        self.client.force_authenticate(user=other_user)
        
        # Other user should not be able to access contact
        response = self.client.get(f'/api/crm/contacts/{contact.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Other user should not be able to access lead
        response = self.client.get(f'/api/crm/leads/{lead.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Other user should not be able to create lead with contact from first user
        lead_data = {
            'contact_id_write': contact.id,
            'asset_id': self.asset.id,
            'status': 'new'
        }
        
        response = self.client.post('/api/crm/leads/', lead_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_crm_data_consistency_integration(self):
        """Test CRM data consistency integration"""
        # Create contact
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Create lead
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new'
        )
        
        # Update contact
        contact.name = 'רות כהן-לוי'
        contact.save()
        
        # Verify lead still shows updated contact name
        response = self.client.get(f'/api/crm/leads/{lead.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['contact']['name'], 'רות כהן-לוי')
        
        # Delete contact
        contact.delete()
        
        # Verify lead is also deleted (CASCADE)
        response = self.client.get(f'/api/crm/leads/{lead.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_crm_performance_integration(self):
        """Test CRM performance integration"""
        # Create many contacts and leads
        contacts = []
        leads = []
        
        for i in range(50):
            contact = Contact.objects.create(
                owner=self.user,
                name=f'Contact {i}',
                email=f'contact{i}@example.com'
            )
            contacts.append(contact)
            
            lead = Lead.objects.create(
                contact=contact,
                asset=self.asset,
                status='new'
            )
            leads.append(lead)
        
        # Test pagination
        response = self.client.get('/api/crm/contacts/?page=1&page_size=25')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 25)
        
        # Test search performance
        response = self.client.get('/api/crm/contacts/search/?q=Contact 1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        
        # Test leads filtering
        response = self.client.get('/api/crm/leads/?status=new')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 50)
