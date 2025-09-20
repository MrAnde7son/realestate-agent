"""
Frontend smoke tests for CRM functionality
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Asset
from crm.models import Contact, Lead, LeadStatus

User = get_user_model()


class CrmFrontendSmokeTests(TestCase):
    """Frontend smoke tests for CRM functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='crm_frontend_test@example.com',
            username='testuser',
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
    
    def test_crm_contacts_page_accessible(self):
        """Test that CRM contacts API is accessible"""
        response = self.client.get('/api/crm/contacts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_crm_leads_page_accessible(self):
        """Test that CRM leads API is accessible"""
        response = self.client.get('/api/crm/leads/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_crm_main_page_accessible(self):
        """Test that CRM main API is accessible"""
        response = self.client.get('/api/crm/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_asset_page_with_crm_tab(self):
        """Test that asset API is accessible"""
        response = self.client.get(f'/api/assets/{self.asset.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that CRM tab is present in the response
        self.assertContains(response, 'CRM')
    
    def test_contact_form_validation(self):
        """Test contact form validation"""
        # Test with valid data
        valid_data = {
            'name': 'רות כהן',
            'email': 'rut@example.com',
            'phone': '050-1234567',
            'tags': ['VIP']
        }
        
        response = self.client.post('/api/crm/contacts/', valid_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test with invalid email
        invalid_data = {
            'name': 'רות כהן',
            'email': 'invalid-email',
            'phone': '050-1234567'
        }
        
        response = self.client.post('/api/crm/contacts/', invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_lead_status_badge_colors(self):
        """Test that lead status badges have correct colors"""
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
        
        # Test different statuses
        statuses = ['new', 'contacted', 'interested', 'negotiating', 'closed-won', 'closed-lost']
        
        for status_value in statuses:
            lead.status = status_value
            lead.save()
            
            response = self.client.get(f'/api/crm/leads/{lead.id}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['status'], status_value)
    
    def test_lead_quick_actions(self):
        """Test lead quick actions functionality"""
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
        
        # Test status change
        response = self.client.post(f'/api/crm/leads/{lead.id}/set_status/', {'status': 'contacted'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test note addition
        response = self.client.post(f'/api/crm/leads/{lead.id}/add_note/', {'text': 'Test note'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test report sending
        response = self.client.post(f'/api/crm/leads/{lead.id}/send_report/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_contact_search_functionality(self):
        """Test contact search functionality"""
        # Create test contacts
        Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com',
            phone='050-1234567'
        )
        
        Contact.objects.create(
            owner=self.user,
            name='דוד לוי',
            email='david@example.com',
            phone='050-7654321'
        )
        
        # Test search by name
        response = self.client.get('/api/crm/contacts/search/?q=רות')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test search by email
        response = self.client.get('/api/crm/contacts/search/?q=david@example.com')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test search by phone
        response = self.client.get('/api/crm/contacts/search/?q=050-1234567')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_lead_filtering_by_status(self):
        """Test lead filtering by status"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Create another asset for the second lead
        asset2 = Asset.objects.create(
            street='רחוב דיזנגוף',
            number=2,
            city='תל אביב',
            price=1200000,
            area=120,
            rooms=4,
            created_by=self.user
        )
        
        # Create leads with different statuses
        Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new'
        )
        
        Lead.objects.create(
            contact=contact,
            asset=asset2,
            status='contacted'
        )
        
        # Test filtering by status
        response = self.client.get('/api/crm/leads/?status=new')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        response = self.client.get('/api/crm/leads/?status=contacted')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_contact_lead_association(self):
        """Test that contacts can be associated with leads"""
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
        
        # Test that lead shows contact information
        response = self.client.get(f'/api/crm/leads/{lead.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['contact']['name'], 'רות כהן')
        self.assertEqual(response.data['contact']['email'], 'rut@example.com')
    
    def test_asset_leads_panel(self):
        """Test asset leads panel functionality"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Create lead for asset
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new'
        )
        
        # Test getting leads by asset
        response = self.client.get(f'/api/crm/leads/by_asset/?asset_id={self.asset.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['contact']['name'], 'רות כהן')
    
    def test_contact_creation_from_asset_page(self):
        """Test creating contact from asset page"""
        # Test contact creation
        data = {
            'name': 'רות כהן',
            'email': 'rut@example.com',
            'phone': '050-1234567'
        }
        
        response = self.client.post('/api/crm/contacts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        contact_id = response.data['id']
        
        # Test creating lead with new contact
        lead_data = {
            'contact_id': contact_id,
            'asset_id': self.asset.id,
            'status': 'new'
        }
        
        response = self.client.post('/api/crm/leads/', lead_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify lead was created
        lead = Lead.objects.get(contact_id=contact_id, asset=self.asset)
        self.assertEqual(lead.status, 'new')
    
    def test_lead_notes_timeline(self):
        """Test lead notes timeline functionality"""
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
        
        # Add multiple notes
        notes = ['First note', 'Second note', 'Third note']
        
        for note_text in notes:
            response = self.client.post(f'/api/crm/leads/{lead.id}/add_note/', {'text': note_text})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify all notes were added
        lead.refresh_from_db()
        self.assertEqual(len(lead.notes), 3)
        
        # Verify notes are in chronological order
        for i, note in enumerate(lead.notes):
            self.assertEqual(note['text'], notes[i])
    
    def test_contact_tags_functionality(self):
        """Test contact tags functionality"""
        # Create contact with tags
        data = {
            'name': 'רות כהן',
            'email': 'rut@example.com',
            'tags': ['VIP', 'משקיע', 'חוזר']
        }
        
        response = self.client.post('/api/crm/contacts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        contact_id = response.data['id']
        
        # Verify tags were saved
        contact = Contact.objects.get(id=contact_id)
        self.assertEqual(contact.tags, ['VIP', 'משקיע', 'חוזר'])
        
        # Test updating tags
        update_data = {
            'name': 'רות כהן',
            'email': 'rut@example.com',
            'tags': ['VIP', 'משקיע', 'חוזר', 'חדש']
        }
        
        response = self.client.put(f'/api/crm/contacts/{contact_id}/', update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        contact.refresh_from_db()
        self.assertEqual(contact.tags, ['VIP', 'משקיע', 'חוזר', 'חדש'])
    
    def test_lead_status_workflow(self):
        """Test lead status workflow progression"""
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
        
        # Test status progression
        statuses = ['new', 'contacted', 'interested', 'negotiating', 'closed-won']
        
        for status_value in statuses:
            response = self.client.post(f'/api/crm/leads/{lead.id}/set_status/', {'status': status_value})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            lead.refresh_from_db()
            self.assertEqual(lead.status, status_value)
    
    def test_contact_duplicate_prevention(self):
        """Test contact duplicate prevention"""
        # Create first contact
        data = {
            'name': 'רות כהן',
            'email': 'rut@example.com'
        }
        
        response = self.client.post('/api/crm/contacts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Try to create duplicate contact
        duplicate_data = {
            'name': 'רות כהן אחרת',
            'email': 'rut@example.com'  # Same email
        }
        
        response = self.client.post('/api/crm/contacts/', duplicate_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_lead_duplicate_prevention(self):
        """Test lead duplicate prevention"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Create first lead
        lead_data = {
            'contact_id': contact.id,
            'asset_id': self.asset.id,
            'status': 'new'
        }
        
        response = self.client.post('/api/crm/leads/', lead_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Try to create duplicate lead
        response = self.client.post('/api/crm/leads/', lead_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
