from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Asset, Permit, Plan, Document
from .serializers import PermitSerializer, PlanSerializer, DocumentSerializer
from .services.cost_service import CostService

import logging

logger = logging.getLogger(__name__)




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
    
    @extend_schema(
        summary="Get documents organized by Hebrew categories",
        description="Retrieve documents organized by Hebrew categories (שומות, היתרים, תוכניות, נסחים, תשריטים)",
        tags=["Documents"],
        parameters=[
            OpenApiParameter(
                name="asset_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Asset ID to filter documents",
                required=False,
            ),
        ],
    )
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get documents organized by Hebrew categories."""
        asset_id = request.query_params.get('asset_id')
        
        try:
            documents_by_category = Document.get_documents_by_category(asset_id)
            
            # Convert to serialized format
            result = {}
            for category, documents in documents_by_category.items():
                if documents:  # Only include categories with documents
                    serializer = self.get_serializer(documents, many=True)
                    result[category] = serializer.data
            
            return Response(result)
        except Exception as e:
            logger.error(f"Error getting documents by category: {e}")
            return Response(
                {'error': 'Failed to get documents by category'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Search documents",
        description="Search documents by title, description, external_id, or filename",
        tags=["Documents"],
        parameters=[
            OpenApiParameter(
                name="q",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search query",
                required=True,
            ),
            OpenApiParameter(
                name="asset_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Asset ID to filter documents",
                required=False,
            ),
            OpenApiParameter(
                name="category",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Hebrew category to filter by",
                required=False,
            ),
        ],
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search documents with optional filtering."""
        query = request.query_params.get('q', '')
        asset_id = request.query_params.get('asset_id')
        category = request.query_params.get('category')
        
        try:
            # Start with base queryset
            queryset = self.get_queryset()
            
            # Apply search
            if query:
                queryset = Document.search_documents(query, asset_id)
            elif asset_id:
                queryset = queryset.filter(asset_id=asset_id)
            
            # Apply category filter
            if category and category in Document.DOCUMENT_CATEGORIES:
                type_filter = Document.DOCUMENT_CATEGORIES[category]
                queryset = queryset.filter(document_type__in=type_filter)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'results': serializer.data,
                'count': queryset.count(),
                'query': query,
                'category': category
            })
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return Response(
                {'error': 'Failed to search documents'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
# Cost estimation API endpoints
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@extend_schema(
    summary="Estimate build cost",
    description="Estimate building construction costs using Dekel-style calculations",
    tags=["Cost Estimation"],
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "area_m2": {"type": "number", "description": "Building area in square meters"},
                "scope": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of construction scopes"
                },
                "region": {"type": "string", "description": "Region code (TA, CENTER, NORTH, SOUTH)"},
                "quality": {"type": "string", "description": "Quality level (basic, standard, premium)"}
            },
            "required": ["area_m2"]
        }
    },
    responses={
        200: {
            "description": "Cost estimate computed successfully",
            "content": {
                "application/json": {
                    "type": "object",
                    "properties": {
                        "breakdown": {"type": "object"},
                        "totals": {
                            "type": "object",
                            "properties": {
                                "base_cost": {"type": "number"},
                                "base_cost_with_vat": {"type": "number"},
                                "low_cost": {"type": "number"},
                                "low_cost_with_vat": {"type": "number"},
                                "high_cost": {"type": "number"},
                                "high_cost_with_vat": {"type": "number"}
                            }
                        },
                        "metadata": {"type": "object"}
                    }
                }
            }
        },
        400: {"description": "Invalid input data"}
    }
)
def estimate_build_cost(request):
    """Estimate building construction costs."""
    try:
        cost_service = CostService()
        estimate = cost_service.estimate_build_cost(request.data)
        return Response(estimate)
    except Exception as e:
        logger.error(f"Error estimating build cost: {e}")
        return Response({"error": "Failed to estimate build cost"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@extend_schema(
    summary="Get cost estimation options",
    description="Get available options for cost estimation (regions, qualities, scopes)",
    tags=["Cost Estimation"],
    responses={
        200: {
            "description": "Options retrieved successfully",
            "content": {
                "application/json": {
                    "type": "object",
                    "properties": {
                        "regions": {"type": "array"},
                        "qualities": {"type": "array"},
                        "scopes": {"type": "array"}
                    }
                }
            }
        }
    }
)
def get_cost_options(request):
    """Get available options for cost estimation."""
    try:
        cost_service = CostService()
        return Response({
            "regions": cost_service.get_available_regions(),
            "qualities": cost_service.get_available_qualities(),
            "scopes": cost_service.get_available_scopes()
        })
    except Exception as e:
        logger.error(f"Error getting cost options: {e}")
        return Response({"error": "Failed to get cost options"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
