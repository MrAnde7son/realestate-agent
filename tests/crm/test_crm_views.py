"""
Tests for CRM views
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


class CrmViewsTests(TestCase):
    """Tests for CRM views"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='crm_views_test@example.com',
            username='testuser',
            password='testpass123',
            role='broker'
        )
        
        self.other_user = User.objects.create_user(
            email='crm_views_other@example.com',
            username='otheruser',
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
    
    def test_contact_list_view(self):
        """Test ContactViewSet list view"""
        # Create contacts for user
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
        
        # Create contact for other user
        other_contact = Contact.objects.create(
            owner=self.other_user,
            name='שרה גולד',
            email='sara@example.com'
        )
        
        response = self.client.get('/api/crm/contacts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only return user's contacts
        self.assertEqual(len(response.data), 2)
        contact_ids = [contact['id'] for contact in response.data]
        self.assertIn(contact1.id, contact_ids)
        self.assertIn(contact2.id, contact_ids)
        self.assertNotIn(other_contact.id, contact_ids)
    
    def test_contact_create_view(self):
        """Test ContactViewSet create view"""
        data = {
            'name': 'רות כהן',
            'email': 'rut@example.com',
            'phone': '050-1234567',
            'tags': ['VIP', 'משקיע']
        }
        
        response = self.client.post('/api/crm/contacts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify contact was created
        contact = Contact.objects.get(email='rut@example.com')
        self.assertEqual(contact.name, 'רות כהן')
        self.assertEqual(contact.owner, self.user)
        self.assertEqual(contact.tags, ['VIP', 'משקיע'])
    
    def test_contact_retrieve_view(self):
        """Test ContactViewSet retrieve view"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        response = self.client.get(f'/api/crm/contacts/{contact.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(response.data['name'], 'רות כהן')
        self.assertEqual(response.data['email'], 'rut@example.com')
    
    def test_contact_update_view(self):
        """Test ContactViewSet update view"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        data = {
            'name': 'רות כהן-לוי',
            'email': 'rut@example.com',
            'phone': '050-1234567',
            'tags': ['VIP']
        }
        
        response = self.client.put(f'/api/crm/contacts/{contact.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify contact was updated
        contact.refresh_from_db()
        self.assertEqual(contact.name, 'רות כהן-לוי')
        self.assertEqual(contact.phone, '050-1234567')
        self.assertEqual(contact.tags, ['VIP'])
    
    def test_contact_delete_view(self):
        """Test ContactViewSet delete view"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        response = self.client.delete(f'/api/crm/contacts/{contact.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify contact was deleted
        self.assertFalse(Contact.objects.filter(id=contact.id).exists())
    
    def test_contact_search_view(self):
        """Test ContactViewSet search view"""
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
        
        Contact.objects.create(
            owner=self.user,
            name='שרה גולד',
            email='sara@example.com',
            phone='050-9999999'
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
        
        # Search by phone
        response = self.client.get('/api/crm/contacts/search/?q=050-9999999')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'שרה גולד')
    
    def test_contact_export_view(self):
        """Test ContactViewSet export view"""
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
        
        response = self.client.get('/api/crm/contacts/export/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return CSV content
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('רות כהן', response.content.decode())
        self.assertIn('דוד לוי', response.content.decode())
    
    def test_lead_list_view(self):
        """Test LeadViewSet list view"""
        # Create contacts and leads for user
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
        
        # Create lead for other user
        other_contact = Contact.objects.create(
            owner=self.other_user,
            name='שרה גולד',
            email='sara@example.com'
        )
        
        other_lead = Lead.objects.create(
            contact=other_contact,
            asset=self.asset,
            status='new'
        )
        
        response = self.client.get('/api/crm/leads/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only return user's leads
        self.assertEqual(len(response.data), 2)
        lead_ids = [lead['id'] for lead in response.data]
        self.assertIn(lead1.id, lead_ids)
        self.assertIn(lead2.id, lead_ids)
        self.assertNotIn(other_lead.id, lead_ids)
    
    def test_lead_create_view(self):
        """Test LeadViewSet create view"""
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
        
        # Verify lead was created
        lead = Lead.objects.get(contact=contact, asset=self.asset)
        self.assertEqual(lead.status, 'new')
    
    def test_lead_retrieve_view(self):
        """Test LeadViewSet retrieve view"""
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
        
        response = self.client.get(f'/api/crm/leads/{lead.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(response.data['status'], 'new')
        self.assertEqual(response.data['contact']['name'], 'רות כהן')
    
    def test_lead_update_view(self):
        """Test LeadViewSet update view"""
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
        
        data = {
            'contact_id': contact.id,
            'asset_id': self.asset.id,
            'status': 'contacted',
            'notes': [{'ts': '2024-01-01T12:00:00Z', 'text': 'Updated note'}]
        }
        
        response = self.client.put(f'/api/crm/leads/{lead.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify lead was updated
        lead.refresh_from_db()
        self.assertEqual(lead.status, 'contacted')
        self.assertEqual(lead.notes, [{'ts': '2024-01-01T12:00:00Z', 'text': 'Updated note'}])
    
    def test_lead_delete_view(self):
        """Test LeadViewSet delete view"""
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
        
        response = self.client.delete(f'/api/crm/leads/{lead.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify lead was deleted
        self.assertFalse(Lead.objects.filter(id=lead.id).exists())
    
    def test_lead_set_status_action(self):
        """Test LeadViewSet set_status action"""
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
        
        # Verify status was updated
        lead.refresh_from_db()
        self.assertEqual(lead.status, 'contacted')
    
    def test_lead_set_status_invalid_status(self):
        """Test LeadViewSet set_status with invalid status"""
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
        self.assertIn('status', response.data)
    
    def test_lead_add_note_action(self):
        """Test LeadViewSet add_note action"""
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
        
        # Verify note was added
        lead.refresh_from_db()
        self.assertEqual(len(lead.notes), 1)
        self.assertEqual(lead.notes[0]['text'], 'נפגשנו, ביקשה דוח ממותג')
    
    def test_lead_add_note_empty_text(self):
        """Test LeadViewSet add_note with empty text"""
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
        self.assertIn('empty note', response.data['detail'])
    
    def test_lead_send_report_action(self):
        """Test LeadViewSet send_report action"""
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
        
        # Verify response contains expected data
        self.assertIn('message', response.data)
        self.assertIn('contact_email', response.data)
        self.assertEqual(response.data['contact_email'], 'rut@example.com')
    
    def test_lead_send_report_no_email(self):
        """Test LeadViewSet send_report with contact without email"""
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
        self.assertEqual(response.data.get('contact_email'), '')
    
    def test_lead_by_asset_view(self):
        """Test LeadViewSet by_asset view"""
        # Create multiple contacts and leads for the same asset
        contacts = [
            {'name': 'רות כהן', 'email': 'rut@example.com'},
            {'name': 'דוד לוי', 'email': 'david@example.com'},
            {'name': 'שרה גולד', 'email': 'sara@example.com'}
        ]
        
        lead_ids = []
        for contact_data in contacts:
            contact = Contact.objects.create(owner=self.user, **contact_data)
            lead = Lead.objects.create(
                contact=contact,
                asset=self.asset,
                status='new'
            )
            lead_ids.append(lead.id)
        
        response = self.client.get(f'/api/crm/leads/by_asset/?asset_id={self.asset.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return all leads for the asset
        self.assertEqual(len(response.data), 3)
        returned_lead_ids = [lead['id'] for lead in response.data]
        self.assertEqual(set(returned_lead_ids), set(lead_ids))
    
    def test_lead_by_asset_invalid_asset(self):
        """Test LeadViewSet by_asset with invalid asset ID"""
        response = self.client.get('/api/crm/leads/by_asset/?asset_id=99999')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Asset not found', response.data['detail'])
    
    def test_lead_by_asset_missing_asset_id(self):
        """Test LeadViewSet by_asset without asset_id parameter"""
        response = self.client.get('/api/crm/leads/by_asset/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('asset_id is required', response.data['detail'])
    
    def test_lead_filter_by_status(self):
        """Test LeadViewSet filtering by status"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Create leads with different statuses and different assets
        assets = []
        for i in range(3):
            asset = Asset.objects.create(
                street=f'רחוב {i}',
                number=i,
                city='תל אביב',
                price=1000000 + i,
                area=100,
                rooms=3,
                created_by=self.user
            )
            assets.append(asset)
        
        Lead.objects.create(
            contact=contact,
            asset=assets[0],
            status='new'
        )
        
        Lead.objects.create(
            contact=contact,
            asset=assets[1],
            status='contacted'
        )
        
        Lead.objects.create(
            contact=contact,
            asset=assets[2],
            status='interested'
        )
        
        # Filter by status
        response = self.client.get('/api/crm/leads/?status=new')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'new')
        
        response = self.client.get('/api/crm/leads/?status=contacted')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'contacted')
    
    def test_lead_pagination(self):
        """Test LeadViewSet pagination"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Create many leads with different assets
        for i in range(30):
            asset = Asset.objects.create(
                street=f'רחוב {i}',
                number=i,
                city='תל אביב',
                price=1000000 + i,
                area=100,
                rooms=3,
                created_by=self.user
            )
            Lead.objects.create(
                contact=contact,
                asset=asset,
                status='new'
            )
        
        # Test pagination
        response = self.client.get('/api/crm/leads/?page=1&page_size=10')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
    
    def test_contact_pagination(self):
        """Test ContactViewSet pagination"""
        # Create many contacts
        for i in range(30):
            Contact.objects.create(
                owner=self.user,
                name=f'Contact {i}',
                email=f'contact{i}@example.com'
            )
        
        # Test pagination
        response = self.client.get('/api/crm/contacts/?page=1&page_size=10')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
    
    def test_unauthorized_access(self):
        """Test unauthorized access to CRM views"""
        # Test without authentication
        self.client.force_authenticate(user=None)
        
        response = self.client.get('/api/crm/contacts/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.get('/api/crm/leads/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_cross_user_access(self):
        """Test cross-user access prevention"""
        # Create contact and lead for other user
        other_contact = Contact.objects.create(
            owner=self.other_user,
            name='דוד לוי',
            email='david@example.com'
        )
        
        other_lead = Lead.objects.create(
            contact=other_contact,
            asset=self.asset,
            status='new'
        )
        
        # Test user cannot access other user's contact
        response = self.client.get(f'/api/crm/contacts/{other_contact.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test user cannot access other user's lead
        response = self.client.get(f'/api/crm/leads/{other_lead.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
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
            data = {'text': note_text}
            response = self.client.post(f'/api/crm/leads/{lead.id}/add_note/', data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify all notes were added
        lead.refresh_from_db()
        self.assertEqual(len(lead.notes), 3)
        
        # Verify notes are in chronological order
        for i, note in enumerate(lead.notes):
            self.assertEqual(note['text'], notes[i])
    
    def test_lead_status_workflow(self):
        """Test lead status workflow"""
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
        
        for lead_status in statuses:
            data = {'status': lead_status}
            response = self.client.post(f'/api/crm/leads/{lead.id}/set_status/', data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            lead.refresh_from_db()
            self.assertEqual(lead.status, lead_status)
    
    def test_contact_lead_association(self):
        """Test contact-lead association"""
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
        
        # Test that lead shows contact information
        response = self.client.get(f'/api/crm/leads/{lead.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['contact']['name'], 'רות כהן')
        self.assertEqual(response.data['contact']['email'], 'rut@example.com')
    
    def test_lead_duplicate_prevention(self):
        """Test lead duplicate prevention"""
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
    
    def test_contact_duplicate_prevention(self):
        """Test contact duplicate prevention"""
        # Create first contact
        Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Try to create duplicate contact
        data = {
            'name': 'רות כהן אחרת',
            'email': 'rut@example.com'  # Same email
        }
        
        response = self.client.post('/api/crm/contacts/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Should fail due to unique constraint
