import os
import tempfile
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from core.models import Asset, Document
from core.storage import document_storage

User = get_user_model()


class DocumentModelTest(TestCase):
    """Test Document model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.asset = Asset.objects.create(
            scope_type='address',
            city='Tel Aviv',
            street='Rothschild Blvd',
            number=1,
            created_by=self.user
        )
    
    def test_document_creation(self):
        """Test creating a document."""
        document = Document.objects.create(
            asset=self.asset,
            user=self.user,
            title='Test Document',
            description='A test document',
            document_type='permit',
            filename='test.pdf',
            file_path='/path/to/test.pdf',
            file_size=1024,
            mime_type='application/pdf'
        )
        
        self.assertEqual(document.title, 'Test Document')
        self.assertEqual(document.asset, self.asset)
        self.assertEqual(document.user, self.user)
        self.assertEqual(document.document_type, 'permit')
        self.assertFalse(document.is_downloadable)  # File doesn't exist
    
    def test_document_str(self):
        """Test document string representation."""
        document = Document.objects.create(
            asset=self.asset,
            user=self.user,
            title='Test Document',
            filename='test.pdf',
            file_path='/path/to/test.pdf',
            file_size=1024,
            mime_type='application/pdf'
        )
        
        expected = f"Document({document.id}, Test Document, other)"
        self.assertEqual(str(document), expected)
    
    def test_document_file_url(self):
        """Test document file URL generation."""
        document = Document.objects.create(
            asset=self.asset,
            user=self.user,
            title='Test Document',
            filename='test.pdf',
            file_path='/path/to/test.pdf',
            file_size=1024,
            mime_type='application/pdf'
        )
        
        expected_url = f"/api/assets/{self.asset.id}/documents/{document.id}/download/"
        self.assertEqual(document.file_url, expected_url)


class DocumentStorageTest(TestCase):
    """Test document storage functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_upload_path(self):
        """Test upload path generation."""
        asset_id = 123
        filename = 'test.pdf'
        
        path = document_storage.get_upload_path(asset_id, filename)
        
        # Should contain asset_id and be unique
        self.assertIn(str(asset_id), path)
        self.assertTrue(path.endswith('.pdf'))
        self.assertNotEqual(path, f'documents/{asset_id}/test.pdf')  # Should be unique
    
    def test_validate_file(self):
        """Test file validation."""
        # Valid file
        valid_file = SimpleUploadedFile(
            "test.pdf",
            b"file content",
            content_type="application/pdf"
        )
        self.assertTrue(document_storage._validate_file(valid_file))
        
        # Invalid file type
        invalid_file = SimpleUploadedFile(
            "test.exe",
            b"file content",
            content_type="application/x-executable"
        )
        self.assertFalse(document_storage._validate_file(invalid_file))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class DocumentAPITest(APITestCase):
    """Test document API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.asset = Asset.objects.create(
            scope_type='address',
            city='Tel Aviv',
            street='Rothschild Blvd',
            number=1,
            created_by=self.user
        )
        self.client.force_authenticate(user=self.user)
    
    def test_upload_document(self):
        """Test document upload."""
        url = reverse('document_upload', kwargs={'asset_id': self.asset.id})
        
        # Create a test file
        test_file = SimpleUploadedFile(
            "test.pdf",
            b"file content",
            content_type="application/pdf"
        )
        
        data = {
            'file': test_file,
            'title': 'Test Document',
            'description': 'A test document',
            'document_type': 'permit'
        }
        
        response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Document.objects.count(), 1)
        
        document = Document.objects.first()
        self.assertEqual(document.title, 'Test Document')
        self.assertEqual(document.asset, self.asset)
        self.assertEqual(document.user, self.user)
    
    def test_list_documents(self):
        """Test listing documents for an asset."""
        # Create a test document
        Document.objects.create(
            asset=self.asset,
            user=self.user,
            title='Test Document',
            filename='test.pdf',
            file_path='/path/to/test.pdf',
            file_size=1024,
            mime_type='application/pdf'
        )
        
        url = reverse('asset_documents', kwargs={'asset_id': self.asset.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Document')
    
    def test_get_document_detail(self):
        """Test getting document details."""
        document = Document.objects.create(
            asset=self.asset,
            user=self.user,
            title='Test Document',
            filename='test.pdf',
            file_path='/path/to/test.pdf',
            file_size=1024,
            mime_type='application/pdf'
        )
        
        url = reverse('document_detail', kwargs={
            'asset_id': self.asset.id,
            'document_id': document.id
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Document')
    
    def test_update_document(self):
        """Test updating document metadata."""
        document = Document.objects.create(
            asset=self.asset,
            user=self.user,
            title='Test Document',
            filename='test.pdf',
            file_path='/path/to/test.pdf',
            file_size=1024,
            mime_type='application/pdf'
        )
        
        url = reverse('document_detail', kwargs={
            'asset_id': self.asset.id,
            'document_id': document.id
        })
        
        data = {
            'title': 'Updated Document',
            'description': 'Updated description'
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        document.refresh_from_db()
        self.assertEqual(document.title, 'Updated Document')
        self.assertEqual(document.description, 'Updated description')
    
    def test_delete_document(self):
        """Test deleting a document."""
        document = Document.objects.create(
            asset=self.asset,
            user=self.user,
            title='Test Document',
            filename='test.pdf',
            file_path='/path/to/test.pdf',
            file_size=1024,
            mime_type='application/pdf'
        )
        
        url = reverse('document_detail', kwargs={
            'asset_id': self.asset.id,
            'document_id': document.id
        })
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Document.objects.count(), 0)
    
    def test_permission_denied(self):
        """Test that users can only access their own documents."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_asset = Asset.objects.create(
            scope_type='address',
            city='Haifa',
            street='Herzl St',
            number=1,
            created_by=other_user
        )
        
        # Try to access other user's asset documents
        url = reverse('asset_documents', kwargs={'asset_id': other_asset.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_upload_validation(self):
        """Test file upload validation."""
        url = reverse('document_upload', kwargs={'asset_id': self.asset.id})
        
        # Test invalid file type
        invalid_file = SimpleUploadedFile(
            "test.exe",
            b"file content",
            content_type="application/x-executable"
        )
        
        data = {
            'file': invalid_file,
            'title': 'Test Document',
            'document_type': 'permit'
        }
        
        response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)


class DocumentSerializerTest(TestCase):
    """Test document serializers."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.asset = Asset.objects.create(
            scope_type='address',
            city='Tel Aviv',
            street='Rothschild Blvd',
            number=1,
            created_by=self.user
        )
    
    def test_document_serializer(self):
        """Test DocumentSerializer."""
        from core.serializers import DocumentSerializer
        
        document = Document.objects.create(
            asset=self.asset,
            user=self.user,
            title='Test Document',
            filename='test.pdf',
            file_path='/path/to/test.pdf',
            file_size=1024,
            mime_type='application/pdf'
        )
        
        serializer = DocumentSerializer(document)
        data = serializer.data
        
        self.assertEqual(data['title'], 'Test Document')
        self.assertEqual(data['filename'], 'test.pdf')
        self.assertEqual(data['file_size'], 1024)
        self.assertIn('file_url', data)
        self.assertIn('is_downloadable', data)
    
    def test_document_upload_serializer_validation(self):
        """Test DocumentUploadSerializer validation."""
        from core.serializers import DocumentUploadSerializer
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Valid data with file
        test_file = SimpleUploadedFile(
            "test.pdf",
            b"file content",
            content_type="application/pdf"
        )
        valid_data = {
            'file': test_file,
            'title': 'Test Document',
            'description': 'A test document',
            'document_type': 'permit',
            'document_date': '2024-01-01'
        }
        
        serializer = DocumentUploadSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Invalid document type
        invalid_data = {
            'file': test_file,
            'title': 'Test Document',
            'document_type': 'invalid_type'
        }
        
        serializer = DocumentUploadSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('document_type', serializer.errors)
