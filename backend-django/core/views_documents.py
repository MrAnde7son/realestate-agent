import os
import logging
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django.conf import settings

from .models import Asset, Document
from .serializers import DocumentSerializer, DocumentUploadSerializer, DocumentListSerializer
from .storage import document_storage

logger = logging.getLogger(__name__)


class DocumentUploadView(APIView):
    """Handle document uploads for assets."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, asset_id):
        """Upload a document for an asset."""
        try:
            # Get asset
            asset = get_object_or_404(Asset, id=asset_id)
            
            # Check permissions (user owns asset or is admin)
            if not (asset.created_by == request.user or request.user.is_staff):
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Validate upload data
            serializer = DocumentUploadSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            file = serializer.validated_data['file']
            
            # Save file
            file_info, error = document_storage.save_document(file, asset_id, file.name)
            if error:
                return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create document record
            document = Document.objects.create(
                asset=asset,
                user=request.user,
                title=serializer.validated_data['title'],
                description=serializer.validated_data.get('description', ''),
                document_type=serializer.validated_data['document_type'],
                document_date=serializer.validated_data.get('document_date'),
                external_id=serializer.validated_data.get('external_id', ''),
                external_url=serializer.validated_data.get('external_url', ''),
                filename=file.name,
                file_path=file_info['file_path'],
                file_size=file_info['file_size'],
                mime_type=file_info['mime_type'],
                source='user_upload'
            )
            
            # Return document data
            response_serializer = DocumentSerializer(document)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            return Response(
                {'error': 'Upload failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentListView(APIView):
    """List documents for an asset."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, asset_id):
        """Get all documents for an asset."""
        try:
            # Get asset
            asset = get_object_or_404(Asset, id=asset_id)
            
            # Check permissions
            if not (asset.created_by == request.user or request.user.is_staff):
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get documents
            documents = asset.documents.all()
            serializer = DocumentListSerializer(documents, many=True)
            
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return Response(
                {'error': 'Failed to list documents'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentDetailView(APIView):
    """Handle individual document operations."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, asset_id, document_id):
        """Get document details."""
        try:
            # Get document
            document = get_object_or_404(Document, id=document_id, asset_id=asset_id)
            
            # Check permissions
            if not (document.asset.created_by == request.user or request.user.is_staff):
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = DocumentSerializer(document)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error getting document: {e}")
            return Response(
                {'error': 'Failed to get document'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, asset_id, document_id):
        """Update document metadata."""
        try:
            # Get document
            document = get_object_or_404(Document, id=document_id, asset_id=asset_id)
            
            # Check permissions
            if not (document.asset.created_by == request.user or request.user.is_staff):
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Update document
            serializer = DocumentSerializer(document, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return Response(
                {'error': 'Failed to update document'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, asset_id, document_id):
        """Delete document."""
        try:
            # Get document
            document = get_object_or_404(Document, id=document_id, asset_id=asset_id)
            
            # Check permissions
            if not (document.asset.created_by == request.user or request.user.is_staff):
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Delete file
            document.delete_file()
            
            # Delete document record
            document.delete()
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return Response(
                {'error': 'Failed to delete document'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentDownloadView(View):
    """Handle document downloads."""
    
    def get(self, request, asset_id, document_id):
        """Download a document file."""
        try:
            # Get document
            document = get_object_or_404(Document, id=document_id, asset_id=asset_id)
            
            # Check permissions
            if not request.user.is_authenticated:
                return HttpResponse('Authentication required', status=401)
            
            if not (document.asset.created_by == request.user or request.user.is_staff):
                return HttpResponse('Permission denied', status=403)
            
            # Check if file exists
            if not document.is_downloadable:
                raise Http404("File not found")
            
            # Get file content
            try:
                with default_storage.open(document.file_path, 'rb') as file:
                    response = HttpResponse(file.read(), content_type=document.mime_type)
                    response['Content-Disposition'] = f'attachment; filename="{document.filename}"'
                    return response
            except Exception as e:
                logger.error(f"Error reading file {document.file_path}: {e}")
                raise Http404("File not found")
                
        except Http404:
            raise
        except Exception as e:
            logger.error(f"Error downloading document: {e}")
            return HttpResponse('Download failed', status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_document_from_meta(request, asset_id):
    """Create Document records from meta field documents."""
    try:
        # Get asset
        asset = get_object_or_404(Asset, id=asset_id)
        
        # Check permissions
        if not (asset.created_by == request.user or request.user.is_staff):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get documents from meta
        if not asset.meta or 'documents' not in asset.meta:
            return Response({'message': 'No documents in meta field'})
        
        created_documents = []
        for doc_data in asset.meta['documents']:
            # Skip if already exists as Document record
            if Document.objects.filter(
                asset=asset, 
                external_id=doc_data.get('id')
            ).exists():
                continue
            
            # Create Document record
            document = Document.objects.create(
                asset=asset,
                user=request.user,
                title=doc_data.get('title', 'Untitled Document'),
                description=doc_data.get('description', ''),
                document_type=doc_data.get('type', 'other'),
                status=doc_data.get('status', 'pending'),
                external_id=doc_data.get('id'),
                external_url=doc_data.get('url'),
                source=doc_data.get('source', 'meta_migration'),
                document_date=doc_data.get('date'),
                filename=doc_data.get('filename', 'unknown'),
                file_path='',  # No file for meta documents
                file_size=0,
                mime_type='application/octet-stream'
            )
            
            created_documents.append(DocumentSerializer(document).data)
        
        return Response({
            'message': f'Created {len(created_documents)} documents',
            'documents': created_documents
        })
        
    except Exception as e:
        logger.error(f"Error creating documents from meta: {e}")
        return Response(
            {'error': 'Failed to create documents'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
