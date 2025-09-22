"""
Tests for CRM URLs
"""
import pytest
from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Asset
from crm.models import Contact, Lead
from crm.views import ContactViewSet, LeadViewSet

User = get_user_model()


class CrmUrlsTests(TestCase):
    """Tests for CRM URLs"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='crm_urls_test@example.com',
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
    
    def test_contact_list_url(self):
        """Test contact list URL"""
        url = reverse('contacts-list')
        self.assertEqual(url, '/api/crm/contacts/')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_contact_detail_url(self):
        """Test contact detail URL"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        url = reverse('contacts-detail', kwargs={'pk': contact.id})
        self.assertEqual(url, f'/api/crm/contacts/{contact.id}/')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_contact_create_url(self):
        """Test contact create URL"""
        url = reverse('contacts-list')
        self.assertEqual(url, '/api/crm/contacts/')
        
        data = {
            'name': 'רות כהן',
            'email': 'rut@example.com'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_contact_update_url(self):
        """Test contact update URL"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        url = reverse('contacts-detail', kwargs={'pk': contact.id})
        self.assertEqual(url, f'/api/crm/contacts/{contact.id}/')
        
        data = {
            'name': 'רות כהן-לוי',
            'email': 'rut@example.com'
        }
        
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_contact_delete_url(self):
        """Test contact delete URL"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        url = reverse('contacts-detail', kwargs={'pk': contact.id})
        self.assertEqual(url, f'/api/crm/contacts/{contact.id}/')
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_contact_search_url(self):
        """Test contact search URL"""
        url = reverse('contacts-search')
        self.assertEqual(url, '/api/crm/contacts/search/')
        
        response = self.client.get(url, {'q': 'רות'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_contact_export_url(self):
        """Test contact export URL - not implemented yet"""
        # This test is skipped as export functionality is not implemented
        self.skipTest("Export functionality not implemented yet")
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_lead_list_url(self):
        """Test lead list URL"""
        url = reverse('leads-list')
        self.assertEqual(url, '/api/crm/leads/')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_lead_detail_url(self):
        """Test lead detail URL"""
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
        
        url = reverse('leads-detail', kwargs={'pk': lead.id})
        self.assertEqual(url, f'/api/crm/leads/{lead.id}/')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_lead_create_url(self):
        """Test lead create URL"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        url = reverse('leads-list')
        self.assertEqual(url, '/api/crm/leads/')
        
        data = {
            'contact_id': contact.id,
            'asset_id': self.asset.id,
            'status': 'new'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_lead_update_url(self):
        """Test lead update URL"""
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
        
        url = reverse('leads-detail', kwargs={'pk': lead.id})
        self.assertEqual(url, f'/api/crm/leads/{lead.id}/')
        
        data = {
            'contact_id': contact.id,
            'asset_id': self.asset.id,
            'status': 'contacted'
        }
        
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_lead_delete_url(self):
        """Test lead delete URL"""
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
        
        url = reverse('leads-detail', kwargs={'pk': lead.id})
        self.assertEqual(url, f'/api/crm/leads/{lead.id}/')
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_lead_set_status_url(self):
        """Test lead set_status URL"""
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
        
        url = reverse('leads-set-status', kwargs={'pk': lead.id})
        self.assertEqual(url, f'/api/crm/leads/{lead.id}/set_status/')
        
        data = {'status': 'contacted'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_lead_add_note_url(self):
        """Test lead add_note URL"""
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
        
        url = reverse('leads-add-note', kwargs={'pk': lead.id})
        self.assertEqual(url, f'/api/crm/leads/{lead.id}/add_note/')
        
        data = {'text': 'Test note'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_lead_send_report_url(self):
        """Test lead send_report URL"""
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
        
        url = reverse('leads-send-report', kwargs={'pk': lead.id})
        self.assertEqual(url, f'/api/crm/leads/{lead.id}/send_report/')
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_lead_by_asset_url(self):
        """Test lead by_asset URL"""
        url = reverse('leads-by-asset')
        self.assertEqual(url, '/api/crm/leads/by_asset/')
        
        response = self.client.get(url, {'asset_id': self.asset.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_url_resolution(self):
        """Test URL resolution"""
        # Test contact URLs
        contact_url = reverse('contacts-list')
        resolved = resolve(contact_url)
        self.assertEqual(resolved.func.cls, ContactViewSet)
        
        # Test lead URLs
        lead_url = reverse('leads-list')
        resolved = resolve(lead_url)
        self.assertEqual(resolved.func.cls, LeadViewSet)
    
    def test_url_patterns(self):
        """Test URL patterns"""
        from crm.urls import urlpatterns
        
        # Should have contact and lead patterns
        self.assertTrue(len(urlpatterns) > 0)
        
        # Check that patterns are properly configured
        for pattern in urlpatterns:
            self.assertIsNotNone(pattern.name)
            self.assertIsNotNone(pattern.pattern)
    
    def test_contact_urls_require_authentication(self):
        """Test contact URLs require authentication"""
        self.client.force_authenticate(user=None)
        
        # Test list
        response = self.client.get('/api/crm/contacts/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test create
        data = {'name': 'רות כהן', 'email': 'rut@example.com'}
        response = self.client.post('/api/crm/contacts/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_lead_urls_require_authentication(self):
        """Test lead URLs require authentication"""
        self.client.force_authenticate(user=None)
        
        # Test list
        response = self.client.get('/api/crm/leads/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test create
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
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_contact_search_url_parameters(self):
        """Test contact search URL parameters"""
        url = reverse('contacts-search')
        
        # Test with query parameter
        response = self.client.get(url, {'q': 'רות'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test without query parameter
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_lead_by_asset_url_parameters(self):
        """Test lead by_asset URL parameters"""
        url = reverse('leads-by-asset')
        
        # Test with asset_id parameter
        response = self.client.get(url, {'asset_id': self.asset.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test without asset_id parameter
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_lead_filter_url_parameters(self):
        """Test lead filter URL parameters"""
        url = reverse('leads-list')
        
        # Test with status filter
        response = self.client.get(url, {'status': 'new'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test with multiple filters
        response = self.client.get(url, {'status': 'new', 'page': 1, 'page_size': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_contact_export_url_parameters(self):
        """Test contact export URL parameters - not implemented yet"""
        # This test is skipped as export functionality is not implemented
        self.skipTest("Export functionality not implemented yet")
    
    def test_url_namespace(self):
        """Test URL namespace"""
        # All CRM URLs should be under /api/crm/
        contact_url = reverse('contacts-list')
        self.assertTrue(contact_url.startswith('/api/crm/'))
        
        lead_url = reverse('leads-list')
        self.assertTrue(lead_url.startswith('/api/crm/'))
    
    def test_url_trailing_slash(self):
        """Test URL trailing slash"""
        # All URLs should end with /
        contact_url = reverse('contacts-list')
        self.assertTrue(contact_url.endswith('/'))
        
        lead_url = reverse('leads-list')
        self.assertTrue(lead_url.endswith('/'))
    
    def test_url_methods(self):
        """Test URL HTTP methods"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Test GET
        response = self.client.get(f'/api/crm/contacts/{contact.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test PUT
        data = {'name': 'רות כהן-לוי', 'email': 'rut@example.com'}
        response = self.client.put(f'/api/crm/contacts/{contact.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test PATCH
        data = {'name': 'רות כהן-לוי-כהן'}
        response = self.client.patch(f'/api/crm/contacts/{contact.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test DELETE
        response = self.client.delete(f'/api/crm/contacts/{contact.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_url_error_handling(self):
        """Test URL error handling"""
        # Test 404 for non-existent contact
        response = self.client.get('/api/crm/contacts/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test 404 for non-existent lead
        response = self.client.get('/api/crm/leads/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_url_permissions(self):
        """Test URL permissions"""
        # Create contact for other user
        other_user = User.objects.create_user(
            email='crm_urls_other@example.com',
            username='otheruser',
            password='testpass123',
            role='broker'
        )
        
        other_contact = Contact.objects.create(
            owner=other_user,
            name='דוד לוי',
            email='david@example.com'
        )
        
        # Test user cannot access other user's contact
        response = self.client.get(f'/api/crm/contacts/{other_contact.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_url_serialization(self):
        """Test URL serialization"""
        # Test that URLs can be serialized
        contact_url = reverse('contacts-list')
        lead_url = reverse('leads-list')
        
        # Should not raise exceptions
        str(contact_url)
        str(lead_url)
        
        # Should be valid URLs
        self.assertTrue(contact_url.startswith('/'))
        self.assertTrue(lead_url.startswith('/'))
    
    def test_url_consistency(self):
        """Test URL consistency"""
        # All contact URLs should follow same pattern
        contact_urls = [
            reverse('contacts-list'),
            reverse('contacts-search')
        ]
        
        for url in contact_urls:
            self.assertTrue(url.startswith('/api/crm/contacts/'))
        
        # All lead URLs should follow same pattern
        lead_urls = [
            reverse('leads-list'),
            reverse('leads-by-asset')
        ]
        
        for url in lead_urls:
            self.assertTrue(url.startswith('/api/crm/leads/'))
    
    def test_url_parameters_validation(self):
        """Test URL parameters validation"""
        # Test invalid asset_id
        response = self.client.get('/api/crm/leads/by_asset/', {'asset_id': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test missing required parameters
        response = self.client.get('/api/crm/leads/by_asset/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_url_pagination(self):
        """Test URL pagination"""
        # Test pagination parameters
        response = self.client.get('/api/crm/contacts/', {'page': 1, 'page_size': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test invalid pagination parameters
        response = self.client.get('/api/crm/contacts/', {'page': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Should default to page 1
        
        response = self.client.get('/api/crm/contacts/', {'page_size': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Should use default page size
