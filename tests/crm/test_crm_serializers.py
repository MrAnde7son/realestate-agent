"""
Tests for CRM serializers
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework import status
from datetime import timedelta

from django.utils import timezone

from core.models import Asset
from crm.models import (
    Contact,
    Lead,
    LeadStatus,
    ContactTask,
    ContactMeeting,
    ContactInteraction,
)
from crm.serializers import (
    ContactSerializer,
    LeadSerializer,
    ContactTaskSerializer,
    ContactMeetingSerializer,
    ContactInteractionSerializer,
)

User = get_user_model()


class CrmSerializersTests(TestCase):
    """Tests for CRM serializers"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='crm_serializers_test@example.com',
            username='testuser',
            password='testpass123',
            role='broker'
        )
        
        self.other_user = User.objects.create_user(
            email='crm_serializers_other@example.com',
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
        self.factory = APIRequestFactory()

    def _build_request(self, user):
        class DummyRequest:
            def __init__(self, user):
                self.user = user

        return DummyRequest(user)
    
    def test_contact_serializer_serialization(self):
        """Test ContactSerializer serialization"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com',
            phone='050-1234567',
            tags=['VIP', 'משקיע']
        )
        
        serializer = ContactSerializer(contact)
        data = serializer.data
        
        self.assertEqual(data['id'], contact.id)
        self.assertEqual(data['name'], 'רות כהן')
        self.assertEqual(data['email'], 'rut@example.com')
        self.assertEqual(data['phone'], '050-1234567')
        self.assertEqual(data['tags'], ['VIP', 'משקיע'])
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_contact_serializer_deserialization(self):
        """Test ContactSerializer deserialization"""
        data = {
            'name': 'רות כהן',
            'email': 'rut@example.com',
            'phone': '050-1234567',
            'tags': ['VIP', 'משקיע']
        }
        
        serializer = ContactSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        contact = serializer.save(owner=self.user)
        self.assertEqual(contact.name, 'רות כהן')
        self.assertEqual(contact.email, 'rut@example.com')
        self.assertEqual(contact.phone, '050-1234567')
        self.assertEqual(contact.tags, ['VIP', 'משקיע'])
        self.assertEqual(contact.owner, self.user)
    
    def test_contact_serializer_validation(self):
        """Test ContactSerializer validation"""
        # Test valid data
        data = {
            'name': 'רות כהן',
            'email': 'rut@example.com',
            'phone': '050-1234567',
            'tags': ['VIP']
        }
        
        serializer = ContactSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Test invalid email
        data = {
            'name': 'רות כהן',
            'email': 'invalid-email',
            'phone': '050-1234567'
        }
        
        serializer = ContactSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        
        # Test missing required field
        data = {
            'email': 'rut@example.com',
            'phone': '050-1234567'
        }
        
        serializer = ContactSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_contact_task_serializer_enforces_contact_ownership(self):
        """Task serializer should restrict creation to owned contacts."""
        owned_contact = Contact.objects.create(
            owner=self.user,
            name='Owned Contact',
            email='owned@example.com'
        )
        other_contact = Contact.objects.create(
            owner=self.other_user,
            name='Other Contact',
            email='other@example.com'
        )

        request = self._build_request(self.user)

        serializer = ContactTaskSerializer(
            data={'title': 'Call client', 'contact_id': owned_contact.id},
            context={'request': request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        task = serializer.save(owner=self.user)
        self.assertEqual(task.contact, owned_contact)

        invalid_serializer = ContactTaskSerializer(
            data={'title': 'Follow up', 'contact_id': other_contact.id},
            context={'request': request}
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIn('contact_id', invalid_serializer.errors)

    def test_contact_task_serializer_with_lead(self):
        """Test ContactTaskSerializer with lead_id field"""
        contact = Contact.objects.create(
            owner=self.user,
            name='Test Contact',
            email='test@example.com'
        )
        
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new'
        )

        request = self._build_request(self.user)

        # Test creating task with lead
        serializer = ContactTaskSerializer(
            data={
                'title': 'Follow up with lead',
                'description': 'Call the lead about the property',
                'contact_id_write': contact.id,
                'lead_id': lead.id
            },
            context={'request': request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        task = serializer.save(owner=self.user)
        self.assertEqual(task.contact, contact)
        self.assertEqual(task.lead, lead)
        
        # Test serialization includes lead data
        serialized_data = ContactTaskSerializer(task, context={'request': request}).data
        self.assertIn('lead', serialized_data)
        self.assertIn('lead_id', serialized_data)
        self.assertEqual(serialized_data['lead_id'], lead.id)

    def test_contact_task_serializer_lead_permission_validation(self):
        """Test ContactTaskSerializer validates lead ownership"""
        contact = Contact.objects.create(
            owner=self.user,
            name='Test Contact',
            email='test@example.com'
        )
        
        other_contact = Contact.objects.create(
            owner=self.other_user,
            name='Other Contact',
            email='other@example.com'
        )
        
        other_lead = Lead.objects.create(
            contact=other_contact,
            asset=self.asset,
            status='new'
        )

        request = self._build_request(self.user)

        # Should fail because lead belongs to other user's contact
        serializer = ContactTaskSerializer(
            data={
                'title': 'Follow up with lead',
                'contact_id_write': contact.id,
                'lead_id': other_lead.id
            },
            context={'request': request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('lead_id', serializer.errors)

    def test_contact_meeting_serializer_validation(self):
        """Meeting serializer should validate scheduling and ownership."""
        contact = Contact.objects.create(
            owner=self.user,
            name='Meeting Contact',
            email='meeting@example.com'
        )

        request = self._build_request(self.user)

        scheduled_for = timezone.now() + timedelta(days=7)
        serializer = ContactMeetingSerializer(
            data={
                'title': 'Property tour',
                'scheduled_for': scheduled_for.isoformat(),
                'duration_minutes': 45,
                'location': 'Tel Aviv',
                'contact_id': contact.id
            },
            context={'request': request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        meeting = serializer.save(owner=self.user)
        self.assertEqual(meeting.contact, contact)
        self.assertEqual(meeting.duration_minutes, 45)

    def test_contact_interaction_serializer_validation(self):
        """Interaction serializer should accept communication logs."""
        contact = Contact.objects.create(
            owner=self.user,
            name='Interaction Contact',
            email='interaction@example.com'
        )

        request = self._build_request(self.user)

        occurred_at = timezone.now()
        serializer = ContactInteractionSerializer(
            data={
                'interaction_type': 'email',
                'subject': 'Summary email',
                'notes': 'Sent recap of conversation',
                'occurred_at': occurred_at.isoformat(),
                'contact_id': contact.id
            },
            context={'request': request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        interaction = serializer.save(owner=self.user)
        self.assertEqual(interaction.contact, contact)
        self.assertEqual(interaction.interaction_type, 'email')
    
    def test_contact_serializer_empty_tags(self):
        """Test ContactSerializer with empty tags"""
        data = {
            'name': 'רות כהן',
            'email': 'rut@example.com',
            'tags': []
        }
        
        serializer = ContactSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        contact = serializer.save(owner=self.user)
        self.assertEqual(contact.tags, [])
    
    def test_contact_serializer_no_tags(self):
        """Test ContactSerializer without tags field"""
        data = {
            'name': 'רות כהן',
            'email': 'rut@example.com'
        }
        
        serializer = ContactSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        contact = serializer.save(owner=self.user)
        self.assertEqual(contact.tags, [])
    
    def test_lead_serializer_serialization(self):
        """Test LeadSerializer serialization"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new',
            notes=[{'ts': '2024-01-01T12:00:00Z', 'text': 'Test note'}]
        )
        
        serializer = LeadSerializer(lead)
        data = serializer.data
        
        self.assertEqual(data['id'], lead.id)
        self.assertEqual(data['status'], 'new')
        self.assertEqual(data['notes'], [{'ts': '2024-01-01T12:00:00Z', 'text': 'Test note'}])
        self.assertIn('contact', data)
        self.assertIn('last_activity_at', data)
        self.assertIn('created_at', data)
        
        # Check contact data
        contact_data = data['contact']
        self.assertEqual(contact_data['id'], contact.id)
        self.assertEqual(contact_data['name'], 'רות כהן')
        self.assertEqual(contact_data['email'], 'rut@example.com')
    
    def test_lead_serializer_deserialization(self):
        """Test LeadSerializer deserialization"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        data = {
            'contact_id_write': contact.id,
            'asset_id': self.asset.id,
            'status': 'new',
            'notes': [{'ts': '2024-01-01T12:00:00Z', 'text': 'Test note'}]
        }
        
        # Mock request context
        request = self.client.request()
        request.user = self.user
        
        serializer = LeadSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())
        
        lead = serializer.save()
        self.assertEqual(lead.contact, contact)
        self.assertEqual(lead.asset, self.asset)
        self.assertEqual(lead.status, 'new')
        self.assertEqual(lead.notes, [{'ts': '2024-01-01T12:00:00Z', 'text': 'Test note'}])
    
    def test_lead_serializer_validation_contact_permission(self):
        """Test LeadSerializer validation for contact permission"""
        # Create contact for other user
        other_contact = Contact.objects.create(
            owner=self.other_user,
            name='דוד לוי',
            email='david@example.com'
        )
        
        data = {
            'contact_id': other_contact.id,
            'asset_id': self.asset.id,
            'status': 'new'
        }
        
        # Mock request context with different user
        request = self.client.request()
        request.user = self.user
        
        serializer = LeadSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('No permission on this contact', str(serializer.errors))
    
    def test_lead_serializer_validation_invalid_status(self):
        """Test LeadSerializer validation for invalid status"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        data = {
            'contact_id_write': contact.id,
            'asset_id': self.asset.id,
            'status': 'invalid_status'
        }
        
        request = self.client.request()
        request.user = self.user
        
        serializer = LeadSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)
    
    def test_lead_serializer_validation_invalid_asset(self):
        """Test LeadSerializer validation for invalid asset"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        data = {
            'contact_id_write': contact.id,
            'asset_id': 99999,  # Non-existent asset
            'status': 'new'
        }
        
        request = self.client.request()
        request.user = self.user
        
        serializer = LeadSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('asset_id', serializer.errors)
    
    def test_lead_serializer_empty_notes(self):
        """Test LeadSerializer with empty notes"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        data = {
            'contact_id_write': contact.id,
            'asset_id': self.asset.id,
            'status': 'new',
            'notes': []
        }
        
        request = self.client.request()
        request.user = self.user
        
        serializer = LeadSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())
        
        lead = serializer.save()
        self.assertEqual(lead.notes, [])
    
    def test_lead_serializer_no_notes(self):
        """Test LeadSerializer without notes field"""
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
        
        request = self.client.request()
        request.user = self.user
        
        serializer = LeadSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())
        
        lead = serializer.save()
        self.assertEqual(lead.notes, [])
    
    def test_lead_serializer_notes_validation(self):
        """Test LeadSerializer notes validation"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Test invalid notes format
        data = {
            'contact_id_write': contact.id,
            'asset_id': self.asset.id,
            'status': 'new',
            'notes': 'invalid_notes_format'
        }
        
        request = self.client.request()
        request.user = self.user
        
        serializer = LeadSerializer(data=data, context={'request': request})
        # The serializer converts invalid notes format to a list, so it should be valid
        self.assertTrue(serializer.is_valid())
    
    def test_lead_serializer_contact_id_readable(self):
        """Test LeadSerializer contact_id is readable"""
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
        
        serializer = LeadSerializer(lead)
        data = serializer.data
        
        # contact_id should be in serialized data
        self.assertIn('contact_id', data)
        self.assertEqual(data['contact_id'], contact.id)
        
        # contact should be in serialized data
        self.assertIn('contact', data)
    
    def test_lead_serializer_contact_id_write_field(self):
        """Test LeadSerializer contact_id_write field for creating leads"""
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
        
        request = self.client.request()
        request.user = self.user
        
        serializer = LeadSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())
        
        lead = serializer.save()
        self.assertEqual(lead.contact, contact)
        self.assertEqual(lead.asset, self.asset)
        self.assertEqual(lead.status, 'new')
    
    def test_lead_serializer_asset_id_write_only(self):
        """Test LeadSerializer asset_id is write-only"""
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
        
        serializer = LeadSerializer(lead)
        data = serializer.data
        
        # asset_id should not be in serialized data
        self.assertNotIn('asset_id', data)
    
    def test_contact_serializer_field_validation(self):
        """Test ContactSerializer field validation"""
        # Test name length validation
        data = {
            'name': 'A' * 201,  # Too long
            'email': 'rut@example.com'
        }
        
        serializer = ContactSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
        
        # Test phone length validation
        data = {
            'name': 'רות כהן',
            'phone': 'A' * 31,  # Too long
            'email': 'rut@example.com'
        }
        
        serializer = ContactSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone', serializer.errors)
    
    def test_lead_serializer_status_choices(self):
        """Test LeadSerializer status choices validation"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Test valid status
        data = {
            'contact_id_write': contact.id,
            'asset_id': self.asset.id,
            'status': 'contacted'
        }
        
        request = self.client.request()
        request.user = self.user
        
        serializer = LeadSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())
        
        # Test invalid status
        data = {
            'contact_id_write': contact.id,
            'asset_id': self.asset.id,
            'status': 'invalid_status'
        }
        
        serializer = LeadSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)
    
    def test_contact_serializer_update(self):
        """Test ContactSerializer update functionality"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com',
            phone='050-1234567',
            tags=['VIP']
        )
        
        # Update contact
        data = {
            'name': 'רות כהן-לוי',
            'email': 'rut@example.com',
            'phone': '050-7654321',
            'tags': ['VIP', 'משקיע']
        }
        
        serializer = ContactSerializer(contact, data=data)
        self.assertTrue(serializer.is_valid())
        
        updated_contact = serializer.save()
        self.assertEqual(updated_contact.name, 'רות כהן-לוי')
        self.assertEqual(updated_contact.phone, '050-7654321')
        self.assertEqual(updated_contact.tags, ['VIP', 'משקיע'])
    
    def test_lead_serializer_update(self):
        """Test LeadSerializer update functionality"""
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
        
        # Update lead
        data = {
            'contact_id_write': contact.id,
            'asset_id': self.asset.id,
            'status': 'contacted',
            'notes': [{'ts': '2024-01-01T12:00:00Z', 'text': 'Updated note'}]
        }
        
        request = self.client.request()
        request.user = self.user
        
        serializer = LeadSerializer(lead, data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())
        
        updated_lead = serializer.save()
        self.assertEqual(updated_lead.status, 'contacted')
        self.assertEqual(updated_lead.notes, [{'ts': '2024-01-01T12:00:00Z', 'text': 'Updated note'}])
    
    def test_serializer_meta_fields(self):
        """Test serializer Meta fields configuration"""
        # Test ContactSerializer fields
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        serializer = ContactSerializer(contact)
        expected_fields = ['id', 'name', 'phone', 'email', 'tags', 'created_at', 'updated_at']
        
        for field in expected_fields:
            self.assertIn(field, serializer.data)
        
        # Test LeadSerializer fields
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new'
        )
        
        serializer = LeadSerializer(lead)
        expected_fields = [
            'id', 'contact', 'asset_address', 'asset_price', 'asset_rooms', 
            'asset_area', 'status', 'notes', 'last_activity_at', 'created_at'
        ]
        
        for field in expected_fields:
            self.assertIn(field, serializer.data)
    
    def test_serializer_read_only_fields(self):
        """Test serializer read-only fields"""
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
        
        # Test ContactSerializer read-only fields
        serializer = ContactSerializer(contact)
        data = serializer.data
        
        # These fields should be read-only
        read_only_fields = ['id', 'created_at', 'updated_at']
        for field in read_only_fields:
            self.assertIn(field, data)
        
        # Test LeadSerializer read-only fields
        serializer = LeadSerializer(lead)
        data = serializer.data
        
        # These fields should be read-only
        read_only_fields = ['id', 'contact', 'last_activity_at', 'created_at']
        for field in read_only_fields:
            self.assertIn(field, data)
    
    def test_serializer_write_only_fields(self):
        """Test serializer write-only fields"""
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
        
        # Test LeadSerializer write-only fields
        serializer = LeadSerializer(lead)
        data = serializer.data
        
        # These fields should be write-only
        write_only_fields = ['contact_id', 'asset_id']
        for field in write_only_fields:
            self.assertNotIn(field, data)
    
    def test_serializer_validation_error_messages(self):
        """Test serializer validation error messages"""
        # Test ContactSerializer validation error messages
        data = {
            'name': '',  # Empty name
            'email': 'invalid-email',
            'phone': 'A' * 31  # Too long phone
        }
        
        serializer = ContactSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        
        errors = serializer.errors
        self.assertIn('name', errors)
        self.assertIn('email', errors)
        self.assertIn('phone', errors)
        
        # Test LeadSerializer validation error messages
        data = {
            'contact_id': 99999,  # Non-existent contact
            'asset_id': 99999,    # Non-existent asset
            'status': 'invalid_status'
        }
        
        request = self.client.request()
        request.user = self.user
        
        serializer = LeadSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        
        errors = serializer.errors
        self.assertIn('contact_id', errors)
        self.assertIn('status', errors)
        # Asset validation error is in asset_id field
        self.assertIn('asset_id', errors)
