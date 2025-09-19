"""
Tests for CRM models
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from core.models import Asset
from crm.models import Contact, Lead, LeadStatus

User = get_user_model()


class CrmModelsTests(TestCase):
    """Tests for CRM models"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
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
    
    def test_contact_creation(self):
        """Test Contact model creation"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com',
            phone='050-1234567',
            tags=['VIP', 'משקיע']
        )
        
        self.assertEqual(contact.name, 'רות כהן')
        self.assertEqual(contact.email, 'rut@example.com')
        self.assertEqual(contact.phone, '050-1234567')
        self.assertEqual(contact.tags, ['VIP', 'משקיע'])
        self.assertEqual(contact.owner, self.user)
        self.assertIsNotNone(contact.created_at)
        self.assertIsNotNone(contact.updated_at)
    
    def test_contact_str_representation(self):
        """Test Contact model string representation"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        self.assertEqual(str(contact), 'רות כהן (rut@example.com)')
        
        # Test with no email
        contact_no_email = Contact.objects.create(
            owner=self.user,
            name='דוד לוי',
            phone='050-1234567'
        )
        
        self.assertEqual(str(contact_no_email), 'דוד לוי (no-email)')
    
    def test_contact_meta_indexes(self):
        """Test Contact model Meta indexes"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Test that indexes are created
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND tbl_name='crm_contact'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            
            # Should have indexes for owner and name
            self.assertTrue(any('owner' in idx for idx in indexes))
            self.assertTrue(any('name' in idx for idx in indexes))
    
    def test_contact_unique_constraints(self):
        """Test Contact model unique constraints"""
        # Create first contact
        Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Try to create duplicate contact with same email for same owner
        with self.assertRaises(Exception):  # Should raise IntegrityError
            Contact.objects.create(
                owner=self.user,
                name='רות כהן אחרת',
                email='rut@example.com'
            )
        
        # But different owner can have same email
        other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='testpass123'
        )
        
        other_contact = Contact.objects.create(
            owner=other_user,
            name='רות כהן אחרת',
            email='rut@example.com'
        )
        
        self.assertIsNotNone(other_contact)
    
    def test_contact_blank_fields(self):
        """Test Contact model blank fields"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן'
            # No email, phone, or tags
        )
        
        self.assertEqual(contact.email, '')
        self.assertEqual(contact.phone, '')
        self.assertEqual(contact.tags, [])
    
    def test_lead_status_choices(self):
        """Test LeadStatus choices"""
        choices = LeadStatus.choices
        
        expected_choices = [
            ('new', 'New'),
            ('contacted', 'Contacted'),
            ('interested', 'Interested'),
            ('negotiating', 'Negotiating'),
            ('closed-won', 'Closed Won'),
            ('closed-lost', 'Closed Lost')
        ]
        
        self.assertEqual(choices, expected_choices)
    
    def test_lead_creation(self):
        """Test Lead model creation"""
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
        
        self.assertEqual(lead.contact, contact)
        self.assertEqual(lead.asset, self.asset)
        self.assertEqual(lead.status, 'new')
        self.assertEqual(lead.notes, [{'ts': '2024-01-01T12:00:00Z', 'text': 'Test note'}])
        self.assertIsNotNone(lead.created_at)
        self.assertIsNotNone(lead.last_activity_at)
    
    def test_lead_str_representation(self):
        """Test Lead model string representation"""
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
        
        self.assertEqual(str(lead), f'Lead({contact.id} -> {self.asset.id})')
    
    def test_lead_meta_indexes(self):
        """Test Lead model Meta indexes"""
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
        
        # Test that indexes are created
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND tbl_name='crm_lead'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            
            # Should have indexes for status and last_activity_at
            self.assertTrue(any('status' in idx for idx in indexes))
            self.assertTrue(any('last_activity_at' in idx for idx in indexes))
    
    def test_lead_unique_constraints(self):
        """Test Lead model unique constraints"""
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
        with self.assertRaises(Exception):  # Should raise IntegrityError
            Lead.objects.create(
                contact=contact,
                asset=self.asset,
                status='contacted'
            )
    
    def test_lead_default_values(self):
        """Test Lead model default values"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset
            # No status or notes specified
        )
        
        self.assertEqual(lead.status, 'new')
        self.assertEqual(lead.notes, [])
    
    def test_lead_blank_fields(self):
        """Test Lead model blank fields"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new',
            notes=[]
        )
        
        self.assertEqual(lead.notes, [])
    
    def test_contact_lead_relationship(self):
        """Test Contact-Lead relationship"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Create multiple leads for the same contact
        lead1 = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new'
        )
        
        lead2 = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='contacted'
        )
        
        # Test reverse relationship
        leads = contact.leads.all()
        self.assertEqual(leads.count(), 2)
        self.assertIn(lead1, leads)
        self.assertIn(lead2, leads)
    
    def test_asset_lead_relationship(self):
        """Test Asset-Lead relationship"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Create multiple leads for the same asset
        lead1 = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new'
        )
        
        lead2 = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='contacted'
        )
        
        # Test reverse relationship
        leads = self.asset.leads.all()
        self.assertEqual(leads.count(), 2)
        self.assertIn(lead1, leads)
        self.assertIn(lead2, leads)
    
    def test_contact_cascade_delete(self):
        """Test Contact cascade delete"""
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
        
        # Delete contact
        contact.delete()
        
        # Verify lead is also deleted
        self.assertFalse(Lead.objects.filter(id=lead.id).exists())
    
    def test_asset_cascade_delete(self):
        """Test Asset cascade delete"""
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
        
        # Delete asset
        self.asset.delete()
        
        # Verify lead is also deleted
        self.assertFalse(Lead.objects.filter(id=lead.id).exists())
    
    def test_lead_status_validation(self):
        """Test Lead status validation"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Test valid status
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new'
        )
        self.assertEqual(lead.status, 'new')
        
        # Test invalid status (should not raise exception at model level)
        lead.status = 'invalid_status'
        lead.save()
        self.assertEqual(lead.status, 'invalid_status')
    
    def test_lead_notes_validation(self):
        """Test Lead notes validation"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Test valid notes format
        valid_notes = [
            {'ts': '2024-01-01T12:00:00Z', 'text': 'First note'},
            {'ts': '2024-01-01T13:00:00Z', 'text': 'Second note'}
        ]
        
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new',
            notes=valid_notes
        )
        
        self.assertEqual(lead.notes, valid_notes)
        
        # Test invalid notes format (should not raise exception at model level)
        invalid_notes = 'invalid_notes_format'
        lead.notes = invalid_notes
        lead.save()
        self.assertEqual(lead.notes, invalid_notes)
    
    def test_contact_tags_validation(self):
        """Test Contact tags validation"""
        # Test valid tags
        valid_tags = ['VIP', 'משקיע', 'חוזר']
        
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com',
            tags=valid_tags
        )
        
        self.assertEqual(contact.tags, valid_tags)
        
        # Test invalid tags format (should not raise exception at model level)
        invalid_tags = 'invalid_tags_format'
        contact.tags = invalid_tags
        contact.save()
        self.assertEqual(contact.tags, invalid_tags)
    
    def test_lead_last_activity_at_auto_update(self):
        """Test Lead last_activity_at auto update"""
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
        
        original_activity = lead.last_activity_at
        
        # Update lead
        lead.status = 'contacted'
        lead.save()
        
        # Verify last_activity_at was updated
        lead.refresh_from_db()
        self.assertGreater(lead.last_activity_at, original_activity)
    
    def test_contact_updated_at_auto_update(self):
        """Test Contact updated_at auto update"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        original_updated = contact.updated_at
        
        # Update contact
        contact.name = 'רות כהן-לוי'
        contact.save()
        
        # Verify updated_at was updated
        contact.refresh_from_db()
        self.assertGreater(contact.updated_at, original_updated)
    
    def test_lead_created_at_immutable(self):
        """Test Lead created_at is immutable"""
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
        
        original_created = lead.created_at
        
        # Update lead
        lead.status = 'contacted'
        lead.save()
        
        # Verify created_at was not changed
        lead.refresh_from_db()
        self.assertEqual(lead.created_at, original_created)
    
    def test_contact_created_at_immutable(self):
        """Test Contact created_at is immutable"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        original_created = contact.created_at
        
        # Update contact
        contact.name = 'רות כהן-לוי'
        contact.save()
        
        # Verify created_at was not changed
        contact.refresh_from_db()
        self.assertEqual(contact.created_at, original_created)
    
    def test_lead_notes_timeline(self):
        """Test Lead notes timeline functionality"""
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
        notes = [
            {'ts': '2024-01-01T12:00:00Z', 'text': 'First note'},
            {'ts': '2024-01-01T13:00:00Z', 'text': 'Second note'},
            {'ts': '2024-01-01T14:00:00Z', 'text': 'Third note'}
        ]
        
        for note in notes:
            lead.notes.append(note)
            lead.save()
        
        # Verify all notes were added
        lead.refresh_from_db()
        self.assertEqual(len(lead.notes), 3)
        
        # Verify notes are in correct order
        for i, note in enumerate(lead.notes):
            self.assertEqual(note['text'], notes[i]['text'])
    
    def test_contact_lead_count(self):
        """Test Contact lead count"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Create multiple leads
        for i in range(5):
            Lead.objects.create(
                contact=contact,
                asset=self.asset,
                status='new'
            )
        
        # Test lead count
        self.assertEqual(contact.leads.count(), 5)
    
    def test_asset_lead_count(self):
        """Test Asset lead count"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Create multiple leads
        for i in range(3):
            Lead.objects.create(
                contact=contact,
                asset=self.asset,
                status='new'
            )
        
        # Test lead count
        self.assertEqual(self.asset.leads.count(), 3)
    
    def test_lead_status_choices_validation(self):
        """Test Lead status choices validation"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Test all valid statuses
        valid_statuses = [choice[0] for choice in LeadStatus.choices]
        
        for status in valid_statuses:
            lead = Lead.objects.create(
                contact=contact,
                asset=self.asset,
                status=status
            )
            self.assertEqual(lead.status, status)
    
    def test_contact_email_optional(self):
        """Test Contact email is optional"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            phone='050-1234567'
            # No email
        )
        
        self.assertEqual(contact.email, '')
        self.assertEqual(contact.phone, '050-1234567')
    
    def test_contact_phone_optional(self):
        """Test Contact phone is optional"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
            # No phone
        )
        
        self.assertEqual(contact.email, 'rut@example.com')
        self.assertEqual(contact.phone, '')
    
    def test_lead_notes_optional(self):
        """Test Lead notes is optional"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new'
            # No notes
        )
        
        self.assertEqual(lead.notes, [])
    
    def test_contact_tags_optional(self):
        """Test Contact tags is optional"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
            # No tags
        )
        
        self.assertEqual(contact.tags, [])
    
    def test_lead_contact_asset_required(self):
        """Test Lead contact and asset are required"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        # Test contact is required
        with self.assertRaises(Exception):
            Lead.objects.create(
                asset=self.asset,
                status='new'
            )
        
        # Test asset is required
        with self.assertRaises(Exception):
            Lead.objects.create(
                contact=contact,
                status='new'
            )
    
    def test_contact_owner_required(self):
        """Test Contact owner is required"""
        with self.assertRaises(Exception):
            Contact.objects.create(
                name='רות כהן',
                email='rut@example.com'
            )
    
    def test_lead_status_default(self):
        """Test Lead status default value"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset
            # No status specified
        )
        
        self.assertEqual(lead.status, 'new')
    
    def test_lead_notes_default(self):
        """Test Lead notes default value"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
        )
        
        lead = Lead.objects.create(
            contact=contact,
            asset=self.asset,
            status='new'
            # No notes specified
        )
        
        self.assertEqual(lead.notes, [])
    
    def test_contact_tags_default(self):
        """Test Contact tags default value"""
        contact = Contact.objects.create(
            owner=self.user,
            name='רות כהן',
            email='rut@example.com'
            # No tags specified
        )
        
        self.assertEqual(contact.tags, [])
