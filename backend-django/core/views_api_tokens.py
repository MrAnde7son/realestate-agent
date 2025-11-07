"""API Token management views."""

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from .models import APIToken

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_api_tokens(request):
    """List all API tokens for the current user."""
    try:
        tokens = APIToken.objects.filter(user=request.user).order_by("-created_at")
        tokens_data = []
        for token in tokens:
            tokens_data.append({
                "id": token.id,
                "name": token.name,
                "token": token.token if token.is_valid() else None,  # Only show token if valid
                "last_used_at": token.last_used_at.isoformat() if token.last_used_at else None,
                "expires_at": token.expires_at.isoformat() if token.expires_at else None,
                "is_active": token.is_active,
                "is_expired": token.is_expired(),
                "is_valid": token.is_valid(),
                "created_at": token.created_at.isoformat(),
            })
        return Response({"tokens": tokens_data})
    except Exception as e:
        logger.error("Error listing API tokens: %s", e)
        return Response({"error": "Failed to list tokens"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_api_token(request):
    """Create a new API token."""
    try:
        name = request.data.get("name", "Untitled Token")
        expires_in_days = request.data.get("expires_in_days")
        
        # Generate token
        token_value = APIToken.generate_token()
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = timezone.now() + timedelta(days=int(expires_in_days))
        
        # Create token
        api_token = APIToken.objects.create(
            user=request.user,
            name=name,
            token=token_value,
            expires_at=expires_at,
        )
        
        return Response({
            "success": True,
            "token": {
                "id": api_token.id,
                "name": api_token.name,
                "token": api_token.token,  # Only show token on creation
                "expires_at": api_token.expires_at.isoformat() if api_token.expires_at else None,
                "created_at": api_token.created_at.isoformat(),
            },
            "message": "Token created successfully. Save this token securely - it won't be shown again!"
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error("Error creating API token: %s", e)
        return Response({"error": "Failed to create token"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_api_token(request, token_id):
    """Delete an API token."""
    try:
        token = APIToken.objects.get(id=token_id, user=request.user)
        token.delete()
        return Response({"success": True, "message": "Token deleted successfully"})
    except APIToken.DoesNotExist:
        return Response({"error": "Token not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error("Error deleting API token: %s", e)
        return Response({"error": "Failed to delete token"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_api_token(request, token_id):
    """Update an API token (name, active status)."""
    try:
        token = APIToken.objects.get(id=token_id, user=request.user)
        
        if "name" in request.data:
            token.name = request.data["name"]
        if "is_active" in request.data:
            token.is_active = request.data["is_active"]
        
        token.save()
        
        return Response({
            "success": True,
            "token": {
                "id": token.id,
                "name": token.name,
                "is_active": token.is_active,
                "expires_at": token.expires_at.isoformat() if token.expires_at else None,
            }
        })
    except APIToken.DoesNotExist:
        return Response({"error": "Token not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error("Error updating API token: %s", e)
        return Response({"error": "Failed to update token"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

