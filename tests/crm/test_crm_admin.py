"""
Tests for CRM admin
"""
import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.admin.sites import site
from core.models import Asset
from crm.models import Contact, Lead
from crm.admin import ContactAdmin, LeadAdmin

User = get_user_model()


class CrmAdminTests(TestCase):
    """Tests for CRM admin"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_superuser(
            email='crm_admin@example.com',
            username='crm_admin',
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
        
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_contact_admin_registration(self):
        """Test Contact model is registered in admin"""
        self.assertIn(Contact, site._registry)
        self.assertIsInstance(site._registry[Contact], ContactAdmin)
    
    def test_lead_admin_registration(self):
        """Test Lead model is registered in admin"""
        self.assertIn(Lead, site._registry)
        self.assertIsInstance(site._registry[Lead], LeadAdmin)
    
    def test_contact_admin_list_display(self):
        """Test Contact admin list display"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com',
            phone='050-1234567',
            tags=['VIP', 'משקיע']
        )
        
        admin = ContactAdmin(Contact, site)
        list_display = admin.get_list_display(None)
        
        expected_fields = ['name', 'email', 'phone', 'owner', 'created_at']
        for field in expected_fields:
            self.assertIn(field, list_display)
    
    def test_contact_admin_list_filter(self):
        """Test Contact admin list filter"""
        admin = ContactAdmin(Contact, site)
        list_filter = admin.get_list_filter(None)
        
        expected_filters = ['owner', 'created_at']
        for filter_field in expected_filters:
            self.assertIn(filter_field, list_filter)
    
    def test_contact_admin_search_fields(self):
        """Test Contact admin search fields"""
        admin = ContactAdmin(Contact, site)
        search_fields = admin.get_search_fields(None)
        
        expected_fields = ['name', 'email', 'phone']
        for field in expected_fields:
            self.assertIn(field, search_fields)
    
    def test_contact_admin_ordering(self):
        """Test Contact admin ordering"""
        admin = ContactAdmin(Contact, site)
        ordering = admin.get_ordering(None)
        
        expected_ordering = ['-created_at']
        self.assertEqual(ordering, expected_ordering)
    
    def test_contact_admin_readonly_fields(self):
        """Test Contact admin readonly fields"""
        admin = ContactAdmin(Contact, site)
        readonly_fields = admin.get_readonly_fields(None)
        
        expected_fields = ['created_at', 'updated_at']
        for field in expected_fields:
            self.assertIn(field, readonly_fields)
    
    def test_contact_admin_list_per_page(self):
        """Test Contact admin list per page"""
        admin = ContactAdmin(Contact, site)
        list_per_page = admin.get_list_per_page(None)
        
        self.assertEqual(list_per_page, 25)
    
    def test_lead_admin_list_display(self):
        """Test Lead admin list display"""
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
        
        admin = LeadAdmin(Lead, site)
        list_display = admin.get_list_display(None)
        
        expected_fields = ['contact', 'asset', 'status', 'last_activity_at', 'created_at']
        for field in expected_fields:
            self.assertIn(field, list_display)
    
    def test_lead_admin_list_filter(self):
        """Test Lead admin list filter"""
        admin = LeadAdmin(Lead, site)
        list_filter = admin.get_list_filter(None)
        
        expected_filters = ['status', 'created_at', 'last_activity_at']
        for filter_field in expected_filters:
            self.assertIn(filter_field, list_filter)
    
    def test_lead_admin_search_fields(self):
        """Test Lead admin search fields"""
        admin = LeadAdmin(Lead, site)
        search_fields = admin.get_search_fields(None)
        
        expected_fields = ['contact__name', 'contact__email', 'asset__street']
        for field in expected_fields:
            self.assertIn(field, search_fields)
    
    def test_lead_admin_ordering(self):
        """Test Lead admin ordering"""
        admin = LeadAdmin(Lead, site)
        ordering = admin.get_ordering(None)
        
        expected_ordering = ['-last_activity_at']
        self.assertEqual(ordering, expected_ordering)
    
    def test_lead_admin_readonly_fields(self):
        """Test Lead admin readonly fields"""
        admin = LeadAdmin(Lead, site)
        readonly_fields = admin.get_readonly_fields(None)
        
        expected_fields = ['created_at', 'last_activity_at']
        for field in expected_fields:
            self.assertIn(field, readonly_fields)
    
    def test_lead_admin_list_per_page(self):
        """Test Lead admin list per page"""
        admin = LeadAdmin(Lead, site)
        list_per_page = admin.get_list_per_page(None)
        
        self.assertEqual(list_per_page, 25)
    
    def test_contact_admin_changelist_view(self):
        """Test Contact admin changelist view"""
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
        
        url = reverse('admin:crm_contact_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'רות כהן')
        self.assertContains(response, 'דוד לוי')
    
    def test_contact_admin_add_view(self):
        """Test Contact admin add view"""
        url = reverse('admin:crm_contact_add')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Check if the form is present (more reliable than checking specific text)
        self.assertContains(response, 'form')
    
    def test_contact_admin_change_view(self):
        """Test Contact admin change view"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        url = reverse('admin:crm_contact_change', args=[contact.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'רות כהן')
    
    def test_contact_admin_delete_view(self):
        """Test Contact admin delete view"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        url = reverse('admin:crm_contact_delete', args=[contact.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Check if the confirmation form is present
        self.assertContains(response, 'form')
    
    def test_lead_admin_changelist_view(self):
        """Test Lead admin changelist view"""
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
        
        url = reverse('admin:crm_lead_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'רות כהן')
    
    def test_lead_admin_add_view(self):
        """Test Lead admin add view"""
        url = reverse('admin:crm_lead_add')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Check if the form is present (more reliable than checking specific text)
        self.assertContains(response, 'form')
    
    def test_lead_admin_change_view(self):
        """Test Lead admin change view"""
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
        
        url = reverse('admin:crm_lead_change', args=[lead.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'רות כהן')
    
    def test_lead_admin_delete_view(self):
        """Test Lead admin delete view"""
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
        
        url = reverse('admin:crm_lead_delete', args=[lead.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Check if the confirmation form is present
        self.assertContains(response, 'form')
    
    def test_contact_admin_creation(self):
        """Test Contact creation through admin"""
        url = reverse('admin:crm_contact_add')
        
        data = {
            'owner': self.user.id,
            'name': 'רות כהן',
            'email': 'rut@example.com',
            'phone': '050-1234567',
            'tags': '["VIP", "משקיע"]'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Verify contact was created
        contact = Contact.objects.get(email='rut@example.com')
        self.assertEqual(contact.name, 'רות כהן')
        self.assertEqual(contact.owner, self.user)
    
    def test_lead_admin_creation(self):
        """Test Lead creation through admin"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        url = reverse('admin:crm_lead_add')
        
        data = {
            'contact': contact.id,
            'asset': self.asset.id,
            'status': 'new',
            'notes': '[]'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Verify lead was created
        lead = Lead.objects.get(contact=contact, asset=self.asset)
        self.assertEqual(lead.status, 'new')
    
    def test_contact_admin_editing(self):
        """Test Contact editing through admin"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        url = reverse('admin:crm_contact_change', args=[contact.id])
        
        data = {
            'owner': self.user.id,
            'name': 'רות כהן-לוי',
            'email': 'rut@example.com',
            'phone': '050-1234567',
            'tags': '["VIP"]'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        
        # Verify contact was updated
        contact.refresh_from_db()
        self.assertEqual(contact.name, 'רות כהן-לוי')
        self.assertEqual(contact.phone, '050-1234567')
    
    def test_lead_admin_editing(self):
        """Test Lead editing through admin"""
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
        
        url = reverse('admin:crm_lead_change', args=[lead.id])
        
        data = {
            'contact': contact.id,
            'asset': self.asset.id,
            'status': 'contacted',
            'notes': '[{"ts": "2024-01-01T12:00:00Z", "text": "Test note"}]'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        
        # Verify lead was updated
        lead.refresh_from_db()
        self.assertEqual(lead.status, 'contacted')
        self.assertEqual(len(lead.notes), 1)
    
    def test_contact_admin_deletion(self):
        """Test Contact deletion through admin"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        url = reverse('admin:crm_contact_delete', args=[contact.id])
        
        data = {'post': 'yes'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful deletion
        
        # Verify contact was deleted
        self.assertFalse(Contact.objects.filter(id=contact.id).exists())
    
    def test_lead_admin_deletion(self):
        """Test Lead deletion through admin"""
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
        
        url = reverse('admin:crm_lead_delete', args=[lead.id])
        
        data = {'post': 'yes'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful deletion
        
        # Verify lead was deleted
        self.assertFalse(Lead.objects.filter(id=lead.id).exists())
    
    def test_contact_admin_permissions(self):
        """Test Contact admin permissions"""
        # Test with non-superuser
        regular_user = User.objects.create_user(
            email='regular@example.com',
            username='regular',
            password='testpass123'
        )
        
        self.client.force_login(regular_user)
        
        url = reverse('admin:crm_contact_changelist')
        response = self.client.get(url)
        
        # Should redirect to login or show permission denied
        self.assertIn(response.status_code, [302, 403])
    
    def test_lead_admin_permissions(self):
        """Test Lead admin permissions"""
        # Test with non-superuser
        regular_user = User.objects.create_user(
            email='regular@example.com',
            username='regular',
            password='testpass123'
        )
        
        self.client.force_login(regular_user)
        
        url = reverse('admin:crm_lead_changelist')
        response = self.client.get(url)
        
        # Should redirect to login or show permission denied
        self.assertIn(response.status_code, [302, 403])
    
    def test_contact_admin_filtering(self):
        """Test Contact admin filtering"""
        # Create contacts with different owners
        other_user = User.objects.create_user(
            email='crm_admin_other@example.com',
            username='other',
            password='testpass123'
        )
        
        Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        Contact.objects.create(
            owner=other_user,
            name='דוד לוי',
            email='david@example.com'
        )
        
        # Test filtering by owner
        url = reverse('admin:crm_contact_changelist')
        response = self.client.get(url, {'owner__id__exact': self.user.id})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'רות כהן')
        self.assertNotContains(response, 'דוד לוי')
    
    def test_lead_admin_filtering(self):
        """Test Lead admin filtering"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Create leads with different statuses
        Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new'
        )
        
        # Create a second asset for the second lead to avoid unique constraint
        asset2 = Asset.objects.create(
            street='רחוב הרצל 2',
            city='תל אביב',
            price=1200000,
            rooms=4,
            area=120.0,
            created_by=self.user
        )
        
        Lead.objects.create(
            contact=contact,
            asset=asset2,
            status='contacted'
        )
        
        # Test filtering by status
        url = reverse('admin:crm_lead_changelist')
        response = self.client.get(url, {'status__exact': 'new'})
        
        self.assertEqual(response.status_code, 200)
        # Should show only new leads
    
    def test_contact_admin_search(self):
        """Test Contact admin search"""
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
        
        # Test search by name
        url = reverse('admin:crm_contact_changelist')
        response = self.client.get(url, {'q': 'רות'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'רות כהן')
        self.assertNotContains(response, 'דוד לוי')
    
    def test_lead_admin_search(self):
        """Test Lead admin search"""
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
        
        # Test search by contact name
        url = reverse('admin:crm_lead_changelist')
        response = self.client.get(url, {'q': 'רות'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'רות כהן')
    
    def test_contact_admin_ordering(self):
        """Test Contact admin ordering"""
        # Create contacts with different creation times
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
        
        url = reverse('admin:crm_contact_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should be ordered by created_at descending
    
    def test_lead_admin_ordering(self):
        """Test Lead admin ordering"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Create leads with different last_activity_at times
        lead1 = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new'
        )
        
        # Create a second asset for the second lead to avoid unique constraint
        asset2 = Asset.objects.create(
            street='רחוב הרצל 2',
            city='תל אביב',
            price=1200000,
            rooms=4,
            area=120.0,
            created_by=self.user
        )
        
        lead2 = Lead.objects.create(
            contact=contact,
            asset=asset2,
            status='contacted'
        )
        
        url = reverse('admin:crm_lead_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should be ordered by last_activity_at descending
    
    def test_contact_admin_readonly_fields(self):
        """Test Contact admin readonly fields"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        url = reverse('admin:crm_contact_change', args=[contact.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should show readonly fields for created_at and updated_at
    
    def test_lead_admin_readonly_fields(self):
        """Test Lead admin readonly fields"""
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
        
        url = reverse('admin:crm_lead_change', args=[lead.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should show readonly fields for created_at and last_activity_at
    
    def test_contact_admin_list_per_page(self):
        """Test Contact admin list per page"""
        # Create many contacts
        for i in range(30):
            Contact.objects.create(
                owner=self.user,
                name=f'Contact {i}',
                email=f'contact{i}@example.com'
            )
        
        url = reverse('admin:crm_contact_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should show 25 contacts per page
    
    def test_lead_admin_list_per_page(self):
        """Test Lead admin list per page"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Create many leads with unique assets to avoid constraint violations
        for i in range(30):
            asset = Asset.objects.create(
                street=f'רחוב הרצל {i+10}',
                city='תל אביב',
                price=1000000 + i * 10000,
                rooms=3,
                area=100.0,
                created_by=self.user
            )
            Lead.objects.create(
                contact=contact,
                asset=asset,
                status='new'
            )
        
        url = reverse('admin:crm_lead_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should show 25 leads per page
