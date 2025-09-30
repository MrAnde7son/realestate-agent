"""
Tests for CRM apps
"""
import pytest
from django.test import TestCase
from django.apps import apps
from crm.apps import CrmConfig


class CrmAppsTests(TestCase):
    """Tests for CRM apps"""
    
    def test_crm_config(self):
        """Test CrmConfig configuration"""
        config = CrmConfig('crm', apps)
        
        self.assertEqual(config.name, 'crm')
        self.assertEqual(config.verbose_name, 'CRM')
    
    def test_crm_app_registration(self):
        """Test CRM app is registered"""
        from django.conf import settings
        
        self.assertIn('crm', settings.INSTALLED_APPS)
    
    def test_crm_models_registration(self):
        """Test CRM models are registered"""
        from crm.models import Contact, Lead
        
        # Models should be available
        self.assertIsNotNone(Contact)
        self.assertIsNotNone(Lead)
    
    def test_crm_admin_registration(self):
        """Test CRM admin is registered"""
        from django.contrib.admin.sites import site
        from crm.models import Contact, Lead
        
        # Models should be registered in admin
        self.assertIn(Contact, site._registry)
        self.assertIn(Lead, site._registry)
    
    def test_crm_urls_registration(self):
        """Test CRM URLs are registered"""
        from django.urls import reverse
        
        # URLs should be accessible
        try:
            reverse('contacts-list')
            reverse('leads-list')
        except Exception as e:
            self.fail(f"CRM URLs not properly registered: {e}")
    
    def test_crm_serializers_registration(self):
        """Test CRM serializers are registered"""
        from crm.serializers import ContactSerializer, LeadSerializer
        
        # Serializers should be available
        self.assertIsNotNone(ContactSerializer)
        self.assertIsNotNone(LeadSerializer)
    
    def test_crm_views_registration(self):
        """Test CRM views are registered"""
        from crm.views import ContactViewSet, LeadViewSet
        
        # Views should be available
        self.assertIsNotNone(ContactViewSet)
        self.assertIsNotNone(LeadViewSet)
    
    def test_crm_permissions_registration(self):
        """Test CRM permissions are registered"""
        from crm.permissions import IsOwnerContact
        
        # Permissions should be available
        self.assertIsNotNone(IsOwnerContact)
    
    def test_crm_services_registration(self):
        """Test CRM services are registered"""
        from crm.services import notify_asset_change, send_report_to_contact
        
        # Services should be available
        self.assertIsNotNone(notify_asset_change)
        self.assertIsNotNone(send_report_to_contact)
