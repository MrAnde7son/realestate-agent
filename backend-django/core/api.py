from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Asset, Permit, Plan, PlanningMetrics
from .serializers import AssetSerializer, PermitSerializer, PlanSerializer
from .services.planning_service import PlanningService
from .services.cost_service import CostService

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


# Planning API endpoints
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@extend_schema(
    summary="Compute planning metrics",
    description="Compute planning metrics for an asset including coverage, setbacks, and height analysis",
    tags=["Planning"],
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "parcel": {"type": "object", "description": "GeoJSON polygon of parcel"},
                "footprint": {"type": "object", "description": "GeoJSON polygon of building footprint"},
                "rules": {
                    "type": "object",
                    "properties": {
                        "setbacks": {"type": "object", "description": "Setback rules"},
                        "height": {"type": "object", "description": "Height rules"}
                    }
                },
                "current": {
                    "type": "object",
                    "properties": {
                        "floors": {"type": "integer", "description": "Current number of floors"},
                        "height_m": {"type": "number", "description": "Current height in meters"}
                    }
                }
            }
        }
    },
    responses={
        200: {
            "description": "Planning metrics computed successfully",
            "content": {
                "application/json": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "parcel_area_m2": {"type": "number"},
                        "footprint_area_m2": {"type": "number"},
                        "coverage_pct": {"type": "number"},
                        "setback_violations": {"type": "array"},
                        "height_current": {"type": "object"},
                        "height_allowed": {"type": "object"},
                        "height_delta": {"type": "object"},
                        "calc_confidence": {"type": "string"}
                    }
                }
            }
        },
        404: {"description": "Asset not found"},
        400: {"description": "Invalid input data"}
    }
)
def compute_planning_metrics(request, asset_id):
    """Compute planning metrics for an asset."""
    try:
        asset = Asset.objects.get(id=asset_id)
    except Asset.DoesNotExist:
        return Response({"error": "Asset not found"}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        planning_service = PlanningService()
        planning_metrics = planning_service.compute_planning_metrics(asset, request.data)
        
        return Response({
            "id": planning_metrics.id,
            "parcel_area_m2": planning_metrics.parcel_area_m2,
            "footprint_area_m2": planning_metrics.footprint_area_m2,
            "coverage_pct": planning_metrics.coverage_pct,
            "allowed_envelope_polygon": planning_metrics.allowed_envelope_polygon,
            "setback_violations": planning_metrics.setback_violations,
            "height_current": planning_metrics.height_current,
            "height_allowed": planning_metrics.height_allowed,
            "height_delta": planning_metrics.height_delta,
            "calc_confidence": planning_metrics.calc_confidence,
            "updated_at": planning_metrics.updated_at
        })
    except Exception as e:
        logger.error(f"Error computing planning metrics for asset {asset_id}: {e}")
        return Response({"error": "Failed to compute planning metrics"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@extend_schema(
    summary="Get planning metrics",
    description="Retrieve planning metrics for an asset",
    tags=["Planning"],
    responses={
        200: {
            "description": "Planning metrics retrieved successfully",
            "content": {
                "application/json": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "parcel_area_m2": {"type": "number"},
                        "footprint_area_m2": {"type": "number"},
                        "coverage_pct": {"type": "number"},
                        "setback_violations": {"type": "array"},
                        "height_current": {"type": "object"},
                        "height_allowed": {"type": "object"},
                        "height_delta": {"type": "object"},
                        "calc_confidence": {"type": "string"}
                    }
                }
            }
        },
        404: {"description": "Asset or planning metrics not found"}
    }
)
def get_planning_metrics(request, asset_id):
    """Get planning metrics for an asset."""
    try:
        asset = Asset.objects.get(id=asset_id)
        planning_metrics = asset.planning_metrics
    except Asset.DoesNotExist:
        return Response({"error": "Asset not found"}, status=status.HTTP_404_NOT_FOUND)
    except PlanningMetrics.DoesNotExist:
        return Response({"error": "Planning metrics not found"}, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        "id": planning_metrics.id,
        "parcel_area_m2": planning_metrics.parcel_area_m2,
        "footprint_area_m2": planning_metrics.footprint_area_m2,
        "coverage_pct": planning_metrics.coverage_pct,
        "allowed_envelope_polygon": planning_metrics.allowed_envelope_polygon,
        "setback_violations": planning_metrics.setback_violations,
        "height_current": planning_metrics.height_current,
        "height_allowed": planning_metrics.height_allowed,
        "height_delta": planning_metrics.height_delta,
        "calc_confidence": planning_metrics.calc_confidence,
        "updated_at": planning_metrics.updated_at
    })


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
