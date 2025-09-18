from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Asset, Permit, Plan, Document
from .serializers import AssetSerializer, PermitSerializer, PlanSerializer, DocumentSerializer

import logging

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="List all assets",
        description="Retrieve a list of all real estate assets",
        tags=["Assets"],
    ),
    create=extend_schema(
        summary="Create a new asset",
        description="Create a new real estate asset",
        tags=["Assets"],
    ),
    retrieve=extend_schema(
        summary="Retrieve an asset",
        description="Get details of a specific asset by ID",
        tags=["Assets"],
    ),
    update=extend_schema(
        summary="Update an asset",
        description="Update an existing asset",
        tags=["Assets"],
    ),
    partial_update=extend_schema(
        summary="Partially update an asset",
        description="Partially update an existing asset",
        tags=["Assets"],
    ),
    destroy=extend_schema(
        summary="Delete an asset",
        description="Delete an asset by ID",
        tags=["Assets"],
    ),
)
class AssetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing real estate assets.
    
    Provides CRUD operations for real estate assets including permits and plans.
    """
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        asset = serializer.save()
        logger.info("Asset created with id %s", asset.id)

    @extend_schema(
        summary="Get asset statistics",
        description="Get statistics about assets",
        tags=["Assets"],
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get asset statistics."""
        total_assets = self.get_queryset().count()
        return Response({
            'total_assets': total_assets,
            'active_assets': self.get_queryset().filter(is_active=True).count(),
        })


@extend_schema_view(
    list=extend_schema(
        summary="List all permits",
        description="Retrieve a list of all building permits",
        tags=["Permits"],
    ),
    create=extend_schema(
        summary="Create a new permit",
        description="Create a new building permit",
        tags=["Permits"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a permit",
        description="Get details of a specific permit by ID",
        tags=["Permits"],
    ),
    update=extend_schema(
        summary="Update a permit",
        description="Update an existing permit",
        tags=["Permits"],
    ),
    partial_update=extend_schema(
        summary="Partially update a permit",
        description="Partially update an existing permit",
        tags=["Permits"],
    ),
    destroy=extend_schema(
        summary="Delete a permit",
        description="Delete a permit by ID",
        tags=["Permits"],
    ),
)
class PermitViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing building permits.
    
    Provides CRUD operations for building permits and approvals.
    """
    queryset = Permit.objects.all()
    serializer_class = PermitSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema_view(
    list=extend_schema(
        summary="List all plans",
        description="Retrieve a list of all urban planning documents",
        tags=["Plans"],
    ),
    create=extend_schema(
        summary="Create a new plan",
        description="Create a new urban planning document",
        tags=["Plans"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a plan",
        description="Get details of a specific plan by ID",
        tags=["Plans"],
    ),
    update=extend_schema(
        summary="Update a plan",
        description="Update an existing plan",
        tags=["Plans"],
    ),
    partial_update=extend_schema(
        summary="Partially update a plan",
        description="Partially update an existing plan",
        tags=["Plans"],
    ),
    destroy=extend_schema(
        summary="Delete a plan",
        description="Delete a plan by ID",
        tags=["Plans"],
    ),
)
class PlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing urban planning documents.
    
    Provides CRUD operations for urban planning and development plans.
    """
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema_view(
    list=extend_schema(
        summary="List all documents",
        description="Retrieve a list of all documents",
        tags=["Documents"],
    ),
    create=extend_schema(
        summary="Create a new document",
        description="Create a new document record",
        tags=["Documents"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a document",
        description="Get details of a specific document by ID",
        tags=["Documents"],
    ),
    update=extend_schema(
        summary="Update a document",
        description="Update an existing document",
        tags=["Documents"],
    ),
    partial_update=extend_schema(
        summary="Partially update a document",
        description="Partially update an existing document",
        tags=["Documents"],
    ),
    destroy=extend_schema(
        summary="Delete a document",
        description="Delete a document",
        tags=["Documents"],
    ),
)
class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing documents.
    
    Provides CRUD operations for document files and metadata.
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter documents by user permissions."""
        if self.request.user.is_staff:
            return Document.objects.all()
        return Document.objects.filter(asset__created_by=self.request.user)
    
    @extend_schema(
        summary="Get documents by asset",
        description="Retrieve all documents for a specific asset",
        tags=["Documents"],
        parameters=[
            OpenApiParameter(
                name="asset_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Asset ID to filter documents",
                required=True,
            ),
        ],
    )
    @action(detail=False, methods=['get'])
    def by_asset(self, request):
        """Get documents for a specific asset."""
        asset_id = request.query_params.get('asset_id')
        if not asset_id:
            return Response(
                {'error': 'asset_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            documents = self.get_queryset().filter(asset_id=asset_id)
            serializer = self.get_serializer(documents, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting documents by asset: {e}")
            return Response(
                {'error': 'Failed to get documents'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
