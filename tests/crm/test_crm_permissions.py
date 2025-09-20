"""
Tests for CRM permissions
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Asset
from crm.models import Contact, Lead, LeadStatus
from crm.permissions import IsOwnerContact

User = get_user_model()


class CrmPermissionsTests(TestCase):
    """Tests for CRM permissions"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='crm_permissions_test@example.com',
            username='testuser',
            password='testpass123'
        )
        
        self.other_user = User.objects.create_user(
            email='crm_permissions_other@example.com',
            username='crm_permissions_other',
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
    
    def test_is_owner_contact_permission_contact_owner(self):
        """Test IsOwnerContact permission for contact owner"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        permission = IsOwnerContact()
        
        # Test with contact owner
        self.client.force_authenticate(user=self.user)
        request = self.client.request()
        request.user = self.user
        
        self.assertTrue(permission.has_object_permission(request, None, contact))
    
    def test_is_owner_contact_permission_contact_non_owner(self):
        """Test IsOwnerContact permission for non-contact owner"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        permission = IsOwnerContact()
        
        # Test with non-contact owner
        self.client.force_authenticate(user=self.other_user)
        request = self.client.request()
        request.user = self.other_user
        
        self.assertFalse(permission.has_object_permission(request, None, contact))
    
    def test_is_owner_contact_permission_lead_owner(self):
        """Test IsOwnerContact permission for lead owner"""
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
        
        permission = IsOwnerContact()
        
        # Test with lead owner (contact owner)
        self.client.force_authenticate(user=self.user)
        request = self.client.request()
        request.user = self.user
        
        self.assertTrue(permission.has_object_permission(request, None, lead))
    
    def test_is_owner_contact_permission_lead_non_owner(self):
        """Test IsOwnerContact permission for non-lead owner"""
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
        
        permission = IsOwnerContact()
        
        # Test with non-lead owner
        self.client.force_authenticate(user=self.other_user)
        request = self.client.request()
        request.user = self.other_user
        
        self.assertFalse(permission.has_object_permission(request, None, lead))
    
    def test_is_owner_contact_permission_invalid_object(self):
        """Test IsOwnerContact permission with invalid object"""
        permission = IsOwnerContact()
        
        # Test with object that has no owner or contact attribute
        class InvalidObject:
            pass
        
        invalid_obj = InvalidObject()
        
        self.client.force_authenticate(user=self.user)
        request = self.client.request()
        request.user = self.user
        
        self.assertFalse(permission.has_object_permission(request, None, invalid_obj))
    
    def test_contact_viewset_permissions(self):
        """Test ContactViewSet permissions"""
        # Create contact for user
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Create contact for other user
        other_contact = Contact.objects.create(
            owner=self.other_user,
            name='דוד לוי',
            email='david@example.com'
        )
        
        # Test user can access their own contact
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/crm/contacts/{contact.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test user cannot access other user's contact
        response = self.client.get(f'/api/crm/contacts/{other_contact.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test user can list only their own contacts
        response = self.client.get('/api/crm/contacts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], contact.id)
    
    def test_lead_viewset_permissions(self):
        """Test LeadViewSet permissions"""
        # Create contact and lead for user
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
        
        # Test user can access their own lead
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/crm/leads/{lead.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test user cannot access other user's lead
        response = self.client.get(f'/api/crm/leads/{other_lead.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test user can list only their own leads
        response = self.client.get('/api/crm/leads/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], lead.id)
    
    def test_contact_creation_permissions(self):
        """Test contact creation permissions"""
        # Test authenticated user can create contact
        self.client.force_authenticate(user=self.user)
        
        data = {
            'name': 'רות כהן',
            'email': 'rut@example.com'
        }
        
        response = self.client.post('/api/crm/contacts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify contact was created with correct owner
        contact = Contact.objects.get(email='rut@example.com')
        self.assertEqual(contact.owner, self.user)
    
    def test_contact_creation_unauthorized(self):
        """Test contact creation without authentication"""
        data = {
            'name': 'רות כהן',
            'email': 'rut@example.com'
        }
        
        response = self.client.post('/api/crm/contacts/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_lead_creation_permissions(self):
        """Test lead creation permissions"""
        # Create contact for user
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Create contact for other user
        other_contact = Contact.objects.create(
            owner=self.other_user,
            name='דוד לוי',
            email='david@example.com'
        )
        
        # Test user can create lead with their own contact
        self.client.force_authenticate(user=self.user)
        
        data = {
            'contact_id': contact.id,
            'asset_id': self.asset.id,
            'status': 'new'
        }
        
        response = self.client.post('/api/crm/leads/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test user cannot create lead with other user's contact
        data = {
            'contact_id': other_contact.id,
            'asset_id': self.asset.id,
            'status': 'new'
        }
        
        response = self.client.post('/api/crm/leads/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('No permission on this contact', str(response.data))
    
    def test_contact_update_permissions(self):
        """Test contact update permissions"""
        # Create contact for user
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Create contact for other user
        other_contact = Contact.objects.create(
            owner=self.other_user,
            name='דוד לוי',
            email='david@example.com'
        )
        
        # Test user can update their own contact
        self.client.force_authenticate(user=self.user)
        
        data = {
            'name': 'רות כהן-לוי',
            'email': 'rut@example.com'
        }
        
        response = self.client.put(f'/api/crm/contacts/{contact.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test user cannot update other user's contact
        data = {
            'name': 'דוד לוי-כהן',
            'email': 'david@example.com'
        }
        
        response = self.client.put(f'/api/crm/contacts/{other_contact.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_contact_delete_permissions(self):
        """Test contact delete permissions"""
        # Create contact for user
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Create contact for other user
        other_contact = Contact.objects.create(
            owner=self.other_user,
            name='דוד לוי',
            email='david@example.com'
        )
        
        # Test user can delete their own contact
        self.client.force_authenticate(user=self.user)
        
        response = self.client.delete(f'/api/crm/contacts/{contact.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify contact was deleted
        self.assertFalse(Contact.objects.filter(id=contact.id).exists())
        
        # Test user cannot delete other user's contact
        response = self.client.delete(f'/api/crm/contacts/{other_contact.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify other contact still exists
        self.assertTrue(Contact.objects.filter(id=other_contact.id).exists())
    
    def test_lead_update_permissions(self):
        """Test lead update permissions"""
        # Create contact and lead for user
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
        
        # Test user can update their own lead
        self.client.force_authenticate(user=self.user)
        
        data = {
            'contact_id': contact.id,
            'asset_id': self.asset.id,
            'status': 'contacted'
        }
        
        response = self.client.put(f'/api/crm/leads/{lead.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test user cannot update other user's lead
        data = {
            'contact_id': other_contact.id,
            'asset_id': self.asset.id,
            'status': 'contacted'
        }
        
        response = self.client.put(f'/api/crm/leads/{other_lead.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_lead_delete_permissions(self):
        """Test lead delete permissions"""
        # Create contact and lead for user
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
        
        # Test user can delete their own lead
        self.client.force_authenticate(user=self.user)
        
        response = self.client.delete(f'/api/crm/leads/{lead.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify lead was deleted
        self.assertFalse(Lead.objects.filter(id=lead.id).exists())
        
        # Test user cannot delete other user's lead
        response = self.client.delete(f'/api/crm/leads/{other_lead.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify other lead still exists
        self.assertTrue(Lead.objects.filter(id=other_lead.id).exists())
    
    def test_lead_custom_actions_permissions(self):
        """Test lead custom actions permissions"""
        # Create contact and lead for user
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
        
        # Test user can perform actions on their own lead
        self.client.force_authenticate(user=self.user)
        
        # Test set_status
        response = self.client.post(f'/api/crm/leads/{lead.id}/set_status/', {'status': 'contacted'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test add_note
        response = self.client.post(f'/api/crm/leads/{lead.id}/add_note/', {'text': 'Test note'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test send_report
        response = self.client.post(f'/api/crm/leads/{lead.id}/send_report/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test user cannot perform actions on other user's lead
        # Test set_status
        response = self.client.post(f'/api/crm/leads/{other_lead.id}/set_status/', {'status': 'contacted'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test add_note
        response = self.client.post(f'/api/crm/leads/{other_lead.id}/add_note/', {'text': 'Test note'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test send_report
        response = self.client.post(f'/api/crm/leads/{other_lead.id}/send_report/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_permissions_with_multiple_users(self):
        """Test permissions with multiple users"""
        # Create multiple users
        users = []
        for i in range(5):
            user = User.objects.create_user(
                email=f'user{i}@example.com',
                username=f'user{i}',
                password='testpass123'
            )
            users.append(user)
        
        # Create contacts for each user
        contacts = []
        for i, user in enumerate(users):
            contact = Contact.objects.create(
                owner=user,
                name=f'Contact {i}',
                email=f'contact{i}@example.com'
            )
            contacts.append(contact)
        
        # Test each user can only access their own contacts
        for i, user in enumerate(users):
            self.client.force_authenticate(user=user)
            
            # Test user can access their own contact
            response = self.client.get(f'/api/crm/contacts/{contacts[i].id}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Test user cannot access other users' contacts
            for j, other_contact in enumerate(contacts):
                if i != j:
                    response = self.client.get(f'/api/crm/contacts/{other_contact.id}/')
                    self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_permissions_with_anonymous_user(self):
        """Test permissions with anonymous user"""
        # Create contact
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Test anonymous user cannot access contacts
        response = self.client.get(f'/api/crm/contacts/{contact.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test anonymous user cannot create contacts
        data = {
            'name': 'דוד לוי',
            'email': 'david@example.com'
        }
        
        response = self.client.post('/api/crm/contacts/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_permissions_with_superuser(self):
        """Test permissions with superuser"""
        # Create superuser
        superuser = User.objects.create_superuser(
            email='crm_permissions_admin@example.com',
            username='admin',
            password='testpass123'
        )
        
        # Create contact for regular user
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Test superuser can access any contact
        self.client.force_authenticate(user=superuser)
        
        response = self.client.get(f'/api/crm/contacts/{contact.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test superuser can create contacts
        data = {
            'name': 'דוד לוי',
            'email': 'david@example.com'
        }
        
        response = self.client.post('/api/crm/contacts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
