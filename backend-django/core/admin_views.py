from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .serializers import (
    AdminUserSerializer,
    AdminUserCreateSerializer,
    AdminUserUpdateSerializer,
)

User = get_user_model()


class AdminUserPagination(PageNumberPagination):
    """Pagination for admin user management."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class IsAdminUser(permissions.BasePermission):
    """Custom permission to only allow admin users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )


@extend_schema_view(
    list=extend_schema(
        summary="List all users",
        description="Retrieve a paginated list of all users with filtering and search capabilities",
        tags=["Admin Users"],
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search by name, email, or username",
            ),
            OpenApiParameter(
                name="role",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by user role",
            ),
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by active status (active/inactive)",
            ),
            OpenApiParameter(
                name="created_after",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Filter users created after this date",
            ),
            OpenApiParameter(
                name="created_before",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Filter users created before this date",
            ),
        ],
    ),
    create=extend_schema(
        summary="Create a new user",
        description="Create a new user account",
        tags=["Admin Users"],
    ),
    retrieve=extend_schema(
        summary="Retrieve user details",
        description="Get detailed information about a specific user",
        tags=["Admin Users"],
    ),
    update=extend_schema(
        summary="Update user",
        description="Update user information",
        tags=["Admin Users"],
    ),
    partial_update=extend_schema(
        summary="Partially update user",
        description="Partially update user information",
        tags=["Admin Users"],
    ),
    destroy=extend_schema(
        summary="Delete user", description="Delete a user account", tags=["Admin Users"]
    ),
)
class AdminUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for admin user management.

    Provides CRUD operations for user management with filtering, search, and pagination.
    Only accessible by admin users.
    """

    queryset = User.objects.all().order_by("-created_at")
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]
    pagination_class = AdminUserPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["username", "email", "first_name", "last_name", "phone", "company"]
    ordering_fields = ["created_at", "last_login", "username", "email", "role"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return AdminUserCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return AdminUserUpdateSerializer
        return AdminUserSerializer

    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = User.objects.all()

        # Search filter
        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(phone__icontains=search)
                | Q(company__icontains=search)
            )

        # Role filter
        role = self.request.query_params.get("role", None)
        if role:
            queryset = queryset.filter(role=role)

        # Status filter
        status_filter = self.request.query_params.get("status", None)
        if status_filter == "active":
            queryset = queryset.filter(is_active=True)
        elif status_filter == "inactive":
            queryset = queryset.filter(is_active=False)

        # Date filters
        created_after = self.request.query_params.get("created_after", None)
        if created_after:
            try:
                date = datetime.strptime(created_after, "%Y-%m-%d").date()
                queryset = queryset.filter(created_at__date__gte=date)
            except ValueError:
                pass

        created_before = self.request.query_params.get("created_before", None)
        if created_before:
            try:
                date = datetime.strptime(created_before, "%Y-%m-%d").date()
                queryset = queryset.filter(created_at__date__lte=date)
            except ValueError:
                pass

        return queryset.order_by("-created_at")

    @extend_schema(
        summary="Deactivate user",
        description="Deactivate a user account (soft delete)",
        tags=["Admin Users"],
    )
    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """Deactivate a user account."""
        user = self.get_object()
        user.is_active = False
        user.save()

        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @extend_schema(
        summary="Activate user",
        description="Activate a user account",
        tags=["Admin Users"],
    )
    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Activate a user account."""
        user = self.get_object()
        user.is_active = True
        user.save()

        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @extend_schema(
        summary="Reset user password",
        description="Reset a user's password to a default value",
        tags=["Admin Users"],
    )
    @action(detail=True, methods=["post"])
    def reset_password(self, request, pk=None):
        """Reset user password to default."""
        user = self.get_object()
        default_password = "defaultpassword123"
        user.set_password(default_password)
        user.save()

        return Response(
            {"message": "Password reset successfully", "new_password": default_password}
        )

    @extend_schema(
        summary="Bulk actions",
        description="Perform bulk actions on multiple users",
        tags=["Admin Users"],
    )
    @action(detail=False, methods=["post"])
    def bulk_action(self, request):
        """Perform bulk actions on multiple users."""
        action_type = request.data.get("action")
        user_ids = request.data.get("user_ids", [])

        if not action_type or not user_ids:
            return Response(
                {"error": "Action type and user IDs are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        users = User.objects.filter(id__in=user_ids)

        if action_type == "activate":
            users.update(is_active=True)
            message = f"{users.count()} users activated"
        elif action_type == "deactivate":
            users.update(is_active=False)
            message = f"{users.count()} users deactivated"
        elif action_type == "delete":
            users.delete()
            message = f"{len(user_ids)} users deleted"
        else:
            return Response(
                {"error": "Invalid action type"}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response({"message": message})

    @extend_schema(
        summary="User statistics",
        description="Get user statistics and counts",
        tags=["Admin Users"],
    )
    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """Get user statistics."""
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = User.objects.filter(is_active=False).count()

        # Role counts
        role_counts = {}
        for role_choice in User.Role.choices:
            role_counts[role_choice[0]] = User.objects.filter(
                role=role_choice[0]
            ).count()

        # Recent registrations (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_registrations = User.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()

        # Users with recent login (last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_logins = User.objects.filter(last_login__gte=seven_days_ago).count()

        return Response(
            {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": inactive_users,
                "role_counts": role_counts,
                "recent_registrations": recent_registrations,
                "recent_logins": recent_logins,
            }
        )

    def destroy(self, request, *args, **kwargs):
        """Override destroy to prevent admin self-deletion."""
        user = self.get_object()

        # Prevent admin from deleting themselves
        if user == request.user:
            return Response(
                {"error": "You cannot delete your own account"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().destroy(request, *args, **kwargs)
