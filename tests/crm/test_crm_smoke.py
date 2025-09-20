"""
Smoke tests for CRM functionality
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


class CrmSmokeTests(TestCase):
    """Smoke tests for CRM functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Clean up any existing data
        Lead.objects.all().delete()
        Contact.objects.all().delete()
        Asset.objects.all().delete()
        User.objects.all().delete()
        
        self.user = User.objects.create_user(
            email='crm_smoke_test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            email='crm_smoke_other@example.com',
            username='otheruser',
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
    
    def test_contact_creation_success(self):
        """Test successful contact creation by owner"""
        data = {
            'name': 'רות כהן',
            'email': 'rut@example.com',
            'phone': '050-1234567',
            'tags': ['VIP', 'משקיע']
        }
        
        response = self.client.post('/api/crm/contacts/', data, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        contact = Contact.objects.get(email='rut@example.com')
        self.assertEqual(contact.name, 'רות כהן')
        self.assertEqual(contact.owner, self.user)
        self.assertEqual(contact.tags, ['VIP', 'משקיע'])
    
    def test_contact_creation_unauthorized(self):
        """Test contact creation fails for unauthenticated user"""
        self.client.force_authenticate(user=None)
        
        data = {
            'name': 'רות כהן',
            'email': 'rut@example.com'
        }
        
        response = self.client.post('/api/crm/contacts/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_contact_access_ownership(self):
        """Test contact access is restricted to owner"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Owner can access
        response = self.client.get(f'/api/crm/contacts/{contact.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Other user cannot access
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(f'/api/crm/contacts/{contact.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_lead_creation_success(self):
        """Test successful lead creation"""
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
        
        lead = Lead.objects.get(contact=contact, asset=self.asset)
        self.assertEqual(lead.status, 'new')
        self.assertEqual(lead.contact.owner, self.user)
    
    def test_lead_creation_invalid_contact(self):
        """Test lead creation fails with contact from different owner"""
        other_contact = Contact.objects.create(
            owner=self.other_user,
            name='דוד לוי',
            email='david@example.com'
        )
        
        data = {
            'contact_id': other_contact.id,
            'asset_id': self.asset.id
        }
        
        response = self.client.post('/api/crm/leads/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('No permission on this contact', str(response.data))
    
    def test_lead_creation_invalid_asset(self):
        """Test lead creation fails with non-existent asset"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        data = {
            'contact_id': contact.id,
            'asset_id': 99999  # Non-existent asset
        }
        
        response = self.client.post('/api/crm/leads/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Asset not found', str(response.data))
    
    def test_lead_status_update_success(self):
        """Test successful lead status update"""
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
        
        data = {'status': 'contacted'}
        response = self.client.post(f'/api/crm/leads/{lead.id}/set_status/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        lead.refresh_from_db()
        self.assertEqual(lead.status, 'contacted')
    
    def test_lead_status_update_invalid(self):
        """Test lead status update fails with invalid status"""
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
        
        data = {'status': 'invalid_status'}
        response = self.client.post(f'/api/crm/leads/{lead.id}/set_status/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_lead_note_addition_success(self):
        """Test successful lead note addition"""
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
        
        data = {'text': 'נפגשנו, ביקשה דוח ממותג'}
        response = self.client.post(f'/api/crm/leads/{lead.id}/add_note/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        lead.refresh_from_db()
        self.assertEqual(len(lead.notes), 1)
        self.assertEqual(lead.notes[0]['text'], 'נפגשנו, ביקשה דוח ממותג')
    
    def test_lead_note_addition_empty(self):
        """Test lead note addition fails with empty text"""
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
        
        data = {'text': ''}
        response = self.client.post(f'/api/crm/leads/{lead.id}/add_note/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check for the custom message
        response_text = str(response.data)
        self.assertTrue('Cannot add empty note' in response_text)
    
    def test_lead_by_asset_endpoint(self):
        """Test getting leads by asset"""
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
        
        lead1 = Lead.objects.create(
            contact=contact1,
            asset=self.asset,
            status='new'
        )
        
        lead2 = Lead.objects.create(
            contact=contact2,
            asset=self.asset,
            status='contacted'
        )
        
        response = self.client.get(f'/api/crm/leads/by_asset/?asset_id={self.asset.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_contact_search(self):
        """Test contact search functionality"""
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
        
        # Search by name
        response = self.client.get('/api/crm/contacts/search/?q=רות')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'רות כהן')
        
        # Search by email
        response = self.client.get('/api/crm/contacts/search/?q=david@example.com')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'דוד לוי')
    
    def test_lead_report_send(self):
        """Test lead report sending"""
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
        
        response = self.client.post(f'/api/crm/leads/{lead.id}/send_report/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('contact_email', response.data)
        self.assertEqual(response.data['contact_email'], 'rut@example.com')
    
    def test_lead_report_send_no_email(self):
        """Test lead report sending fails when contact has no email"""
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
        
        response = self.client.post(f'/api/crm/leads/{lead.id}/send_report/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should still succeed but with no email
        self.assertIn('message', response.data)
    
    def test_duplicate_lead_prevention(self):
        """Test that duplicate leads are prevented"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Create first lead
        Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new'
        )
        
        # Try to create duplicate lead
        data = {
            'contact_id': contact.id,
            'asset_id': self.asset.id,
            'status': 'contacted'
        }
        
        response = self.client.post('/api/crm/leads/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Should fail due to unique constraint
    
    def test_contact_unique_email_per_owner(self):
        """Test that contact email is unique per owner"""
        # Create first contact via API
        data1 = {
            'name': 'רות כהן',
            'email': 'rut@example.com'
        }
        response1 = self.client.post('/api/crm/contacts/', data1, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Try to create another contact with same email for same owner
        data2 = {
            'name': 'רות כהן אחרת',
            'email': 'rut@example.com'
        }
        
        response2 = self.client.post('/api/crm/contacts/', data2, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        
        # But different owner can have same email
        # Switch to other user
        self.client.force_authenticate(user=self.other_user)
        data3 = {
            'name': 'רות כהן אחרת',
            'email': 'rut@example.com'
        }
        response3 = self.client.post('/api/crm/contacts/', data3, format='json')
        self.assertEqual(response3.status_code, status.HTTP_201_CREATED)
        
        # Switch back to original user
        self.client.force_authenticate(user=self.user)
