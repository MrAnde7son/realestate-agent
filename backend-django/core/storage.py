import os
import uuid
from urllib.parse import urlparse

import mimetypes
import logging
from typing import Optional

import requests
from requests import RequestException

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone

logger = logging.getLogger(__name__)


class DocumentStorage:
    """Handles document file storage operations."""
    
    def __init__(self):
        self.base_path = getattr(settings, 'DOCUMENT_STORAGE_PATH', 'documents')
        self.max_file_size = getattr(settings, 'MAX_DOCUMENT_SIZE', 10 * 1024 * 1024)  # 10MB
        self.allowed_extensions = {
            '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.doc', '.docx', '.txt',
            '.xls', '.xlsx', '.csv', '.zip', '.rar', '.7z'
        }
    
    def get_upload_path(self, asset_id, filename):
        """Generate upload path for a document."""
        # Create a unique filename to avoid conflicts
        file_ext = os.path.splitext(filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        # Create directory structure: documents/asset_id/year/month/
        now = timezone.now()
        year = now.year
        month = now.month
        
        return os.path.join(
            self.base_path,
            str(asset_id),
            str(year),
            str(month),
            unique_filename
        )
    
    def save_document(self, file, asset_id, filename):
        """Save uploaded document file."""
        try:
            # Validate file
            if not self._validate_file(file):
                return None, "Invalid file"
            
            # Generate upload path
            upload_path = self.get_upload_path(asset_id, filename)
            
            # Ensure directory exists
            full_path = os.path.join(settings.MEDIA_ROOT, upload_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Save file
            with default_storage.open(upload_path, 'wb') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            # Get file info
            file_size = file.size
            mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            
            return {
                'file_path': upload_path,
                'file_size': file_size,
                'mime_type': mime_type
            }, None
            
        except Exception as e:
            logger.error(f"Error saving document: {e}")
            return None, str(e)

    def save_from_content(self, content: bytes, asset_id, filename, mime_type: Optional[str] = None):
        """Persist in-memory content as a stored document."""

        if not content:
            return None, "Empty content"

        content_file = ContentFile(content)
        content_file.name = filename
        content_file.size = len(content)

        saved, error = self.save_document(content_file, asset_id, filename)
        if saved and mime_type:
            saved['mime_type'] = mime_type
        return saved, error

    def save_from_url(
        self,
        url: str,
        asset_id,
        filename: Optional[str] = None,
        mime_type: Optional[str] = None,
        timeout: int = 30,
    ):
        """Download a remote document and persist it via the storage backend."""

        if not url:
            return None, "Missing URL"

        inferred_filename = filename or self._infer_filename_from_url(url, mime_type)

        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
        except RequestException as exc:
            logger.warning("Failed fetching document from %s: %s", url, exc)
            return None, str(exc)

        content_type = mime_type or response.headers.get('Content-Type')
        saved, error = self.save_from_content(
            response.content,
            asset_id,
            inferred_filename,
            mime_type=content_type,
        )

        return saved, error

    def _infer_filename_from_url(self, url: str, mime_type: Optional[str] = None) -> str:
        """Derive a sensible filename from a URL or MIME type."""

        parsed = urlparse(url)
        candidate = os.path.basename(parsed.path)
        if candidate and os.path.splitext(candidate)[1]:
            return candidate

        extension = mimetypes.guess_extension(mime_type or '') or '.bin'
        return f"document{extension}"
    
    def delete_document(self, file_path):
        """Delete document file."""
        try:
            if default_storage.exists(file_path):
                default_storage.delete(file_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting document {file_path}: {e}")
            return False
    
    def get_document_url(self, file_path):
        """Get URL for document file."""
        if default_storage.exists(file_path):
            return default_storage.url(file_path)
        return None
    
    def _validate_file(self, file):
        """Validate uploaded file."""
        # Check file size
        if file.size > self.max_file_size:
            return False
        
        # Check file extension
        file_ext = os.path.splitext(file.name)[1].lower()
        if file_ext not in self.allowed_extensions:
            return False
        
        return True
    
    def get_file_info(self, file_path):
        """Get file information."""
        try:
            if default_storage.exists(file_path):
                stat = default_storage.stat(file_path)
                return {
                    'size': stat.size,
                    'modified': stat.modified_time,
                    'exists': True
                }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
        
        return {'exists': False}


# Global instance
document_storage = DocumentStorage()
