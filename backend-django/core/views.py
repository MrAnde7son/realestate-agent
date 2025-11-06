# -*- coding: utf-8 -*-
import json
import statistics
import re
import os
import secrets
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
from typing import Optional, Any
from pathlib import Path

from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, render
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import (
    Q,
    Avg,
    Min,
    Max,
    Case,
    When,
    Value,
    FloatField,
    ExpressionWrapper,
    F,
    CharField,
    Count,
    Exists,
    OuterRef,
)
from datetime import datetime
from asgiref.sync import async_to_sync
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
try:
    from rest_framework_simplejwt.token_blacklist.models import (
        BlacklistedToken,
        OutstandingToken,
    )
except ImportError:  # pragma: no cover - blacklist app not installed
    BlacklistedToken = None
    OutstandingToken = None
from drf_spectacular.utils import extend_schema

import logging

# Import Django models
from .models import (
    AlertRule,
    AlertEvent,
    Asset,
    AssetListing,
    SourceRecord,
    RealEstateTransaction,
    OnboardingProgress,
    ShareToken,
    AssetContribution,
    UserProfile,
    Snapshot,
    Document,
    Plan,
    AssetWatchlistEntry,
)

from .listing_builder import build_listing
from .serializers import (
    AlertRuleSerializer,
    AlertEventSerializer,
    AssetContributionSerializer,
    AssetSerializer,
    UserProfileSerializer,
    PlanTypeSerializer,
    UserPlanSerializer,
    UserPlanInfoSerializer, DocumentSerializer,
)
from .llm.select import get_llm
from .llm.types import BaseGenOptions, ChatMessage

# Import agent
RealEstateAgent = None
_agent_import_error = None

try:
    # Try importing as a package from the Django project root
    from agent.real_estate_agent import RealEstateAgent
except ImportError as e:
    _agent_import_error = str(e)
    # Try alternative import path - direct file import
    try:
        import sys
        import os
        # Get the backend-django directory
        backend_django_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        if backend_django_path not in sys.path:
            sys.path.insert(0, backend_django_path)
        from agent.real_estate_agent import RealEstateAgent
        _agent_import_error = None
    except ImportError as e2:
        _agent_import_error = f"{str(e)}; {str(e2)}"
        # Last resort: try importing the file directly
        try:
            import importlib.util
            agent_file = os.path.join(os.path.dirname(__file__), "..", "agent", "real_estate_agent.py")
            spec = importlib.util.spec_from_file_location("real_estate_agent", agent_file)
            if spec and spec.loader:
                agent_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(agent_module)
                RealEstateAgent = getattr(agent_module, "RealEstateAgent", None)
                if RealEstateAgent:
                    _agent_import_error = None
        except Exception as e3:
            _agent_import_error = f"{_agent_import_error}; {str(e3)}"

# Tenacity retry errors
try:
    from tenacity import RetryError
except ImportError:
    RetryError = None

try:
    from utils.parse_tabu import TabuParser
except ImportError:
    TabuParser = None


# Import tasks
from .tasks import run_data_pipeline
from .analytics import track, track_search, track_feature_usage
from .services.asset_links import (
    asset_transactions_all,
    asset_listings_all,
)
from .utils.listings import (
    format_rooms_value,
    normalize_listing_from_meta,
    normalize_listing_from_model,
    parse_date_value,
    parse_float,
    parse_int,
)

User = get_user_model()

User = get_user_model()

# Import services
from .auth_service import AuthenticationService
from .report_service import ReportService
from .constants import DEFAULT_REPORT_SECTIONS

BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize services
auth_service = AuthenticationService(settings)
report_service = ReportService(BASE_DIR)

logger = logging.getLogger(__name__)


# Rate limiting for asset creation to avoid abuse
ASSETS_POST_LIMIT = 5  # max POST requests per window
ASSETS_POST_WINDOW = 60  # window size in seconds
DEFAULT_ASSET_PAGE_SIZE = 25
MAX_ASSET_PAGE_SIZE = 100
_assets_rate_limit = {}

def _update_onboarding(user, step):
    logger.debug("_update_onboarding called - User: %s, Step: %s, Authenticated: %s", 
                 user, step, getattr(user, 'is_authenticated', False) if user else 'No user')
    if not user or not user.is_authenticated:
        logger.debug("Skipping onboarding update - No authenticated user")
        return
    progress, _ = OnboardingProgress.objects.get_or_create(user=user)
    if not getattr(progress, step):
        setattr(progress, step, True)
        progress.save()
        logger.info("Updated onboarding step %s to True for user %s", step, user.id)
    else:
        logger.debug("Onboarding step %s already True for user %s", step, user.id)


# Authentication views
@extend_schema(
    summary="User login",
    description="Authenticate user with email and password",
    tags=["Authentication"],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'},
                'password': {'type': 'string'},
            },
            'required': ['email', 'password']
        }
    },
    responses={
        200: {
            'description': 'Login successful',
            'examples': {
                'application/json': {
                    'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                    'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                    'user': {
                        'id': 1,
                        'email': 'user@example.com',
                        'username': 'user',
                        'role': 'broker'
                    }
                }
            }
        },
        400: {'description': 'Invalid credentials'},
        401: {'description': 'Authentication failed'}
    }
)
@api_view(["POST"])
@permission_classes([AllowAny])
def auth_login(request):
    """User login endpoint."""
    try:
        data = json.loads(request.body.decode("utf-8"))
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Use authentication service
        logger.info("Login attempt for %s", email)
        result = auth_service.authenticate_user(email, password)
        if result["success"]:
            try:
                user = get_user_model().objects.get(email=email)
            except Exception:
                user = None
            track("user_login", user=user)
            logger.info("Login succeeded for %s", email)
        else:
            logger.warning("Login failed for %s: %s", email, result.get("error"))
        return Response(
            result["data"] if result["success"] else {"error": result["error"]},
            status=result["status"],
        )

    except json.JSONDecodeError:
        return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Unexpected error during login for %s", locals().get("email"))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="User registration",
    description="Register a new user account",
    tags=["Authentication"],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'},
                'password': {'type': 'string', 'minLength': 8},
                'first_name': {'type': 'string'},
                'last_name': {'type': 'string'},
                'equity': {'type': 'number', 'minimum': 0},
            },
            'required': ['email', 'password']
        }
    },
    responses={
        201: {'description': 'User created successfully'},
        400: {'description': 'Invalid input data'},
        409: {'description': 'User already exists'}
    }
)
@api_view(["POST"])
@permission_classes([AllowAny])
def auth_register(request):
    """User registration endpoint."""
    try:
        data = json.loads(request.body.decode("utf-8"))
        email = data.get("email")
        logger.info("Registration attempt for %s", email)

        # Use authentication service
        result = auth_service.register_user(data)
        if result["success"]:
            try:
                user = get_user_model().objects.get(email=email)
            except Exception:
                user = None
            track("user_signup", user=user)
            logger.info("Registration succeeded for %s", email)
        else:
            logger.warning("Registration failed for %s: %s", email, result.get("error"))
        return Response(
            result["data"] if result["success"] else {"error": result["error"]},
            status=result["status"],
        )

    except json.JSONDecodeError:
        return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Unexpected error during registration for %s", locals().get("email"))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def auth_logout(request):
    """User logout endpoint."""
    try:
        refresh_token = None
        if isinstance(request.data, dict):
            refresh_token = (
                request.data.get("refresh_token")
                or request.data.get("refresh")
            )

        if not refresh_token:
            refresh_token = request.COOKIES.get("refresh_token")

        tokens_revoked = 0

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                if hasattr(token, "blacklist"):
                    token.blacklist()
                    tokens_revoked += 1
                else:  # pragma: no cover - safety net when blacklist app missing
                    raise AttributeError("Token blacklisting not configured")
            except TokenError:
                return Response(
                    {"error": "Invalid refresh token"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # As a fallback (or when no refresh token provided) blacklist all tokens
        if BlacklistedToken and OutstandingToken:
            outstanding_tokens = OutstandingToken.objects.filter(user=request.user)
            for outstanding in outstanding_tokens:
                _, created = BlacklistedToken.objects.get_or_create(token=outstanding)
                if created:
                    tokens_revoked += 1

        logger.info(
            "User %s logged out. Revoked %s tokens.",
            request.user.pk,
            tokens_revoked,
        )

        return Response({"message": "Logged out successfully"})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def auth_profile(request):
    """Get current user profile."""
    try:
        user = request.user
        
        # Get onboarding progress
        onboarding_progress, _ = OnboardingProgress.objects.get_or_create(user=user)
        
        response_data = {
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "company": getattr(user, "company", ""),
                "role": getattr(user, "role", ""),
                "equity": float(user.equity) if getattr(user, "equity", None) is not None else None,
                "is_verified": getattr(user, "is_verified", False),
                "created_at": (
                    user.created_at.isoformat()
                    if hasattr(user, "created_at")
                    else None
                ),
                "language": getattr(user, "language", ""),
                "timezone": getattr(user, "timezone", ""),
                "currency": getattr(user, "currency", ""),
                "date_format": getattr(user, "date_format", ""),
                "notify_email": getattr(user, "notify_email", False),
                "notify_whatsapp": getattr(user, "notify_whatsapp", False),
                "notify_urgent": getattr(user, "notify_urgent", False),
                "notification_time": getattr(user, "notification_time", ""),
                "onboarding_flags": {
                    "connect_payment": onboarding_progress.connect_payment,
                    "add_first_asset": onboarding_progress.add_first_asset,
                    "generate_first_report": onboarding_progress.generate_first_report,
                    "set_one_alert": onboarding_progress.set_one_alert,
                }
            }
        }
        
        
        return Response(response_data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def auth_update_profile(request):
    """Update current user profile."""
    try:
        data = json.loads(request.body.decode("utf-8"))
        user = request.user

        # Update allowed fields
        if "first_name" in data:
            user.first_name = data["first_name"]
        if "last_name" in data:
            user.last_name = data["last_name"]
        if "company" in data:
            user.company = data["company"]
        if "equity" in data:
            equity_value = data["equity"]
            if equity_value in (None, ""):
                user.equity = None
            else:
                try:
                    equity_decimal = Decimal(str(equity_value))
                except (InvalidOperation, TypeError):
                    return Response(
                        {"error": "Equity must be a valid number"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if equity_decimal < 0:
                    return Response(
                        {"error": "Equity must be a non-negative amount"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                user.equity = equity_decimal
        # Role changes are not allowed for regular users - only admins can change roles
        # if "role" in data:
        #     user.role = data["role"]

        user.save()

        # Get onboarding progress
        onboarding_progress, _ = OnboardingProgress.objects.get_or_create(user=user)
        
        return Response(
            {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "company": getattr(user, "company", ""),
                    "role": getattr(user, "role", ""),
                    "equity": float(user.equity) if getattr(user, "equity", None) is not None else None,
                    "is_verified": getattr(user, "is_verified", False),
                    "onboarding_flags": {
                        "connect_payment": onboarding_progress.connect_payment,
                        "add_first_asset": onboarding_progress.add_first_asset,
                        "generate_first_report": onboarding_progress.generate_first_report,
                        "set_one_alert": onboarding_progress.set_one_alert,
                    }
                }
            }
        )

    except json.JSONDecodeError:
        return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([AllowAny])
def auth_refresh(request):
    """Refresh JWT token."""
    try:
        data = json.loads(request.body.decode("utf-8"))
        refresh_token = data.get("refresh_token")

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify and refresh token
        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)

        return Response(
            {
                "access_token": access_token,
                "refresh_token": str(refresh),
            }
        )

    except json.JSONDecodeError:
        return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(["GET"])
@permission_classes([AllowAny])
def auth_google_login(request):
    """Initiate Google OAuth login flow using the auth service."""
    try:
        result = auth_service.get_google_auth_url(request)
        return Response(
            result["data"] if result["success"] else {"error": result["error"]},
            status=result["status"],
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([AllowAny])
def auth_google_callback(request):
    """Handle Google OAuth callback via the auth service."""
    try:
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        result = auth_service.handle_google_callback(request, frontend_url)
        if result["success"]:
            return redirect(result["data"]["redirect_url"])
        response_data = {"error": result["error"]}
        response_data.update(result.get("data", {}))
        return Response(
            response_data,
            status=result["status"],
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def me(request):
    u = request.user
    if not u.is_authenticated:
        return Response({"authenticated": False}, status=401)
    return Response(
        {
            "authenticated": True,
            "email": u.email,
            "role": getattr(u, "role", "private"),
        }
    )


# Demo mode


@api_view(["POST"])
@permission_classes([AllowAny])
def demo_start(request):
    """Create a demo user and seed sample assets."""
    User = get_user_model()
    username = "demo_{}".format(get_random_string(8))
    email = "{}@demo.local".format(username)
    password = get_random_string(12)
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name="Demo",
        last_name="User",
        role=User.Role.BROKER,
        is_demo=True,
    )

    sample_assets = [
        {
            "scope_type": "address",
            "city": "Tel Aviv",
            "street": "Herzl",
            "number": 1,
            "price": 1500000,
            "rooms": 3,
        },
        {
            "scope_type": "address",
            "city": "Jerusalem",
            "street": "King George",
            "number": 5,
            "price": 2000000,
            "rooms": 4,
        },
        {
            "scope_type": "address",
            "city": "Haifa",
            "street": "HaNassi",
            "number": 20,
            "price": 1200000,
            "rooms": 2,
        },
    ]

    for data in sample_assets:
        asset_data = data.copy()
        asset_data.update({
            "status": "done",
            "is_demo": True,
            "meta": {"demo": True},
        })
        Asset.objects.create(**asset_data)

    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(user)
    return Response(
        {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user": auth_service._get_user_data(user),
        }
    )


# Font setup is now handled by the HebrewPDFGenerator class


def parse_json(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return None


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def user_settings(request):
    """Retrieve or update user settings."""
    user = request.user
    if request.method == "GET":
        return Response(
            {
                "language": getattr(user, "language", ""),
                "timezone": getattr(user, "timezone", ""),
                "currency": getattr(user, "currency", ""),
                "date_format": getattr(user, "date_format", ""),
                "notify_email": getattr(user, "notify_email", False),
                "notify_whatsapp": getattr(user, "notify_whatsapp", False),
                "notify_urgent": getattr(user, "notify_urgent", False),
                "notification_time": getattr(user, "notification_time", ""),
                "report_sections": getattr(user, "report_sections", [])
                or DEFAULT_REPORT_SECTIONS,
            }
        )

    if request.method == "PUT":
        data = parse_json(request)
        if not data:
            return Response(
                {"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST
            )

        for field in [
            "language",
            "timezone",
            "currency",
            "date_format",
            "notify_email",
            "notify_whatsapp",
            "notify_urgent",
            "notification_time",
            "report_sections",
        ]:
            if field in data:
                setattr(user, field, data[field])
        user.save()

        return Response(
            {
                "language": user.language,
                "timezone": user.timezone,
                "currency": user.currency,
                "date_format": user.date_format,
                "notify_email": user.notify_email,
                "notify_whatsapp": user.notify_whatsapp,
                "notify_urgent": user.notify_urgent,
                "notification_time": user.notification_time,
                "report_sections": user.report_sections,
            }
        )

    return Response(
        {"error": "Unsupported method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@api_view(["GET", "POST", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def alerts(request):
    if request.method == "POST":
        data = parse_json(request)
        if not data:
            return Response(
                {"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AlertRuleSerializer(data=data)
        if serializer.is_valid():
            # Save with user from request - pass user object to save method
            alert_rule = serializer.save(user=request.user)
            
            # Track analytics event for alert rule creation
            track("alert_rule_create", user=request.user, asset_id=alert_rule.asset_id if alert_rule.asset else None)
            
            _update_onboarding(request.user, "set_one_alert")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "GET":
        # Only return alert rules for the current user
        rules = AlertRule.objects.filter(user=request.user).order_by("-created_at")
        serializer = AlertRuleSerializer(rules, many=True)
        
        # Track feature usage
        track_feature_usage("alert_rules_view", user=request.user)
        
        return Response({"rules": serializer.data})

    if request.method == "PUT":
        rule_id = request.GET.get('id')
        if not rule_id:
            return Response({"error": "Alert rule ID required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            rule = AlertRule.objects.get(id=rule_id, user=request.user)
        except AlertRule.DoesNotExist:
            return Response({"error": "Alert rule not found"}, status=status.HTTP_404_NOT_FOUND)
        
        data = parse_json(request)
        if not data:
            return Response(
                {"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = AlertRuleSerializer(rule, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "DELETE":
        rule_id = request.GET.get('ruleId')
        if not rule_id:
            return Response({"error": "Alert rule ID required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            rule = AlertRule.objects.get(id=rule_id, user=request.user)
            rule.delete()
            return Response({"message": "Alert rule deleted successfully"}, status=status.HTTP_200_OK)
        except AlertRule.DoesNotExist:
            return Response({"error": "Alert rule not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response(
        {"error": "Unsupported method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def onboarding_status(request):
    progress, _ = OnboardingProgress.objects.get_or_create(user=request.user)
    return Response(
        {
            "steps": {
                "connect_payment": progress.connect_payment,
                "add_first_asset": progress.add_first_asset,
                "generate_first_report": progress.generate_first_report,
                "set_one_alert": progress.set_one_alert,
            },
            "completed": progress.is_complete(),
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def connect_payment(request):
    _update_onboarding(getattr(request, "user", None), "connect_payment")
    return Response({"status": "ok"})


@csrf_exempt
def sync_address(request):
    """Fetch external data for a given address and store it.

    Expected JSON payload:
    - street: str - Street name in Hebrew
    - house_number: int - House number
    OR
    - address: str - Full address string to parse

    Returns:
    - 200: {"rows": [...]} - List of found assets
    - 400: Error message for invalid input
    - 500: Error message for server errors
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    # Parse JSON with error handling
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON in request body"}, status=400)

    # Extract street and number from data
    street = data.get("street", "").strip() if data.get("street") else None
    number = data.get("house_number")

    # If no direct street/number, try to parse from address field
    if not street or number is None:
        addr = (data.get("address") or "").strip()
        if not addr:
            return JsonResponse(
                {"error": "Either (street, house_number) or address is required"},
                status=400,
            )

        match = re.match(r"^(.+?)\s+(\d+)", addr)
        if match:
            street, number = match.group(1).strip(), match.group(2)
        else:
            return JsonResponse(
                {
                    "error": 'Could not parse address. Expected format: "Street Name Number"'
                },
                status=400,
            )

    # Validate and convert number
    if not street:
        return JsonResponse({"error": "Street name is required"}, status=400)

    try:
        number = int(number)
        if number <= 0:
            return JsonResponse(
                {"error": "House number must be a positive integer"}, status=400
            )
    except (TypeError, ValueError):
        return JsonResponse(
            {"error": "House number must be a valid integer"}, status=400
        )

    # Execute sync with comprehensive error handling
    try:
        # Check for existing asset using deduplication service
        from .models import Asset
        from .services.asset_deduplication import find_existing_asset
        from orchestration.location import LocationQuery
        
        # Try to find existing asset (city may not be available in this endpoint)
        location = LocationQuery(
            city="",
            street=street,
            house_number=number,
        )
        existing_asset = find_existing_asset(
            location=location,
            scope_type="address",
        )
        
        if existing_asset:
            # Update existing asset instead of creating duplicate
            asset = existing_asset
            asset.status = "pending"  # Reset status to trigger re-enrichment
            if not asset.meta:
                asset.meta = {}
            asset.meta.update({"radius": 150})
            asset.save()
            logger.info("Found existing asset %s in sync_address, updating instead of creating duplicate", asset.id)
        else:
            # Create a new asset for the address
            asset = Asset.objects.create(
                scope_type="address",
                street=street,
                number=number,
                status="pending",
                meta={"radius": 150},
            )

        # Start enrichment pipeline
        try:
            # Check if Celery is enabled
            from django.conf import settings
            if hasattr(settings, 'CELERY_BROKER_URL') and settings.CELERY_BROKER_URL:
                run_data_pipeline.delay(asset.id)
                message = (
                    "Asset enrichment started for {} {} (Asset ID: {})".format(street, number, asset.id)
                )
            else:
                # Run asynchronously in background thread when Celery is disabled
                import threading
                
                def run_pipeline_async():
                    try:
                        run_data_pipeline(asset.id)
                        logger.info("Background data pipeline completed for asset %s", asset.id)
                    except Exception as e:
                        logger.error("Background data pipeline failed for asset %s: %s", asset.id, e)
                        # Update asset status to error
                        try:
                            asset_obj = Asset.objects.get(id=asset.id)
                            asset_obj.status = "failed"
                            asset_obj.last_enrich_error = str(e)
                            asset_obj.save()
                        except Exception as save_error:
                            logger.error("Failed to update asset status: %s", save_error)
                
                thread = threading.Thread(target=run_pipeline_async, daemon=True)
                thread.start()
                message = (
                    "Asset enrichment started for {} {} (Asset ID: {})".format(street, number, asset.id)
                )
        except Exception as e:
            message = "Asset created but enrichment failed: {}".format(str(e))

        # Return asset info
        assets = [
            {
                "id": asset.id,
                "source": "asset",
                "external_id": "asset_{}".format(asset.id),
                "title": "Asset for {} {}".format(street, number),
                "address": "{} {}".format(street, number),
                "status": asset.status,
                "message": message,
            }
        ]

        return JsonResponse(
            {"rows": assets, "message": message, "address": "{} {}".format(street, number)}
        )
    except ValueError as e:
        return JsonResponse({"error": "Validation error: {}".format(str(e))}, status=400)
    except Exception as e:
        # Log the full error for debugging
        import logging

        logging.exception("Unexpected error in sync_address: %s", e)
        return JsonResponse(
            {"error": "Internal server error occurred during address sync"}, status=500
        )


# Old view functions removed - replaced with new asset enrichment pipeline


@api_view(["GET", "POST", "DELETE"])
@permission_classes([AllowAny])  # Allow both authenticated and unauthenticated access
def reports(request):
    """Create a PDF report for a listing or list existing reports."""
    if request.method == "GET":
        # Get all reports using service
        reports_list = report_service.get_reports_list()
        return Response({"reports": reports_list})

    if request.method == "DELETE":
        # Delete a specific report using service
        data = parse_json(request)
        if not data or not data.get("reportId"):
            return Response({"error": "reportId required"}, status=400)

        try:
            report_id = int(data["reportId"])
            success = report_service.delete_report(report_id)

            if success:
                return Response(
                    {"message": "Report {} deleted successfully".format(report_id)}, status=200
                )
            else:
                return Response({"error": "Failed to delete report"}, status=500)

        except ValueError:
            return Response({"error": "Invalid report ID"}, status=400)
        except Exception as e:
            return Response(
                {"error": "Error deleting report", "details": str(e)}, status=500
            )

    if request.method != "POST":
        return Response({"error": "POST or DELETE required"}, status=405)

    data = parse_json(request)
    if not data or not data.get("assetId"):
        return Response({"error": "assetId required"}, status=400)

    asset_id = data["assetId"]
    sections = data.get("sections")
    if sections is None:
        sections = DEFAULT_REPORT_SECTIONS
    elif not sections:
        return Response({"error": "sections required"}, status=400)

    logger.info("Report generation requested for asset %s", asset_id)
    track("report_request", user=getattr(request, "user", None), asset_id=asset_id)
    try:
        # Create report using service
        report = report_service.create_report(asset_id, sections)

        if not report:
            logger.error("Failed to create report for asset %s", asset_id)
            return Response({"error": "Failed to create report"}, status=500)

        # Generate PDF using service
        success = report_service.generate_pdf(report)

        if not success:
            logger.error("PDF generation failed for report %s", report.id)
            return Response({"error": "PDF generation failed"}, status=500)

        _update_onboarding(getattr(request, "user", None), "generate_first_report")
        track("report_success", user=getattr(request, "user", None), asset_id=asset_id)
        
        # Track feature usage
        track_feature_usage("report_generation", user=getattr(request, "user", None), asset_id=asset_id)
        logger.info("Report %s successfully generated for asset %s", report.id, asset_id)

        # Return success response
        return Response(
            {
                "report": {
                    "id": report.id,
                    "assetId": asset_id,
                    "address": report.title,
                    "filename": report.filename,
                    "createdAt": report.generated_at.isoformat(),
                    "status": report.status,
                    "pages": report.pages,
                    "fileSize": report.file_size,
                    "sections": report.sections,
                    "url": report.file_url,
                }
            },
            status=201,
        )

    except Exception as e:
        track(
            "report_fail",
            user=getattr(request, "user", None),
            asset_id=asset_id,
            error_code=str(e),
        )
        logger.exception("Report generation failed for asset %s", asset_id)
        return Response(
            {"error": "Report generation failed", "details": str(e)}, status=500
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def assets_bulk_action(request):
    """Perform bulk actions on multiple assets."""

    data = parse_json(request)
    if not data:
        return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)

    action = data.get("action")
    asset_ids = data.get("assetIds") or data.get("asset_ids")

    if not action or not isinstance(asset_ids, list) or not asset_ids:
        return Response(
            {"error": "action and assetIds are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        requested_ids = [int(asset_id) for asset_id in asset_ids]
    except (TypeError, ValueError):
        return Response({"error": "assetIds must be integers"}, status=400)

    assets_map = {
        asset.id: asset
        for asset in Asset.objects.filter(id__in=requested_ids).select_related("created_by")
    }

    if not assets_map:
        return Response(
            {"error": "No assets found for provided IDs"},
            status=status.HTTP_404_NOT_FOUND,
        )

    user = request.user

    results: list[dict[str, Any]] = []
    success_count = 0
    not_found_count = 0

    if action == "delete":
        if not (
            getattr(user, "role", None) == User.Role.ADMIN
            or getattr(user, "is_superuser", False)
        ):
            return Response(
                {"error": "Admin privileges required to delete assets"},
                status=status.HTTP_403_FORBIDDEN,
            )

        for asset_id in requested_ids:
            asset = assets_map.get(asset_id)
            if not asset:
                not_found_count += 1
                results.append({"assetId": asset_id, "status": "not_found"})
                continue

            try:
                deleted = asset.delete_asset()
                if deleted:
                    success_count += 1
                    results.append({"assetId": asset_id, "status": "success"})
                else:
                    results.append(
                        {
                            "assetId": asset_id,
                            "status": "failed",
                            "error": "Failed to delete asset",
                        }
                    )
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.exception("Error deleting asset %s: %s", asset_id, exc)
                results.append(
                    {
                        "assetId": asset_id,
                        "status": "failed",
                        "error": str(exc),
                    }
                )

        message = f"Deleted {success_count} of {len(requested_ids)} assets"

    elif action == "sync":
        from django.conf import settings

        celery_enabled = bool(getattr(settings, "CELERY_BROKER_URL", None))

        try:
            from .tasks import run_data_pipeline
        except Exception as exc:  # pragma: no cover - import safety
            logger.exception("Failed to import run_data_pipeline: %s", exc)
            return Response(
                {"error": "Sync is not available"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        for asset_id in requested_ids:
            asset = assets_map.get(asset_id)
            if not asset:
                not_found_count += 1
                results.append({"assetId": asset_id, "status": "not_found"})
                continue

            try:
                address = asset.address
                if not address:
                    raise ValueError("Asset is missing address information")

                asset.status = "syncing"
                asset.last_sync_started_at = timezone.now()
                asset.save(update_fields=["status", "last_sync_started_at"])

                job_id = None
                if celery_enabled:
                    result = run_data_pipeline.delay(asset.id)
                    job_id = getattr(result, "id", None)
                else:
                    import threading

                    def run_sync_async(asset_pk: int) -> None:
                        try:
                            run_data_pipeline(asset_pk)
                            logger.info(
                                "Background asset sync completed for asset %s", asset_pk
                            )
                        except Exception as err:  # pragma: no cover - defensive
                            logger.error(
                                "Background asset sync failed for asset %s: %s",
                                asset_pk,
                                err,
                            )
                            try:
                                asset_obj = Asset.objects.get(id=asset_pk)
                                asset_obj.status = "failed"
                                asset_obj.last_enrich_error = str(err)
                                asset_obj.save(update_fields=["status", "last_enrich_error"])
                            except Exception as save_error:
                                logger.error("Failed to update asset status: %s", save_error)

                    thread = threading.Thread(
                        target=run_sync_async, args=(asset.id,), daemon=True
                    )
                    thread.start()

                success_count += 1
                results.append(
                    {
                        "assetId": asset_id,
                        "status": "success",
                        "jobId": job_id,
                    }
                )
            except Exception as exc:
                logger.error("Failed to start sync for asset %s: %s", asset_id, exc)
                results.append(
                    {
                        "assetId": asset_id,
                        "status": "failed",
                        "error": str(exc),
                    }
                )

        message = f"Sync started for {success_count} of {len(requested_ids)} assets"

    elif action in {"watch", "unwatch"}:
        for asset_id in requested_ids:
            asset = assets_map.get(asset_id)
            if not asset:
                not_found_count += 1
                results.append({"assetId": asset_id, "status": "not_found"})
                continue

            if action == "watch":
                _entry, created = AssetWatchlistEntry.objects.get_or_create(
                    user=user,
                    asset=asset,
                )
                success_count += 1
                results.append(
                    {
                        "assetId": asset_id,
                        "status": "success",
                        "watched": True,
                        "created": created,
                    }
                )
            else:
                deleted, _ = AssetWatchlistEntry.objects.filter(
                    user=user,
                    asset=asset,
                ).delete()
                success_count += 1
                results.append(
                    {
                        "assetId": asset_id,
                        "status": "success",
                        "watched": False,
                        "removed": bool(deleted),
                    }
                )

        message = (
            f"Updated watchlist for {success_count} of {len(requested_ids)} assets"
        )

    elif action in {"create_report", "report"}:
        sections = data.get("sections") or DEFAULT_REPORT_SECTIONS

        for asset_id in requested_ids:
            asset = assets_map.get(asset_id)
            if not asset:
                not_found_count += 1
                results.append({"assetId": asset_id, "status": "not_found"})
                continue

            try:
                track("report_request", user=user, asset_id=asset_id)
                report = report_service.create_report(asset_id, sections)
                if not report:
                    raise RuntimeError("Failed to create report")

                if not report_service.generate_pdf(report):
                    raise RuntimeError("PDF generation failed")

                _update_onboarding(user, "generate_first_report")
                track("report_success", user=user, asset_id=asset_id)
                track_feature_usage(
                    "report_generation",
                    user=user,
                    asset_id=asset_id,
                    meta={"bulk": True},
                )

                success_count += 1
                results.append(
                    {
                        "assetId": asset_id,
                        "status": "success",
                        "reportId": report.id,
                        "filename": report.filename,
                    }
                )
            except Exception as exc:
                track(
                    "report_fail",
                    user=user,
                    asset_id=asset_id,
                    error_code=str(exc),
                )
                logger.exception("Report generation failed for asset %s", asset_id)
                results.append(
                    {
                        "assetId": asset_id,
                        "status": "failed",
                        "error": str(exc),
                    }
                )

        message = f"Generated reports for {success_count} of {len(requested_ids)} assets"

    else:
        return Response({"error": "Unsupported action"}, status=400)

    failed_count = len(requested_ids) - success_count - not_found_count

    response_data = {
        "action": action,
        "total": len(requested_ids),
        "success": success_count,
        "failed": failed_count,
        "notFound": not_found_count,
        "results": results,
        "message": message,
    }

    status_code = (
        status.HTTP_200_OK
        if success_count == len(requested_ids)
        else status.HTTP_207_MULTI_STATUS
    )

    return Response(response_data, status=status_code)


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def asset_watch(request, asset_id):
    """Add or remove an asset from the authenticated user's watchlist."""

    try:
        asset = Asset.objects.get(id=asset_id)
    except Asset.DoesNotExist:
        return Response({"error": "Asset not found"}, status=status.HTTP_404_NOT_FOUND)

    user = request.user

    if request.method == "POST":
        _entry, created = AssetWatchlistEntry.objects.get_or_create(
            user=user,
            asset=asset,
        )

        return Response(
            {
                "assetId": asset.id,
                "watched": True,
                "created": created,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    deleted, _ = AssetWatchlistEntry.objects.filter(user=user, asset=asset).delete()

    return Response(
        {
            "assetId": asset.id,
            "watched": False,
            "removed": bool(deleted),
        },
        status=status.HTTP_200_OK,
    )


def report_file(request, filename):
    """Serve a generated report PDF from the backend."""
    report = report_service.get_report_by_filename(filename)
    if not report or not os.path.exists(report.file_path):
        raise Http404("Report not found")
    
    # Track export/download event
    track_feature_usage(
        "export",
        user=getattr(request, "user", None),
        asset_id=report.asset_id if report.asset else None,
        meta={
            "export_type": "report",
            "report_type": report.report_type,
            "filename": filename,
        }
    )
    
    return FileResponse(open(report.file_path, "rb"), content_type="application/pdf")


def _group_by_month(transactions):
    months = {}
    for t in transactions:
        try:
            d = datetime.fromisoformat((t.get("date", "") or "")[:10])
        except Exception:
            continue
        key = d.strftime("%Y-%m")
        amt = float(t.get("amount") or 0)
        months.setdefault(key, {"income": 0.0, "expense": 0.0, "net": 0.0, "txs": 0})
        if amt >= 0:
            months[key]["income"] += amt
        else:
            months[key]["expense"] += abs(amt)
        months[key]["net"] += amt
        months[key]["txs"] += 1
    return months


def _median(lst):
    lst = [x for x in lst if x is not None]
    if not lst:
        return 0.0
    try:
        return float(statistics.median(lst))
    except statistics.StatisticsError:
        return float(lst[0])


def _annuity_max_loan(payment, annual_rate_pct, term_years):
    r = (annual_rate_pct / 100.0) / 12.0
    n = term_years * 12
    if r <= 0:
        return payment * n
    return payment * (1 - (1 + r) ** (-n)) / r


@csrf_exempt
def mortgage_analyze(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    price = float(data.get("property_price") or 0)
    savings = float(data.get("savings_total") or 0)
    annual_rate_pct = float(data.get("annual_rate_pct") or 4.5)
    term_years = int(data.get("term_years") or 25)
    logger.info(
        "Mortgage analysis requested: price=%s savings=%s rate=%s term=%s",
        price,
        savings,
        annual_rate_pct,
        term_years,
    )
    transactions = data.get("transactions") or []
    months = _group_by_month(transactions)
    keys = sorted(months.keys())[-6:]
    incomes = [months[k]["income"] for k in keys]
    expenses = [months[k]["expense"] for k in keys]
    med_income = _median(incomes)
    med_expense = _median(expenses)
    surplus = med_income - med_expense
    safety = med_income * 0.10
    recommended_payment = max(0.0, min(med_income * 0.30, surplus - safety))

    def annuity_max_loan(payment, annual_rate_pct, term_years):
        r = (annual_rate_pct / 100.0) / 12.0
        n = term_years * 12
        if r <= 0:
            return payment * n
        return payment * (1 - (1 + r) ** (-n)) / r

    max_loan_from_payment = annuity_max_loan(
        recommended_payment, annual_rate_pct, term_years
    )
    max_loan_by_ltv = price * 0.70 if price > 0 else max_loan_from_payment
    approved_loan_ceiling = min(max_loan_from_payment, max_loan_by_ltv)
    cash_needed = max(0.0, price - approved_loan_ceiling)
    cash_gap = max(0.0, cash_needed - savings)
    logger.info(
        "Mortgage analysis completed for price %s with loan ceiling %s", price, approved_loan_ceiling
    )
    return JsonResponse(
        {
            "metrics": {
                "median_monthly_income": round(med_income),
                "median_monthly_expense": round(med_expense),
                "monthly_surplus_estimate": round(surplus),
            },
            "recommendation": {
                "recommended_monthly_payment": round(recommended_payment),
                "max_loan_from_payment": round(max_loan_from_payment),
                "max_loan_by_ltv": round(max_loan_by_ltv),
                "approved_loan_ceiling": round(approved_loan_ceiling),
                "cash_gap_for_purchase": round(cash_gap),
            },
            "notes": [
                "אינפורמטיבי בלבד",
                "LTV 70%, ריבית {}%, תקופה {}y".format(annual_rate_pct, term_years),
            ],
        }
    )


@csrf_exempt
def tabu(request):
    """Parse an uploaded Tabu PDF and return its data as a searchable table.

    Note: If the utils module is not available, this will return dummy data
    to ensure the app continues to function.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    file = request.FILES.get("file")
    if not file:
        return JsonResponse({"error": "file required"}, status=400)

    # Try to parse the PDF file
    try:
        if TabuParser:
            parser = TabuParser(file)
            rows = parser.parse()
        else:
            rows = []
        query = request.GET.get("q") or ""
        if query:
            # Simple search implementation
            rows = [row for row in rows if query.lower() in row.get('field', '').lower() or query.lower() in row.get('value', '').lower()]
            # Track search query
            track_search(
                query=query,
                user=getattr(request, "user", None),
                meta={
                    "source": "tabu",
                    "results_count": len(rows),
                }
            )
        return JsonResponse({"rows": rows})
    except Exception as e:
        logger.error("Error parsing tabu PDF: %s", e)
        # Return dummy data for testing if parsing fails
        # This also handles the case where utils module is not available
        return JsonResponse(
            {
                "rows": [
                    {
                        "id": 1,
                        "block": "1234",
                        "parcel": "56",
                        "owner": "בעלים לדוגמה",
                        "area": "150",
                        "usage": "מגורים",
                    }
                ]
            }
        )


@api_view(["GET", "POST", "DELETE"])
@permission_classes([AllowAny])  # Allow both authenticated and unauthenticated access
def assets(request):
    """Handle assets - GET (list all) or POST (create new).

    GET: Returns all assets in listing format
    POST: Creates a new asset and enqueues enrichment pipeline

    Expected JSON payload for POST:
    {
        "scope": {
            "type": "address|neighborhood|street|city|parcel",
            "value": "string",
            "city": "string"
        },
        "address": "string",
        "city": "string",
        "street": "string",
        "number": "integer",
        "block": "string",
        "parcel": "string",
        "radius": "integer"
    }
    """
    if request.method == "GET":
        # Return paginated assets in listing format
        return _get_assets_list(request)

    if request.method == "DELETE":
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return Response({"error": "Authentication required"}, status=status.HTTP_403_FORBIDDEN)

        if not (
            getattr(user, "role", None) == User.Role.ADMIN
            or getattr(user, "is_superuser", False)
        ):
            return Response(
                {"error": "Admin privileges required to delete assets"},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = parse_json(request)
        if not data or not data.get("assetId"):
            return Response({"error": "assetId required"}, status=400)

        try:
            asset_id = int(data["assetId"])
            asset = Asset.objects.get(id=asset_id)

            if asset.delete_asset():
                return Response(
                    {"message": "Asset {} deleted successfully".format(asset_id)}, status=200
                )
            else:
                return Response({"error": "Failed to delete asset"}, status=500)

        except Asset.DoesNotExist:
            return Response({"error": "Asset not found"}, status=404)
        except ValueError:
            return Response({"error": "Invalid asset ID"}, status=400)
        except Exception as e:
            return Response(
                {"error": "Error deleting asset", "details": str(e)}, status=500
            )

    if request.method != "POST":
        return Response({"error": "POST method required"}, status=405)

    # Rate limiting per IP to prevent abuse
    ip = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if ip:
        ip = ip.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR", "")
    now = timezone.now()
    entry = _assets_rate_limit.get(ip)
    if entry and entry["expires"] > now and entry["count"] >= ASSETS_POST_LIMIT:
        return JsonResponse({"error": "Too many requests"}, status=429)
    if not entry or entry["expires"] <= now:
        _assets_rate_limit[ip] = {
            "count": 1,
            "expires": now + timedelta(seconds=ASSETS_POST_WINDOW),
        }
    else:
        entry["count"] += 1
    cache_key = "assets_post_{}".format(ip)
    cache_count = cache.get(cache_key, 0)
    if cache_count >= ASSETS_POST_LIMIT:
        return Response({"error": "Too many requests"}, status=429)
    cache.set(cache_key, cache_count + 1, ASSETS_POST_WINDOW)

    # Parse JSON with error handling
    data = parse_json(request)
    if not data:
        return Response({"error": "Invalid JSON in request body"}, status=400)

    try:
        # Extract scope information
        scope = data.get("scope", {})
        scope_type = scope.get("type")
        if not scope_type:
            return Response({"error": "Scope type is required"}, status=400)

        # Get user for attribution
        user = getattr(request, "user", None)
        is_authenticated = user and getattr(user, "is_authenticated", False)
        
        # Validate plan limits for authenticated users
        if is_authenticated:
            from .plan_service import PlanService
            validation_result = PlanService.validate_asset_creation(user)
            if not validation_result['can_create']:
                return Response({
                    'error': validation_result['error'],
                    'message': validation_result['message'],
                    'current_plan': validation_result.get('current_plan'),
                    'asset_limit': validation_result.get('asset_limit'),
                    'assets_used': validation_result.get('assets_used'),
                    'remaining': validation_result.get('remaining', 0)
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Check for existing asset using deduplication service
        from .services.asset_deduplication import find_existing_asset
        from orchestration.location import LocationQuery
        
        city = data.get("city") or scope.get("city")
        location = LocationQuery(
            city=city or "",
            street=data.get("street") or "",
            house_number=data.get("number"),
            block=data.get("block"),
            parcel=data.get("parcel"),
            subparcel=data.get("subparcel"),
        )
        existing_asset = find_existing_asset(
            location=location,
            scope_type=scope_type,
        )
        
        if existing_asset:
            # Update existing asset instead of creating duplicate
            asset = existing_asset
            asset.status = "pending"  # Reset status to trigger re-enrichment
            asset.last_updated_by = user if is_authenticated else None
            
            # Update meta with new scope/input if needed
            if not asset.meta:
                asset.meta = {}
            asset.meta.update({
                "scope": scope,
                "raw_input": data,
                "radius": data.get("radius", 150),
            })
            asset.save()
            logger.info("Found existing asset %s, updating instead of creating duplicate", asset.id)
            
            # Create asset_data dict for response consistency
            asset_data = {
                "status": asset.status,
                "scope_type": asset.scope_type,
                "city": asset.city,
                "neighborhood": asset.neighborhood,
                "street": asset.street,
                "number": asset.number,
                "apartment": asset.apartment,
                "block": asset.block,
                "parcel": asset.parcel,
                "subparcel": asset.subparcel,
            }
        else:
            # Create asset record with attribution
            asset_data = {
                "scope_type": scope_type,
                "city": city,
                "neighborhood": data.get("neighborhood"),
                "street": data.get("street"),
                "number": data.get("number"),
                "apartment": data.get("apartment"),
                "block": data.get("block"),
                "parcel": data.get("parcel"),
                "subparcel": data.get("subparcel"),
                "status": "pending",
                "created_by": user if is_authenticated else None,
                "last_updated_by": user if is_authenticated else None,
                "meta": {
                    "scope": scope,
                    "raw_input": data,
                    "radius": data.get("radius", 150),
                },
            }

            # Save to Django database
            asset = Asset.objects.create(**asset_data)
        asset_id = asset.id
        
        # Create attribution record if user is authenticated
        if is_authenticated:
            from .models import AssetContribution, UserProfile
            AssetContribution.objects.create(
                asset=asset,
                user=user,
                contribution_type='creation',
                description="נוצר נכס עבור {}: {}".format(scope_type, data.get('city', 'מיקום לא ידוע')),
                source='manual'
            )
            
            # Update user profile stats
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.update_contribution_stats('creation')
            
            # Update plan usage
            from .plan_service import PlanService
            PlanService.update_asset_usage(user, 1)
        
        logger.info("Asset creation - User: %s, Authenticated: %s", 
                   user, is_authenticated)
        if is_authenticated:
            track("asset_create", user=user, asset_id=asset_id)
        else:
            track("asset_create", asset_id=asset_id)
        
        # Track feature usage
        track_feature_usage("asset_creation", user=user, asset_id=asset_id)
        _update_onboarding(user, "add_first_asset")

        # Enqueue Celery task if available, otherwise run in background thread
        job_id = None
        try:
            # Check if Celery is enabled
            from django.conf import settings
            if hasattr(settings, 'CELERY_BROKER_URL') and settings.CELERY_BROKER_URL:
                result = run_data_pipeline.delay(asset_id)
                job_id = result.id
                logger.info("Enqueued enrichment task with job ID: %s", job_id)
            else:
                # Run asynchronously in background thread when Celery is disabled
                import threading
                logger.info("Celery disabled, running data pipeline in background thread")
                
                def run_pipeline_async():
                    try:
                        run_data_pipeline(asset_id)
                        logger.info("Background data pipeline completed for asset %s", asset_id)
                    except Exception as e:
                        logger.error("Background data pipeline failed for asset %s: %s", asset_id, e)
                        # Update asset status to error
                        try:
                            asset = Asset.objects.get(id=asset_id)
                            asset.status = "failed"
                            asset.last_enrich_error = str(e)
                            asset.save()
                        except Exception as save_error:
                            logger.error("Failed to update asset status: %s", save_error)
                
                thread = threading.Thread(target=run_pipeline_async, daemon=True)
                thread.start()
                logger.info("Started background data pipeline thread for asset %s", asset_id)
        except Exception as e:
            logger.error("Failed to start enrichment task: %s", e)
            # Update asset status to error
            try:
                asset = Asset.objects.get(id=asset_id)
                asset.status = "failed"
                asset.meta["error"] = str(e)
                asset.save()
            except Exception as save_error:
                logger.error("Failed to update asset status: %s", save_error)

        return Response(
            {
                "id": asset_id,
                "status": asset_data["status"],
                "job_id": job_id,
                "message": "Asset created successfully, enrichment pipeline started",
            },
            status=201,
        )

    except Exception as e:
        logger.error("Error creating asset: %s", e)
        return Response(
            {"error": "Failed to create asset", "details": str(e)}, status=500
        )


def _parse_positive_int(value, default):
    try:
        parsed = int(value)
        if parsed > 0:
            return parsed
    except (TypeError, ValueError):
        pass
    return default


def _parse_optional_number(value, cast_type=float):
    try:
        if value is None:
            return None
        parsed = cast_type(value)
        return parsed
    except (TypeError, ValueError):
        return None


def _parse_bool(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    value_str = str(value).strip().lower()
    if value_str in {"1", "true", "yes", "on"}:
        return True
    if value_str in {"0", "false", "no", "off"}:
        return False
    return None


def _apply_asset_filters(queryset, params, user):
    search = params.get("search")
    if search:
        queryset = queryset.filter(
            Q(normalized_address__icontains=search)
            | Q(city__icontains=search)
            | Q(neighborhood__icontains=search)
            | Q(street__icontains=search)
            | Q(block__icontains=search)
            | Q(parcel__icontains=search)
            | Q(building_type__icontains=search)
            | Q(meta__address__icontains=search)
            | Q(meta__raw_input__address__icontains=search)
        )
        # Track search query
        track_search(
            query=search,
            user=user if user and getattr(user, "is_authenticated", False) else None,
            results_count=queryset.count(),
            meta={"source": "assets_list"}
        )

    city = params.get("city")
    if city and city != "all":
        queryset = queryset.filter(city__iexact=city)

    type_filter = params.get("type")
    if type_filter and type_filter != "all":
        queryset = queryset.filter(
            Q(building_type__iexact=type_filter)
            | Q(meta__property_type__iexact=type_filter)
            | Q(meta__propertyType__iexact=type_filter)
        )

    price_min = _parse_optional_number(params.get("priceMin"), int)
    if price_min is not None:
        queryset = queryset.filter(price__gte=price_min)

    price_max = _parse_optional_number(params.get("priceMax"), int)
    if price_max is not None:
        queryset = queryset.filter(price__lte=price_max)

    neighborhood = params.get("neighborhood")
    if neighborhood and neighborhood != "all":
        queryset = queryset.filter(neighborhood__iexact=neighborhood)

    zoning = params.get("zoning")
    if zoning and zoning != "all":
        queryset = queryset.filter(zoning__iexact=zoning)

    risk_filter = params.get("risk")
    if risk_filter == "flagged":
        queryset = queryset.exclude(
            Q(risk_flags__isnull=True) | Q(risk_flags=[])
        )
    elif risk_filter == "clean":
        queryset = queryset.filter(
            Q(risk_flags__isnull=True) | Q(risk_flags=[])
        )

    documents_filter = params.get("documents")
    if documents_filter == "with":
        queryset = queryset.filter(
            Q(documents__isnull=False) | Q(documents_m2m__isnull=False)
        )
    elif documents_filter == "without":
        queryset = queryset.filter(
            documents__isnull=True, documents_m2m__isnull=True
        )

    status_filter = params.get("status")
    if status_filter and status_filter != "all":
        queryset = queryset.filter(status__iexact=status_filter)

    rental_sale = params.get("rentalSale")
    if rental_sale and rental_sale != "all":
        rental_sale_str = str(rental_sale) if rental_sale else ""
        normalized_rental_sale = rental_sale_str.strip().lower()
        matching_asset_ids = set(
            AssetListing.objects.filter(
                listing__listing_type__iexact=normalized_rental_sale
            ).values_list("asset_id", flat=True)
        )

        if normalized_rental_sale in {"rent", "sale"}:
            candidate_ids = list(queryset.values_list("id", flat=True))
            if candidate_ids:
                for asset in Asset.objects.filter(id__in=candidate_ids).only("id", "meta"):
                    yad2_listings = asset.get_property_value("yad2_listings", []) or []
                    for listing in yad2_listings:
                        if not isinstance(listing, dict):
                            continue
                        # Safely extract listing_type
                        listing_type_value = listing.get("listing_type") or listing.get("listingType")
                        if listing_type_value and isinstance(listing_type_value, str):
                            listing_type_value = listing_type_value.lower()
                        else:
                            listing_type_value = ""
                        if listing_type_value == normalized_rental_sale:
                            matching_asset_ids.add(asset.id)
                            break

        if matching_asset_ids:
            queryset = queryset.filter(id__in=matching_asset_ids).distinct()
        else:
            queryset = queryset.none()

    ad_type_filter = params.get("adType") or params.get("ad_type")
    if ad_type_filter and ad_type_filter != "all":
        ad_type_str = str(ad_type_filter) if ad_type_filter else ""
        normalized_ad_type = ad_type_str.strip().lower()
        matching_asset_ids = set(
            AssetListing.objects.filter(
                listing__ad_type__iexact=normalized_ad_type
            ).values_list("asset_id", flat=True)
        )

        candidate_ids = list(queryset.values_list("id", flat=True))
        if candidate_ids:
            for asset in Asset.objects.filter(id__in=candidate_ids).only("id", "meta"):
                yad2_listings = asset.get_property_value("yad2_listings", []) or []
                for listing in yad2_listings:
                    if not isinstance(listing, dict):
                        continue
                    # Safely extract ad_type
                    ad_type_value = listing.get("ad_type") or listing.get("adType")
                    if ad_type_value and isinstance(ad_type_value, str):
                        ad_type_value = ad_type_value.lower()
                    else:
                        ad_type_value = ""
                    if ad_type_value == normalized_ad_type:
                        matching_asset_ids.add(asset.id)
                        break

        if matching_asset_ids:
            queryset = queryset.filter(id__in=matching_asset_ids).distinct()
        else:
            return queryset.none()

    commercial_filter = params.get("commercial")
    if commercial_filter == "commercial":
        queryset = queryset.filter(is_commercial=True)
    elif commercial_filter == "residential":
        queryset = queryset.filter(
            Q(is_commercial=False) | Q(is_commercial__isnull=True)
        )

    user_assets = params.get("userAssets")
    if user_assets and user_assets != "all":
        if not user or not getattr(user, "is_authenticated", False):
            return queryset.none()
        if user_assets == "mine":
            queryset = queryset.filter(created_by=user)
        elif user_assets == "others":
            queryset = queryset.exclude(created_by=user)
        elif user_assets in {"watchlist", "tracked"}:
            queryset = queryset.filter(watchers=user)

    building_type = params.get("buildingType")
    if building_type and building_type != "all":
        queryset = queryset.filter(building_type__iexact=building_type)

    floor_min = _parse_optional_number(params.get("floorMin"), int)
    if floor_min is not None:
        queryset = queryset.filter(floor__gte=floor_min)

    floor_max = _parse_optional_number(params.get("floorMax"), int)
    if floor_max is not None:
        queryset = queryset.filter(floor__lte=floor_max)

    area_min = _parse_optional_number(params.get("areaMin"))
    if area_min is not None:
        queryset = queryset.filter(area__gte=area_min)

    area_max = _parse_optional_number(params.get("areaMax"))
    if area_max is not None:
        queryset = queryset.filter(area__lte=area_max)

    rooms_filter = params.get("rooms")
    if rooms_filter and rooms_filter != "all":
        rooms_value = _parse_optional_number(rooms_filter, int)
        if rooms_value is not None:
            queryset = queryset.filter(rooms=rooms_value)

    features_filter = params.get("features")
    if features_filter and features_filter != "all":
        if features_filter == "elevator":
            queryset = queryset.filter(elevator=True)
        elif features_filter == "parking":
            queryset = queryset.filter(parking_spaces__gt=0)
        elif features_filter == "balcony":
            queryset = queryset.filter(balcony_area__gt=0)
        elif features_filter == "storage":
            queryset = queryset.filter(storage_room=True)
        elif features_filter == "air_conditioning":
            queryset = queryset.filter(air_conditioning=True)
        elif features_filter == "furnished":
            queryset = queryset.filter(furnished=True)
        elif features_filter == "renovated":
            queryset = queryset.filter(renovated=True)

    price_per_sqm_min = _parse_optional_number(params.get("pricePerSqmMin"), int)
    if price_per_sqm_min is not None:
        queryset = queryset.filter(price_per_sqm__gte=price_per_sqm_min)

    price_per_sqm_max = _parse_optional_number(params.get("pricePerSqmMax"), int)
    if price_per_sqm_max is not None:
        queryset = queryset.filter(price_per_sqm__lte=price_per_sqm_max)

    remaining_rights_min = _parse_optional_number(params.get("remainingRightsMin"))
    if remaining_rights_min is not None:
        queryset = queryset.filter(meta__remainingRightsSqm__gte=remaining_rights_min)

    remaining_rights_max = _parse_optional_number(params.get("remainingRightsMax"))
    if remaining_rights_max is not None:
        queryset = queryset.filter(meta__remainingRightsSqm__lte=remaining_rights_max)

    block_filter = params.get("block")
    if block_filter and block_filter != "all":
        queryset = queryset.filter(block__iexact=block_filter)

    parcel_filter = params.get("parcel")
    if parcel_filter and parcel_filter != "all":
        queryset = queryset.filter(parcel__iexact=parcel_filter)

    bedrooms_min = _parse_optional_number(params.get("bedroomsMin"), int)
    if bedrooms_min is not None:
        queryset = queryset.filter(bedrooms__gte=bedrooms_min)

    bedrooms_max = _parse_optional_number(params.get("bedroomsMax"), int)
    if bedrooms_max is not None:
        queryset = queryset.filter(bedrooms__lte=bedrooms_max)

    bathrooms_min = _parse_optional_number(params.get("bathroomsMin"), int)
    if bathrooms_min is not None:
        queryset = queryset.filter(bathrooms__gte=bathrooms_min)

    bathrooms_max = _parse_optional_number(params.get("bathroomsMax"), int)
    if bathrooms_max is not None:
        queryset = queryset.filter(bathrooms__lte=bathrooms_max)

    total_floors_min = _parse_optional_number(params.get("totalFloorsMin"), int)
    if total_floors_min is not None:
        queryset = queryset.filter(total_floors__gte=total_floors_min)

    total_floors_max = _parse_optional_number(params.get("totalFloorsMax"), int)
    if total_floors_max is not None:
        queryset = queryset.filter(total_floors__lte=total_floors_max)

    total_area_min = _parse_optional_number(params.get("totalAreaMin"))
    if total_area_min is not None:
        queryset = queryset.filter(total_area__gte=total_area_min)

    total_area_max = _parse_optional_number(params.get("totalAreaMax"))
    if total_area_max is not None:
        queryset = queryset.filter(total_area__lte=total_area_max)

    balcony_area_min = _parse_optional_number(params.get("balconyAreaMin"))
    if balcony_area_min is not None:
        queryset = queryset.filter(balcony_area__gte=balcony_area_min)

    balcony_area_max = _parse_optional_number(params.get("balconyAreaMax"))
    if balcony_area_max is not None:
        queryset = queryset.filter(balcony_area__lte=balcony_area_max)

    parking_spaces_min = _parse_optional_number(params.get("parkingSpacesMin"), int)
    if parking_spaces_min is not None:
        queryset = queryset.filter(parking_spaces__gte=parking_spaces_min)

    parking_spaces_max = _parse_optional_number(params.get("parkingSpacesMax"), int)
    if parking_spaces_max is not None:
        queryset = queryset.filter(parking_spaces__lte=parking_spaces_max)

    year_built_min = _parse_optional_number(params.get("yearBuiltMin"), int)
    if year_built_min is not None:
        queryset = queryset.filter(year_built__gte=year_built_min)

    year_built_max = _parse_optional_number(params.get("yearBuiltMax"), int)
    if year_built_max is not None:
        queryset = queryset.filter(year_built__lte=year_built_max)

    rent_price_min = _parse_optional_number(params.get("rentPriceMin"), int)
    if rent_price_min is not None:
        queryset = queryset.filter(rent_price__gte=rent_price_min)

    rent_price_max = _parse_optional_number(params.get("rentPriceMax"), int)
    if rent_price_max is not None:
        queryset = queryset.filter(rent_price__lte=rent_price_max)

    rent_estimate_min = _parse_optional_number(params.get("rentEstimateMin"), int)
    if rent_estimate_min is not None:
        queryset = queryset.filter(rent_estimate__gte=rent_estimate_min)

    rent_estimate_max = _parse_optional_number(params.get("rentEstimateMax"), int)
    if rent_estimate_max is not None:
        queryset = queryset.filter(rent_estimate__lte=rent_estimate_max)

    price_gap_pct_min = _parse_optional_number(params.get("priceGapPctMin"))
    if price_gap_pct_min is not None:
        queryset = queryset.filter(price_gap_pct__gte=price_gap_pct_min)

    price_gap_pct_max = _parse_optional_number(params.get("priceGapPctMax"))
    if price_gap_pct_max is not None:
        queryset = queryset.filter(price_gap_pct__lte=price_gap_pct_max)

    cap_rate_pct_min = _parse_optional_number(params.get("capRatePctMin"))
    if cap_rate_pct_min is not None:
        queryset = queryset.filter(cap_rate_pct__gte=cap_rate_pct_min)

    cap_rate_pct_max = _parse_optional_number(params.get("capRatePctMax"))
    if cap_rate_pct_max is not None:
        queryset = queryset.filter(cap_rate_pct__lte=cap_rate_pct_max)

    renovated_filter = _parse_bool(params.get("renovated"))
    if renovated_filter is not None:
        queryset = queryset.filter(renovated=renovated_filter)

    furnished_filter = _parse_bool(params.get("furnished"))
    if furnished_filter is not None:
        queryset = queryset.filter(furnished=furnished_filter)

    air_conditioning_filter = _parse_bool(params.get("airConditioning"))
    if air_conditioning_filter is not None:
        queryset = queryset.filter(air_conditioning=air_conditioning_filter)

    storage_room_filter = _parse_bool(params.get("storageRoom"))
    if storage_room_filter is not None:
        queryset = queryset.filter(storage_room=storage_room_filter)

    elevator_filter = _parse_bool(params.get("hasElevator"))
    if elevator_filter is not None:
        queryset = queryset.filter(elevator=elevator_filter)

    return queryset.distinct()


def _get_asset_filter_metadata():
    base_qs = Asset.objects.all()

    def _distinct(field):
        return [
            value
            for value in base_qs.order_by().values_list(field, flat=True).distinct()
            if value not in (None, "")
        ]

    property_types = set(_distinct("building_type"))
    property_types.update(
        value
        for value in base_qs.order_by().values_list("meta__property_type", flat=True).distinct()
        if value not in (None, "")
    )
    property_types.update(
        value
        for value in base_qs.order_by().values_list("meta__propertyType", flat=True).distinct()
        if value not in (None, "")
    )

    room_values = sorted(
        {
            value
            for value in base_qs.order_by().values_list("rooms", flat=True).distinct()
            if value is not None
        }
    )

    status_counts = {
        row["status"]: row["count"]
        for row in base_qs.values("status").annotate(count=Count("id"))
        if row["status"]
    }

    listing_ad_types = sorted(
        {
            value
            for value in AssetListing.objects.order_by()
            .values_list("listing__ad_type", flat=True)
            .distinct()
            if value not in (None, "")
        }
    )

    numeric_ranges = base_qs.aggregate(
        bedrooms_min=Min("bedrooms"),
        bedrooms_max=Max("bedrooms"),
        bathrooms_min=Min("bathrooms"),
        bathrooms_max=Max("bathrooms"),
        total_floors_min=Min("total_floors"),
        total_floors_max=Max("total_floors"),
        parking_spaces_min=Min("parking_spaces"),
        parking_spaces_max=Max("parking_spaces"),
        balcony_area_min=Min("balcony_area"),
        balcony_area_max=Max("balcony_area"),
        total_area_min=Min("total_area"),
        total_area_max=Max("total_area"),
        year_built_min=Min("year_built"),
        year_built_max=Max("year_built"),
        rent_price_min=Min("rent_price"),
        rent_price_max=Max("rent_price"),
        rent_estimate_min=Min("rent_estimate"),
        rent_estimate_max=Max("rent_estimate"),
        price_gap_pct_min=Min("price_gap_pct"),
        price_gap_pct_max=Max("price_gap_pct"),
        cap_rate_pct_min=Min("cap_rate_pct"),
        cap_rate_pct_max=Max("cap_rate_pct"),
    )

    def _range_dict(min_key, max_key):
        min_value = numeric_ranges.get(min_key)
        max_value = numeric_ranges.get(max_key)
        if min_value is None and max_value is None:
            return {"min": None, "max": None}
        return {"min": min_value, "max": max_value}

    return {
        "cities": sorted(set(_distinct("city"))),
        "types": sorted(property_types),
        "neighborhoods": sorted(set(_distinct("neighborhood"))),
        "zonings": sorted(set(_distinct("zoning"))),
        "blocks": sorted(set(_distinct("block"))),
        "parcels": sorted(set(_distinct("parcel"))),
        "buildingTypes": sorted(set(_distinct("building_type"))),
        "rooms": room_values,
        "statusCounts": status_counts,
        "listingAdTypes": listing_ad_types,
        "bedroomCounts": sorted(
            {
                value
                for value in base_qs.order_by().values_list("bedrooms", flat=True).distinct()
                if value is not None
            }
        ),
        "bathroomCounts": sorted(
            {
                value
                for value in base_qs.order_by().values_list("bathrooms", flat=True).distinct()
                if value is not None
            }
        ),
        "totalFloorCounts": sorted(
            {
                value
                for value in base_qs.order_by().values_list("total_floors", flat=True).distinct()
                if value is not None
            }
        ),
        "parkingSpaceCounts": sorted(
            {
                value
                for value in base_qs.order_by().values_list("parking_spaces", flat=True).distinct()
                if value is not None
            }
        ),
        "balconyAreas": sorted(
            {
                value
                for value in base_qs.order_by().values_list("balcony_area", flat=True).distinct()
                if value is not None
            }
        ),
        "totalAreaRange": _range_dict("total_area_min", "total_area_max"),
        "yearBuiltRange": _range_dict("year_built_min", "year_built_max"),
        "rentPriceRange": _range_dict("rent_price_min", "rent_price_max"),
        "rentEstimateRange": _range_dict("rent_estimate_min", "rent_estimate_max"),
        "priceGapPctRange": _range_dict("price_gap_pct_min", "price_gap_pct_max"),
        "capRatePctRange": _range_dict("cap_rate_pct_min", "cap_rate_pct_max"),
        "bedroomRange": _range_dict("bedrooms_min", "bedrooms_max"),
        "bathroomRange": _range_dict("bathrooms_min", "bathrooms_max"),
        "totalFloorRange": _range_dict("total_floors_min", "total_floors_max"),
        "parkingSpaceRange": _range_dict("parking_spaces_min", "parking_spaces_max"),
        "balconyAreaRange": _range_dict("balcony_area_min", "balcony_area_max"),
    }


def _get_assets_list(request):
    """Helper function to get paginated assets in listing format."""

    params = request.GET

    page = _parse_positive_int(params.get("page"), 1)
    page_size = _parse_positive_int(
        params.get("pageSize") or params.get("page_size"), DEFAULT_ASSET_PAGE_SIZE
    )
    page_size = min(page_size, MAX_ASSET_PAGE_SIZE)

    try:
        user = getattr(request, "user", None)
        queryset = Asset.objects.all().prefetch_related("listings_m2m")

        if user and getattr(user, "is_authenticated", False):
            queryset = queryset.annotate(
                is_watched=Exists(
                    AssetWatchlistEntry.objects.filter(
                        user=user,
                        asset_id=OuterRef("pk"),
                    )
                )
            )

        # Track if any filters are applied (excluding search which is tracked separately)
        has_filters = any(
            params.get(key) not in (None, "", "all")
            for key in [
                "city", "type", "priceMin", "priceMax", "neighborhood", "zoning",
                "risk", "documents", "status", "rentalSale", "adType", "ad_type",
                "commercial", "userAssets", "buildingType", "floorMin", "floorMax",
                "areaMin", "areaMax", "rooms", "features", "pricePerSqmMin", "pricePerSqmMax"
            ]
        )
        
        if has_filters:
            track_feature_usage(
                "filter",
                user=user if user and getattr(user, "is_authenticated", False) else None,
                meta={
                    "filter_params": {k: v for k, v in params.items() if k != "search" and v not in (None, "", "all")},
                    "source": "assets_list"
                }
            )
        
        queryset = _apply_asset_filters(queryset, params, user)

        # Handle ordering parameter
        ordering_param = params.get("ordering", "-created_at")
        if ordering_param:
            ordering_field = ordering_param.lstrip("-")
            ordering_map = {
                "address": "normalized_address",
                "city": "city",
                "street": "street",
                "number": "number",
                "apartment": "apartment",
                "block": "block",
                "parcel": "parcel",
                "subparcel": "subparcel",
                "area": "area",
                "total_area": "total_area",
                "subparcel_area": "subparcel_area",
                "built_area": "built_area",
                "floor": "floor",
                "total_floors": "total_floors",
                "listing_type": "listing_type",
                "ad_type": "ad_type",
                "price": "price",
                "rent_price": "rent_price",
                "price_per_sqm": "price_per_sqm",
                "delta_vs_area_pct": "delta_vs_area_pct",
                "dom_percentile": "dom_percentile",
                "competition_1km": "competition_1km",
                "zoning": "zoning",
                "remaining_rights_sqm": "remaining_rights_sqm",
                "program": "program",
                "last_permit_q": "last_permit_q",
                "documents_count": "documents__count",  # Note: might need annotation
                "noise_level": "noise_level",
                "antenna_distance_m": "antenna_distance_m",
                "green_within_300m": "green_within_300m",
                "shelter_distance_m": "shelter_distance_m",
                "asset_status": "asset_status",
                "model_price": "model_price",
                "price_gap_pct": "price_gap_pct",
                "confidence_pct": "confidence_pct",
                "cap_rate_pct": "cap_rate_pct",
                "rent_estimate": "rent_estimate",
                "recent_deal": "recent_deal",
                "created_at": "created_at",
            }
            
            if ordering_field in ordering_map:
                mapped_field = ordering_map[ordering_field]
                ordering_prefix = "-" if ordering_param.startswith("-") else ""
                queryset = queryset.order_by(f"{ordering_prefix}{mapped_field}", "-id")
            else:
                # Default ordering if field not recognized
                queryset = queryset.order_by("-created_at", "-id")
        else:
            # Default ordering if no ordering parameter
            queryset = queryset.order_by("-created_at", "-id")

        paginator = Paginator(queryset, page_size)
        try:
            page_obj = paginator.page(page)
        except (EmptyPage, PageNotAnInteger):
            page_obj = paginator.page(1)

        serializer = AssetSerializer(
            page_obj.object_list,
            many=True,
            context={"include_documents": False, "request": request},
        )

        return Response(
            {
                "rows": serializer.data,
                "pagination": {
                    "page": page_obj.number,
                    "page_size": page_size,
                    "total": paginator.count,
                    "total_pages": paginator.num_pages,
                    "has_next": page_obj.has_next(),
                    "has_previous": page_obj.has_previous(),
                },
                "filters": _get_asset_filter_metadata(),
            }
        )
    except Exception as e:
        logger.error("Error fetching assets: %s", e)
        return Response(
            {"error": "Failed to fetch assets", "details": str(e)}, status=500
        )


@csrf_exempt
def asset_detail(request, asset_id):
    """Get asset details including enriched data and source records."""
    if request.method != "GET":
        return JsonResponse({"error": "GET method required"}, status=405)

    try:
        include_documents_param = request.GET.get("includeDocuments")
        if include_documents_param is None:
            include_documents_param = request.GET.get("include_documents")

        include_documents = _parse_bool(include_documents_param)
        if include_documents is None:
            include_documents = False

        prefetch_fields = [
            'transactions',
            'transactions_m2m',
            'permits',
            'permits_m2m',
            'plans',
            'plans_m2m',
            'listings_m2m',  # Needed for primary_listing and price/pricePerSqm from listings
        ]
        if include_documents:
            prefetch_fields.extend(['documents', 'documents_m2m'])

        # Get asset using Django ORM with attribution data and optional documents
        try:
            queryset = Asset.objects.select_related('created_by', 'last_updated_by')
            if prefetch_fields:
                queryset = queryset.prefetch_related(*prefetch_fields)
            asset = queryset.get(id=asset_id)
        except Asset.DoesNotExist:
            return JsonResponse({"error": "Asset not found"}, status=404)

        # Get source records grouped by source
        source_records = SourceRecord.objects.filter(asset_id=asset_id)
        records_by_source = {}
        for record in source_records:
            if record.source not in records_by_source:
                records_by_source[record.source] = []
            records_by_source[record.source].append(
                {
                    "id": record.id,
                    "title": record.title,
                    "external_id": record.external_id,
                    "url": record.url,
                    "file_path": record.file_path,
                    "raw": record.raw,
                    "fetched_at": (
                        record.fetched_at.isoformat() if record.fetched_at else None
                    ),
                }
            )

        # Get transactions
        transactions = asset_transactions_all(asset)
        transaction_list = []
        for trans in transactions:
            transaction_list.append(
                {
                    "id": trans.id,
                    "deal_id": trans.deal_id,
                    "date": trans.date.isoformat() if trans.date else None,
                    "price": trans.price,
                    "rooms": trans.rooms,
                    "area": trans.area,
                    "floor": trans.floor,
                    "address": trans.address,
                    "raw": trans.raw,
                    "fetched_at": (
                        trans.fetched_at.isoformat() if trans.fetched_at else None
                    ),
                }
            )

        # Get latest snapshot data
        latest_snapshot = Snapshot.objects.filter(asset_id=asset_id).order_by('-created_at').first()
        snapshot_data = {}
        if latest_snapshot:
            snapshot_data = {
                "id": latest_snapshot.id,
                "created_at": latest_snapshot.created_at.isoformat(),
                "ppsqm": latest_snapshot.ppsqm,
                "payload": latest_snapshot.payload,
            }

        # Get attribution information
        attribution_info = {}
        if asset.created_by:
            attribution_info["created_by"] = {
                "id": asset.created_by.id,
                "email": asset.created_by.email,
                "name": "{} {}".format(asset.created_by.first_name, asset.created_by.last_name).strip() or asset.created_by.email,
            }
        if asset.last_updated_by:
            attribution_info["last_updated_by"] = {
                "id": asset.last_updated_by.id,
                "email": asset.last_updated_by.email,
                "name": "{} {}".format(asset.last_updated_by.first_name, asset.last_updated_by.last_name).strip() or asset.last_updated_by.email,
            }
        
        # Get recent contributions (last 5)
        from .models import AssetContribution
        recent_contributions = AssetContribution.objects.filter(asset=asset).order_by('-created_at')[:5]
        contributions_list = []
        
        # Hebrew translations for contribution types
        contribution_translations = {
            'creation': 'יצירת נכס',
            'enrichment': 'העשרת נתונים',
            'verification': 'אימות נתונים',
            'update': 'עדכון שדה',
            'source_add': 'הוספת מקור',
            'comment': 'הערה/תגובה'
        }
        
        for contrib in recent_contributions:
            contributions_list.append({
                "id": contrib.id,
                "user": {
                    "email": contrib.user.email,
                    "name": "{} {}".format(contrib.user.first_name, contrib.user.last_name).strip() or contrib.user.email,
                },
                "type": contrib.contribution_type,
                "type_display": contribution_translations.get(contrib.contribution_type, contrib.get_contribution_type_display()),
                "field_name": contrib.field_name,
                "description": contrib.description,
                "source": contrib.source,
                "created_at": contrib.created_at.isoformat(),
            })

        # Use serializer to get properly formatted asset data with _meta
        from .serializers import AssetSerializer
        serializer = AssetSerializer(
            asset,
            context={
                "request": request,
                "include_documents": include_documents,
            },
        )
        asset_data = serializer.data

        # Get CRM data for this asset
        crm_data = {}
        try:
            from crm.models import Lead
            from crm.serializers import LeadSerializer
            
            # Get leads for this asset
            leads = Lead.objects.filter(asset=asset).select_related('contact').order_by('-last_activity_at')
            leads_serializer = LeadSerializer(leads, many=True, context={'request': request})
            crm_data = {
                "leads": leads_serializer.data,
                "leads_count": leads.count()
            }
        except Exception as e:
            logger.warning(f"Error fetching CRM data for asset {asset_id}: {e}")
            crm_data = {
                "leads": [],
                "leads_count": 0
            }
        
        # Add additional data not in the serializer
        asset_data.update({
            "attribution": attribution_info,
            "recent_contributions": contributions_list,
            "records": records_by_source,
            "transactions": transaction_list,
            "snapshot": snapshot_data,
            "CRM": crm_data,
        })
        
        return JsonResponse({"asset": asset_data})

    except Exception as e:
        logger.error("Error retrieving asset %s: %s", asset_id, e)
        return JsonResponse(
            {"error": "Failed to retrieve asset", "details": str(e)}, status=500
        )




def _filter_sort_paginate_appraisals(entries, search=None, source_filter=None,
                                     status_filter=None, ordering='-date', limit=25,
                                     offset=0, allow_status=False):
    try:
        limit = max(1, min(int(limit), 100))
    except (TypeError, ValueError):
        limit = 25

    try:
        offset = max(0, int(offset))
    except (TypeError, ValueError):
        offset = 0

    search_lower = search.lower() if search else None
    filtered = []

    for entry in entries:
        source_value = (entry.get('source') or '').lower()
        if source_filter and source_filter != 'all' and source_value != source_filter.lower():
            continue

        if allow_status:
            status_value = (entry.get('status') or '').lower()
            if status_filter and status_filter != 'all' and status_value != status_filter.lower():
                continue

        if search_lower:
            values = [
                str(entry.get('appraiser') or ''),
                str(entry.get('date') or ''),
                str(entry.get('appraisedValue') or entry.get('marketValue') or entry.get('value') or ''),
                str(entry.get('source') or ''),
                str(entry.get('plan_number') or ''),
                str(entry.get('status') or ''),
            ]
            if not any(search_lower in value.lower() for value in values):
                continue

        filtered.append(entry)

    total_count = len(filtered)

    ordering_field = ordering or '-date'
    reverse = False
    if ordering_field.startswith('-'):
        reverse = True
        ordering_field = ordering_field[1:]

    def sort_key(item):
        if ordering_field == 'date':
            return _parse_date_value(item.get('date')) or datetime.min
        if ordering_field == 'appraiser':
            return (item.get('appraiser') or '').lower()
        if ordering_field == 'value':
            value = item.get('appraisedValue') or item.get('marketValue') or item.get('value')
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0
        if ordering_field == 'source':
            return (item.get('source') or '').lower()
        if ordering_field == 'plan_number':
            return (item.get('plan_number') or '').lower()
        if ordering_field == 'status':
            return (item.get('status') or '').lower()
        return _parse_date_value(item.get('date')) or datetime.min

    filtered.sort(key=sort_key, reverse=reverse)

    paginated = filtered[offset: offset + limit]

    filters_metadata = {
        'source': sorted({entry.get('source') for entry in entries if entry.get('source')})
    }
    if allow_status:
        filters_metadata['status'] = sorted({entry.get('status') for entry in entries if entry.get('status')})

    ordering_value = ordering if ordering else '-date'

    return paginated, total_count, filters_metadata, limit, offset, ordering_value


@csrf_exempt
def asset_appraisal(request, asset_id):
    """Get appraisal data for an asset including decisive appraisals and RAMI data."""
    if request.method != "GET":
        return JsonResponse({"error": "GET method required"}, status=405)

    try:
        try:
            asset = Asset.objects.get(id=asset_id)
        except Asset.DoesNotExist:
            return JsonResponse({"error": "Asset not found"}, status=404)

        appraisal_records = SourceRecord.objects.filter(
            asset_id=asset_id,
            source__in=['appraisal_decisive', 'appraisal_rmi', 'decisive', 'rami']
        )

        appraisal_data = {
            "appraisal": None,
            "decisive_appraisals": [],
            "rami_appraisals": [],
            "market_analysis": {},
            "asset_info": {
                "address": asset.address,
                "city": asset.city,
                "area": asset.area,
                "block": asset.block,
                "plot": asset.parcel
            }
        }

        decisive_entries = []
        rami_entries = []

        decisive_records = appraisal_records.filter(source__in=['appraisal_decisive', 'decisive'])
        for record in decisive_records:
            entry = {
                "id": record.id,
                "appraiser": None,
                "date": record.fetched_at.isoformat() if record.fetched_at else None,
                "appraisedValue": None,
                "url": record.url,
                "fetched_at": record.fetched_at.isoformat() if record.fetched_at else None,
                "source": (record.source or 'decisive').lower(),
            }
            if record.raw:
                try:
                    raw_data = json.loads(record.raw) if isinstance(record.raw, str) else record.raw
                except (json.JSONDecodeError, TypeError):
                    raw_data = {}
            else:
                raw_data = {}

            entry["appraiser"] = raw_data.get("appraiser", entry["appraiser"] or "לא זמין")
            entry["date"] = raw_data.get("date", entry["date"])
            entry["appraisedValue"] = raw_data.get("appraisedValue", raw_data.get("value", entry["appraisedValue"]))
            decisive_entries.append(entry)

        rami_records = appraisal_records.filter(source__in=['appraisal_rmi', 'rami'])
        for record in rami_records:
            entry = {
                "id": record.id,
                "date": record.fetched_at.isoformat() if record.fetched_at else None,
                "marketValue": None,
                "url": record.url,
                "fetched_at": record.fetched_at.isoformat() if record.fetched_at else None,
                "source": (record.source or 'rami').lower(),
            }
            if record.raw:
                try:
                    raw_data = json.loads(record.raw) if isinstance(record.raw, str) else record.raw
                except (json.JSONDecodeError, TypeError):
                    raw_data = {}
            else:
                raw_data = {}

            entry["date"] = raw_data.get("date", entry["date"])
            entry["marketValue"] = raw_data.get("marketValue", raw_data.get("value", entry["marketValue"]))
            rami_entries.append(entry)

        document_qs = Document.objects.filter(
            Q(asset_id=asset_id) | Q(assets__id=asset_id),
            document_type__in=['appraisal_decisive', 'appraisal', 'appraisal_rmi']
        ).distinct()

        for doc in document_qs:
            meta = doc.meta or {}
            base_entry = {
                "id": f"doc_{doc.id}",
                "appraiser": meta.get('appraiser') or doc.title,
                "date": doc.document_date.isoformat() if doc.document_date else meta.get('date'),
                "appraisedValue": meta.get('appraised_value') or meta.get('value'),
                "marketValue": meta.get('marketValue') or meta.get('value'),
                "url": doc.external_url or doc.file_url,
                "fetched_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "source": (doc.source or meta.get('source') or 'unknown').lower(),
                "plan_number": meta.get('planNumber') or meta.get('plan_number') or doc.external_id,
                "status": meta.get('status'),
            }

            doc_type = doc.document_type
            if doc_type == 'appraisal_decisive' or (doc_type == 'appraisal' and (doc.source and 'decisive' in doc.source.lower())):
                decisive_entries.append(base_entry.copy())
            elif doc_type in ['appraisal_rmi'] or (doc.source and 'ram' in doc.source.lower()):
                rami_entries.append(base_entry.copy())

        if asset.meta:
            decisive_appraisals = asset.get_property_value('government_data.decisive_appraisals', [])
            if decisive_appraisals:
                for appraisal in decisive_appraisals:
                    decisive_entries.append({
                        "id": f"collected_{appraisal.get('id', '')}",
                        "appraiser": appraisal.get('appraiser', 'לא זמין'),
                        "date": appraisal.get('date', ''),
                        "appraisedValue": appraisal.get('value'),
                        "url": appraisal.get('url'),
                        "fetched_at": appraisal.get('fetched_at'),
                        "source": (appraisal.get('source') or 'decisive').lower(),
                    })

            rami_plans = asset.get_property_value('government_data.rami_plans', [])
            if rami_plans:
                for plan in rami_plans:
                    if plan.get('marketValue') or plan.get('value'):
                        rami_entries.append({
                            "id": f"collected_rami_{plan.get('planNumber', plan.get('plan_number', ''))}",
                            "date": plan.get('status_date', plan.get('date', '')),
                            "marketValue": plan.get('marketValue', plan.get('value', None)),
                            "url": plan.get('url', ''),
                            "fetched_at": asset.get_property_value('last_enrichment'),
                            "source": 'rami',
                            "plan_number": plan.get('planNumber', plan.get('plan_number', '')),
                            "status": plan.get('status', ''),
                        })

        market_metrics = asset.get_property_value('market_metrics', {})
        if market_metrics:
            appraisal_data["market_analysis"].update({
                "model_price": market_metrics.get('modelPrice'),
                "price_gap_pct": market_metrics.get('priceGapPct'),
                "confidence_pct": market_metrics.get('confidencePct'),
                "expected_price_range": market_metrics.get('expectedPriceRange'),
                "competition_level": market_metrics.get('competition1km'),
                "risk_flags": market_metrics.get('riskFlags', [])
            })

        all_appraisals = decisive_entries + rami_entries
        if all_appraisals:
            sorted_appraisals = sorted(all_appraisals, key=lambda x: x.get("date", ""), reverse=True)
            appraisal_data["appraisal"] = sorted_appraisals[0]

        decisive_paged, decisive_total, decisive_filters, decisive_limit, decisive_offset, decisive_ordering = _filter_sort_paginate_appraisals(
            decisive_entries,
            search=request.GET.get('decisive_search'),
            source_filter=request.GET.get('decisive_source'),
            ordering=request.GET.get('decisive_ordering', '-date'),
            limit=request.GET.get('decisive_limit', 25),
            offset=request.GET.get('decisive_offset', 0),
            allow_status=False,
        )

        rami_paged, rami_total, rami_filters, rami_limit, rami_offset, rami_ordering = _filter_sort_paginate_appraisals(
            rami_entries,
            search=request.GET.get('rami_search'),
            source_filter=request.GET.get('rami_source'),
            status_filter=request.GET.get('rami_status'),
            ordering=request.GET.get('rami_ordering', '-date'),
            limit=request.GET.get('rami_limit', 25),
            offset=request.GET.get('rami_offset', 0),
            allow_status=True,
        )

        appraisal_data["decisive_appraisals"] = decisive_paged
        appraisal_data["decisive_count"] = decisive_total
        appraisal_data["decisive_filters"] = decisive_filters
        appraisal_data["decisive_limit"] = decisive_limit
        appraisal_data["decisive_offset"] = decisive_offset
        appraisal_data["decisive_ordering"] = decisive_ordering

        appraisal_data["rami_appraisals"] = rami_paged
        appraisal_data["rami_count"] = rami_total
        appraisal_data["rami_filters"] = rami_filters
        appraisal_data["rami_limit"] = rami_limit
        appraisal_data["rami_offset"] = rami_offset
        appraisal_data["rami_ordering"] = rami_ordering

        return JsonResponse(appraisal_data)

    except Exception as e:
        logger.error("Error retrieving appraisal data for asset %s: %s", asset_id, e)
        return JsonResponse(
            {"error": "Failed to retrieve appraisal data", "details": str(e)}, status=500
        )
@csrf_exempt
def asset_transactions(request, asset_id):
    """Get comparable transactions for an asset."""
    if request.method != "GET":
        return JsonResponse({"error": "GET method required"}, status=405)

    try:
        # Get asset
        try:
            asset = Asset.objects.get(id=asset_id)
        except Asset.DoesNotExist:
            return JsonResponse({"error": "Asset not found"}, status=404)

        try:
            limit = max(1, min(int(request.GET.get("limit", 25)), 100))
        except (TypeError, ValueError):
            limit = 25

        try:
            offset = max(0, int(request.GET.get("offset", 0)))
        except (TypeError, ValueError):
            offset = 0

        search_query = (request.GET.get("search") or "").strip()
        source_filter = (request.GET.get("source") or "").strip()
        area_filter = (request.GET.get("area") or "").strip()
        ordering_param = request.GET.get("ordering", "-date")

        # Get transactions for comparable analysis
        # Always include transactions directly linked to this asset
        # Additionally include transactions from the same neighborhood if available
        transaction_filters = Q(asset_id=asset_id) | Q(assets__id=asset_id)
        
        # Check for transactions matching by city (from GovMap deals)
        # GovMap deals have neighborhood and settlementNameHeb in their raw data
        if asset.city:
            city_name = asset.city.strip()
            if asset.neighborhood:
                neighborhood_name = asset.neighborhood.strip()
                transaction_filters |= (
                    Q(asset__neighborhood=neighborhood_name, asset__city=city_name)
                    | Q(assets__neighborhood=neighborhood_name, assets__city=city_name)
                    | Q(raw__neighborhood=neighborhood_name)
                )
            
            # Also match by city in linked assets
            transaction_filters |= (
                Q(asset__city=city_name) | Q(assets__city=city_name)
            )
            
            # If we have a street, also match by street name in address
            if asset.street:
                street_name = asset.street.strip()
                transaction_filters |= (
                    Q(address__icontains=street_name) |
                    Q(asset__street=street_name, asset__city=city_name) |
                    Q(assets__street=street_name, assets__city=city_name)
                    | Q(raw__streetNameHeb__icontains=street_name)
                )
        
        transactions = RealEstateTransaction.objects.filter(transaction_filters).distinct()

        transactions = transactions.annotate(
            price_per_sqm=Case(
                When(
                    price__isnull=False,
                    area__isnull=False,
                    area__gt=0,
                    then=ExpressionWrapper(
                        F("price") * 1.0 / F("area"),
                        output_field=FloatField(),
                    ),
                ),
                default=Value(None),
                output_field=FloatField(),
            ),
            source_value=Case(
                When(raw__source__isnull=False, then=F("raw__source")),
                When(raw__sourceType__isnull=False, then=F("raw__sourceType")),
                When(raw__source_type__isnull=False, then=F("raw__source_type")),
                When(raw__data_source__isnull=False, then=F("raw__data_source")),
                default=Value("government"),
                output_field=CharField(),
            ),
        )

        if source_filter and source_filter.lower() != "all":
            transactions = transactions.filter(source_value=source_filter)

        if search_query:
            transactions = transactions.filter(
                Q(address__icontains=search_query)
                | Q(deal_id__icontains=search_query)
                | Q(raw__parcel_block__icontains=search_query)
                | Q(raw__parcel_parcel__icontains=search_query)
                | Q(raw__parcel_sub_parcel__icontains=search_query)
            )

        if area_filter and area_filter.lower() != "all":
            if area_filter.endswith("+"):
                try:
                    min_area = float(area_filter[:-1])
                    transactions = transactions.filter(area__gte=min_area)
                except ValueError:
                    pass
            else:
                min_max = area_filter.split("-")
                if len(min_max) == 2:
                    try:
                        min_area = float(min_max[0])
                        max_area = float(min_max[1])
                        transactions = transactions.filter(
                            area__gte=min_area,
                            area__lte=max_area,
                        )
                    except ValueError:
                        pass

        ordering_field = ordering_param.lstrip("-")
        ordering_map = {
            "date": "date",
            "price": "price",
            "price_per_sqm": "price_per_sqm",
            "area": "area",
            "rooms": "rooms",
            "address": "address",
            "source": "source_value",
        }
        resolved_field = ordering_map.get(ordering_field, "date")
        ordering_prefix = "-" if ordering_param.startswith("-") else ""
        resolved_ordering = f"{ordering_prefix}{resolved_field}"
        transactions = transactions.order_by(resolved_ordering, "-id")

        total_count = transactions.count()
        paginated_transactions = list(transactions[offset : offset + limit])

        # Build market analysis from the filtered result set (before pagination)
        market_analysis = {}
        if total_count:
            price_stats = transactions.aggregate(
                avg_price=Avg("price"),
                min_price=Min("price"),
                max_price=Max("price"),
                avg_ppsqm=Avg("price_per_sqm"),
                min_ppsqm=Min("price_per_sqm"),
                max_ppsqm=Max("price_per_sqm"),
            )

            prices = list(
                transactions.filter(price__isnull=False)
                .order_by("price")
                .values_list("price", flat=True)
            )

            if prices:
                mid = len(prices) // 2
                if len(prices) % 2:
                    median_price = prices[mid]
                else:
                    median_price = (prices[mid - 1] + prices[mid]) / 2
            else:
                median_price = None

            def _coerce(value):
                if value is None:
                    return None
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return None

            market_analysis = {
                "avg_price": _coerce(price_stats.get("avg_price")),
                "min_price": _coerce(price_stats.get("min_price")),
                "max_price": _coerce(price_stats.get("max_price")),
                "median_price": _coerce(median_price),
                "transaction_count": len(prices),
            }

            market_analysis.update(
                {
                    "avg_price_per_sqm": _coerce(price_stats.get("avg_ppsqm")),
                    "min_price_per_sqm": _coerce(price_stats.get("min_ppsqm")),
                    "max_price_per_sqm": _coerce(price_stats.get("max_ppsqm")),
                }
            )

        transactions_list = []
        for trans in paginated_transactions:
            price_per_sqm = trans.price_per_sqm
            if price_per_sqm is not None:
                try:
                    price_per_sqm = round(float(price_per_sqm))
                except (TypeError, ValueError):
                    price_per_sqm = None

            transactions_list.append(
                {
                    "id": trans.id,
                    "date": trans.date.isoformat() if trans.date else None,
                    "price": trans.price,
                    "rooms": trans.rooms,
                    "area": trans.area,
                    "floor": trans.floor,
                    "address": trans.address,
                    "price_per_sqm": price_per_sqm,
                    "deal_id": trans.deal_id,
                    "source": trans.source_value or "government",
                }
            )

        available_sources = (
            transactions.values_list("source_value", flat=True)
            .order_by("source_value")
            .distinct()
        )

        area_stats = transactions.aggregate(
            min_area=Min("area"),
            max_area=Max("area"),
        )

        min_area = area_stats.get("min_area")
        max_area = area_stats.get("max_area")

        area_filters = []
        if min_area is not None and max_area is not None:
            predefined_ranges = [
                ("0", "50"),
                ("50", "100"),
                ("100", "150"),
                ("150", "200"),
            ]
            for start, end in predefined_ranges:
                start_val = float(start)
                end_val = float(end)
                if max_area < start_val or min_area > end_val:
                    continue
                area_filters.append(f"{start}-{end}")
            if max_area > 200:
                area_filters.append("200+")

        transaction_data = {
            "transactions": transactions_list,
            "market_analysis": market_analysis,
            "asset_info": {
                "address": asset.address,
                "city": asset.city,
                "area": asset.area,
                "block": asset.block,
                "plot": asset.parcel,
            },
            "count": total_count,
            "limit": limit,
            "offset": offset,
            "ordering": resolved_ordering,
            "filters": {
                "source": [value for value in available_sources if value],
                "area": area_filters,
            },
        }
        return JsonResponse(transaction_data)

    except Exception as e:
        logger.error("Error retrieving transaction data for asset %s: %s", asset_id, e)
        return JsonResponse(
            {"error": "Failed to retrieve transaction data", "details": str(e)}, status=500
        )


def _first_non_empty(*values):
    """Return the first non-empty string representation from the provided values."""
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
        else:
            stringified = str(value).strip()
            if stringified:
                return stringified
    return ""


def _parse_date_value(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
            numeric = int(value)
            if numeric > 1e12:
                numeric = numeric / 1000
            return datetime.fromtimestamp(numeric)
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except Exception:
        return None
    return None


def _format_date_value(value):
    parsed = _parse_date_value(value)
    if not parsed:
        return None
    return parsed.strftime('%Y-%m-%d')


def _normalize_permit(serializer_data):
    meta = serializer_data.get('meta') or {}

    permit_number = _first_non_empty(
        meta.get('permit_number'),
        meta.get('permission_num'),
        meta.get('TlvMPEngPermitNum'),
        serializer_data.get('external_id'),
    )

    request_number = _first_non_empty(
        meta.get('request_num'),
        meta.get('TlvMPEngRequestNum'),
        meta.get('TlvMPEngOnlineReqNum'),
    )

    addresses = _first_non_empty(
        meta.get('addresses'),
        meta.get('address'),
    )

    description = _first_non_empty(
        meta.get('tochen_bakasha'),
        meta.get('description'),
        serializer_data.get('description'),
        serializer_data.get('title'),
    )

    building_stage = _first_non_empty(
        meta.get('building_stage'),
        meta.get('stage'),
        serializer_data.get('status'),
    )

    status = _first_non_empty(
        serializer_data.get('status'),
        meta.get('status'),
        building_stage,
    )

    approval_date = _format_date_value(
        meta.get('permission_date')
        or meta.get('document_date')
        or serializer_data.get('document_date')
        or meta.get('TlvMPEngDocDate')
    )

    expiry_date = _format_date_value(
        meta.get('expiry_date')
        or meta.get('expiration_date')
        or meta.get('license_exp_date')
        or meta.get('valid_until')
        or meta.get('valid_till')
    )

    issue_date = _format_date_value(
        meta.get('open_request')
        or meta.get('issue_date')
        or meta.get('license_issue_date')
    )

    handasa_link = _first_non_empty(
        meta.get('url_hadmaya'),
        meta.get('Path'),
        meta.get('DocumentLink'),
        serializer_data.get('external_url'),
    )

    document_type = _first_non_empty(
        meta.get('handasa_document_type'),
        meta.get('TlvMPEngDocumentType'),
        meta.get('document_type'),
        serializer_data.get('document_type'),
    )

    request_type = _first_non_empty(
        meta.get('sug_bakasha'),
        meta.get('request_type'),
    )

    external_id = _first_non_empty(
        serializer_data.get('external_id'),
        meta.get('external_id'),
        meta.get('id'),
        serializer_data.get('id'),
    )

    source = _first_non_empty(serializer_data.get('source'), meta.get('source'))
    external_url = serializer_data.get('external_url')

    title = _first_non_empty(
        serializer_data.get('title'),
        description,
        document_type,
        permit_number,
        request_number,
    )

    search_values = list(
        filter(
            None,
            [
                title,
                description,
                addresses,
                permit_number,
                request_number,
                building_stage,
                document_type,
                request_type,
                source,
                approval_date,
                expiry_date,
                issue_date,
                status,
                external_id,
            ],
        )
    )

    return {
        'id': serializer_data.get('id'),
        'external_id': external_id,
        'title': title,
        'description': description,
        'addresses': addresses,
        'permitNumber': permit_number,
        'requestNumber': request_number,
        'stage': building_stage,
        'status': status,
        'documentType': document_type,
        'requestType': request_type,
        'approvalDate': approval_date,
        'issueDate': issue_date,
        'expiryDate': expiry_date,
        'handasaLink': handasa_link,
        'externalUrl': external_url,
        'external_url': external_url,
        'source': source,
        'meta': meta,
        'searchValues': search_values,
        'raw': serializer_data,
    }

@csrf_exempt
def asset_permits(request, asset_id):
    """Get building permits for an asset from Document model."""
    if request.method != "GET":
        return JsonResponse({"error": "GET method required"}, status=405)

    try:
        # Get asset
        try:
            asset = Asset.objects.get(id=asset_id)
        except Asset.DoesNotExist:
            return JsonResponse({"error": "Asset not found"}, status=404)

        try:
            limit = max(1, min(int(request.GET.get('limit', 25)), 100))
        except ValueError:
            limit = 25

        try:
            offset = max(0, int(request.GET.get('offset', 0)))
        except ValueError:
            offset = 0

        search_query = request.GET.get('search')
        stage_filter = request.GET.get('stage')
        document_type_filter = request.GET.get('document_type')
        source_filter = request.GET.get('source')
        ordering_param = request.GET.get('ordering', '-approval_date')

        # Get permits from Document model (single source of truth)
        permit_documents = (
            Document.objects.filter(
                Q(asset_id=asset_id) | Q(assets__id=asset_id),
                document_type='permit'
            )
            .select_related('asset')
            .prefetch_related('assets')
            .distinct()
            .order_by('-document_date', '-uploaded_at')
        )

        normalized_permits = []
        for doc in permit_documents:
            serializer = DocumentSerializer(doc)
            normalized = _normalize_permit(serializer.data)

            if stage_filter and stage_filter != 'all':
                if (normalized.get('stage') or '').lower() != stage_filter.lower():
                    continue

            if document_type_filter and document_type_filter != 'all':
                if (normalized.get('documentType') or '').lower() != document_type_filter.lower():
                    continue

            if source_filter and source_filter != 'all':
                if (normalized.get('source') or '').lower() != source_filter.lower():
                    continue

            if search_query:
                search_lower = search_query.lower()
                if not any(value.lower().find(search_lower) != -1 for value in normalized.get('searchValues', [])):
                    continue

            normalized_permits.append(normalized)

        total_count = len(normalized_permits)

        # Sorting
        ordering_field = ordering_param
        reverse = False
        if ordering_field.startswith('-'):
            reverse = True
            ordering_field = ordering_field[1:]

        def sort_key(item):
            if ordering_field == 'approval_date':
                return _parse_date_value(item.get('approvalDate')) or datetime.min
            if ordering_field == 'issue_date':
                return _parse_date_value(item.get('issueDate')) or datetime.min
            if ordering_field == 'expiry_date':
                return _parse_date_value(item.get('expiryDate')) or datetime.min
            if ordering_field == 'permit_number':
                return item.get('permitNumber') or ''
            if ordering_field == 'request_number':
                return item.get('requestNumber') or ''
            if ordering_field == 'stage':
                return item.get('stage') or ''
            if ordering_field == 'document_type':
                return item.get('documentType') or ''
            if ordering_field == 'source':
                return item.get('source') or ''
            if ordering_field == 'title':
                return item.get('title') or ''
            return _parse_date_value(item.get('approvalDate')) or datetime.min

        normalized_permits.sort(key=sort_key, reverse=reverse)

        paginated_permits = normalized_permits[offset: offset + limit]

        filters_metadata = {
            'stage': sorted({item.get('stage') for item in normalized_permits if item.get('stage')}),
            'document_type': sorted({item.get('documentType') for item in normalized_permits if item.get('documentType')}),
            'source': sorted({item.get('source') for item in normalized_permits if item.get('source')}),
        }

        return JsonResponse({
            "permits": paginated_permits,
            "count": total_count,
            "limit": limit,
            "offset": offset,
            "ordering": ordering_param,
            "filters": filters_metadata,
        })

    except Exception as e:
        logger.error("Error retrieving permits for asset %s: %s", asset_id, e)
        return JsonResponse(
            {"error": "Failed to retrieve permits", "details": str(e)}, status=500
        )


def _canonical_plan_number(value):
    """Normalize plan numbers for deduplication by removing whitespace and quotes."""
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    cleaned = re.sub(r'\s+', '', value).replace('"', '').replace("'", '')
    return cleaned or None


def _canonical_plan_title(value):
    """Normalize plan titles for fallback deduplication (case/spacing insensitive)."""
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    cleaned = re.sub(r'\s+', ' ', value).strip().lower()
    return cleaned or None


def _translate_plan_status(status: Optional[str]) -> Optional[str]:
    """Convert internal English status labels into Hebrew display strings."""
    if not status:
        return status
    normalized = str(status).strip().lower()
    translations = {
        "approved": "מאושר",
        "pending": "בתהליך",
        "draft": "טיוטה",
        "cancelled": "מבוטלת",
        "canceled": "מבוטלת",
        "rejected": "נדחתה",
        "submitted": "הוגשה",
        "in_review": "בבחינה",
        "in review": "בבחינה",
        "published": "פורסמה",
        "mixed": "מעורב",
        "unknown": "לא ידוע",
    }
    return translations.get(normalized, status)


def _merge_plan_entries(entries):
    """Merge plan rows representing the same plan (based on number/title) across sources."""
    merged = {}
    for entry in entries:
        canonical_number = _canonical_plan_number(entry.get("plan_number"))
        canonical_title = _canonical_plan_title(entry.get("title") or entry.get("description"))
        key = canonical_number or canonical_title or f"__missing__:{entry.get('id')}"

        if key not in merged:
            merged_entry = dict(entry)
            merged_entry["search_values"] = list(entry.get("search_values", []))
            initial_source = merged_entry.get("source")
            merged_entry["sources"] = [initial_source] if initial_source else []
            merged[key] = merged_entry
            continue

        existing = merged[key]
        incoming_source = entry.get("source")
        existing_sources = existing.get("sources") or []
        if incoming_source and incoming_source not in existing_sources:
            sources = set(filter(None, existing_sources))
            existing_source_value = existing.get("source")
            if existing_source_value and existing_source_value != "mixed":
                sources.add(existing_source_value)
            sources.add(incoming_source)
            combined_sources = sorted(sources)
            existing["sources"] = combined_sources

            meaningful_sources = [s for s in combined_sources if s.lower() != "unknown"]
            if len(meaningful_sources) == 1:
                existing["source"] = meaningful_sources[0]
            elif len(meaningful_sources) > 1:
                existing["source"] = "mixed"
            else:
                existing["source"] = combined_sources[0] if combined_sources else existing.get("source")

        for field in ("title", "description", "status", "effective_date", "file_url"):
            if not existing.get(field) and entry.get(field):
                existing[field] = entry.get(field)

        existing_search = existing.get("search_values") or []
        incoming_search = entry.get("search_values") or []
        if incoming_search:
            existing["search_values"] = list(dict.fromkeys(existing_search + incoming_search))

        if not existing.get("raw") and entry.get("raw"):
            existing["raw"] = entry.get("raw")

    return list(merged.values())


def _normalize_plan_entry(entry):
    plan_number = _first_non_empty(
        entry.get("plan_number"),
        entry.get("planNumber"),
        entry.get("plan_id"),
    )

    title = _first_non_empty(
        entry.get("title"),
        entry.get("name"),
        entry.get("plan_name"),
        entry.get("planTitle"),
    )

    description = _first_non_empty(
        entry.get("description"),
        entry.get("summary"),
        title,
    )

    status = _first_non_empty(entry.get("status"))
    status = _translate_plan_status(status)
    effective_date = _format_date_value(
        entry.get("effective_date")
        or entry.get("status_date")
        or entry.get("date")
        or entry.get("published_at")
    )

    source = (entry.get("source") or "unknown").lower()

    search_values = list(
        filter(
            None,
            [
                plan_number,
                title,
                description,
                status,
                source,
                effective_date,
            ],
        )
    )

    return {
        "id": entry.get("id"),
        "plan_number": plan_number,
        "title": title,
        "description": description,
        "status": status,
        "effective_date": effective_date,
        "file_url": entry.get("file_url"),
        "source": source,
        "raw": entry.get("raw") or entry,
        "search_values": search_values,
    }


@csrf_exempt
def asset_plans(request, asset_id):
    """Get planning documents for an asset from collected data."""
    if request.method != "GET":
        return JsonResponse({"error": "GET method required"}, status=405)

    try:
        try:
            asset = Asset.objects.get(id=asset_id)
        except Asset.DoesNotExist:
            return JsonResponse({"error": "Asset not found"}, status=404)

        try:
            limit = max(1, min(int(request.GET.get('limit', 25)), 100))
        except (TypeError, ValueError):
            limit = 25

        try:
            offset = max(0, int(request.GET.get('offset', 0)))
        except (TypeError, ValueError):
            offset = 0

        search_query = request.GET.get('search')
        source_filter = request.GET.get('source')
        status_filter = request.GET.get('status')
        ordering_param = request.GET.get('ordering', '-effective_date')

        plan_entries = []

        local_plans = Plan.objects.filter(
            Q(asset_id=asset_id) | Q(assets__id=asset_id)
        ).distinct()
        for plan in local_plans:
            plan_raw = plan.raw or {}
            raw_source = str(plan_raw.get('source') or '').lower()
            source = 'unknown'
            if plan_raw.get('planNumber'):
                source = 'rami'
            elif raw_source == 'mavat' or plan_raw.get('plan_id'):
                source = 'mavat'
            elif raw_source:
                source = raw_source
            elif plan_raw.get('url_documents'):
                source = 'gis'

            normalized_entry = _normalize_plan_entry({
                "id": plan.id,
                "plan_number": plan.plan_number,
                "title": plan.title,
                "description": plan.description,
                "status": plan.status,
                "effective_date": plan.effective_date.isoformat() if plan.effective_date else None,
                "file_url": plan.file_url,
                "source": source,
                "raw": plan.raw,
            })
            plan_entries.append(normalized_entry)

        plan_documents = Document.objects.filter(
            Q(asset_id=asset_id) | Q(assets__id=asset_id),
            document_type__in=['plan', 'plan_local', 'plan_citywide', 'plan_detailed']
        ).distinct()

        for doc in plan_documents:
            meta = doc.meta or {}
            meta_plan_number = meta.get('planNumber') or meta.get('plan_number')
            fallback_number = doc.external_id or f"document_{doc.id}"
            display_plan_number = meta_plan_number or fallback_number
            source = 'unknown'
            raw_source = (doc.source or '').lower()
            meta_source = (meta.get('source') or '').lower()
            if 'rami' in raw_source or 'rami' in meta_source:
                source = 'rami'
            elif 'mavat' in raw_source or meta_source == 'mavat':
                source = 'mavat'
            elif 'gis' in raw_source or meta.get('url_documents'):
                source = 'gis'

            plan_entries.append(_normalize_plan_entry({
                "id": doc.id,
                "plan_number": display_plan_number,
                "planNumber": fallback_number,
                "title": doc.title or doc.description,
                "description": doc.description or doc.title,
                "status": doc.status,
                "effective_date": doc.document_date.isoformat() if doc.document_date else None,
                "file_url": doc.external_url or doc.file_url,
                "source": source,
                "raw": meta,
            }))

        plan_entries = _merge_plan_entries(plan_entries)

        # Allow filtering/searching
        filtered_plans = []
        search_lower = search_query.lower() if search_query else None
        for entry in plan_entries:
            if source_filter and source_filter != 'all':
                entry_sources = entry.get('sources') or []
                candidate_sources = set()
                candidate_sources.update(s.lower() for s in entry_sources if isinstance(s, str))
                source_single = entry.get('source')
                if source_single:
                    candidate_sources.add(source_single.lower())
                if source_filter.lower() not in candidate_sources:
                    continue

            if status_filter and status_filter != 'all':
                if (entry.get('status') or '').lower() != status_filter.lower():
                    continue

            if search_lower:
                values = entry.get('search_values', [])
                if not any((v or '').lower().find(search_lower) != -1 for v in values):
                    continue

            filtered_plans.append(entry)

        total_count = len(filtered_plans)

        ordering_field = ordering_param
        reverse = False
        if ordering_field.startswith('-'):
            reverse = True
            ordering_field = ordering_field[1:]

        def plan_sort_key(item):
            if ordering_field == 'effective_date':
                return _parse_date_value(item.get('effective_date')) or datetime.min
            if ordering_field == 'plan_number':
                return item.get('plan_number') or ''
            if ordering_field == 'title':
                return item.get('title') or ''
            if ordering_field == 'status':
                return item.get('status') or ''
            if ordering_field == 'source':
                return item.get('source') or ''
            if ordering_field == 'description':
                return item.get('description') or ''
            return _parse_date_value(item.get('effective_date')) or datetime.min

        filtered_plans.sort(key=plan_sort_key, reverse=reverse)

        paginated_plans = filtered_plans[offset: offset + limit]

        source_values: set[str] = set()
        status_values: set[str] = set()
        for item in plan_entries:
            sources_list = item.get('sources') or []
            for s in sources_list:
                if s:
                    source_values.add(s)
            source_single = item.get('source')
            if source_single:
                source_values.add(source_single)
            status = item.get('status')
            if status:
                status_values.add(status)

        filters_metadata = {
            'source': sorted(source_values),
            'status': sorted(status_values),
        }

        return JsonResponse({
            "plans": paginated_plans,
            "count": total_count,
            "limit": limit,
            "offset": offset,
            "ordering": ordering_param,
            "filters": filters_metadata,
        })

    except Exception as e:
        logger.error("Error retrieving plans for asset %s: %s", asset_id, e)
        return JsonResponse(
            {"error": "Failed to retrieve plans", "details": str(e)}, status=500
        )



@api_view(["POST"])
@permission_classes([AllowAny])
def asset_share_message(request, asset_id):
    """Generate a marketing message for an asset using LLM."""
    try:
        asset = Asset.objects.get(id=asset_id)
    except Asset.DoesNotExist:
        return Response({"error": "Asset not found"}, status=status.HTTP_404_NOT_FOUND)

    # Read language from request, default to Hebrew
    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except json.JSONDecodeError:
        data = {}

    language_code = data.get("language", "he").lower()
    supported = {
        "he": "Hebrew",
        "en": "English",
        "ru": "Russian",
        "fr": "French",
        "es": "Spanish",
        "ar": "Arabic",
    }
    language = supported.get(language_code, "Hebrew")

    srcs = SourceRecord.objects.filter(asset_id=asset.id).order_by("-fetched_at")
    listing = build_listing(asset, srcs)
    keys_to_remove = [
        "location_hint",
        "handasa_archive",
        "gis_collector_data",
        "gisCoordinates",
        "govmap_autocomplete_data",
        "govmap_data",
        "_meta",
    ]
    for key in keys_to_remove:
        if key in listing:
            del listing[key]

    logger.info(
        "Generating marketing message for asset %s in %s",
        asset_id,
        language,
    )

    data_json = json.dumps(listing, ensure_ascii=False)
    prompt = (
        "Create an engaging {} marketing message for social media and messaging apps about a property for sale. "
        "Use this data:\n{}\n".format(language, data_json)
    )

    message = None
    is_ai_generated = False
    try:
        llm = get_llm(request)
        options = BaseGenOptions(temperature=0.2)
        system_prompt = (
            "You write short real estate marketing messages in {}.".format(language)
        )
        payload = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=prompt),
        ]
        result = async_to_sync(llm.chat)(payload, options)
        if isinstance(result, str):
            message = result.strip() or None
            if message:
                is_ai_generated = True
    except Exception as e:
        logger.exception(
            "Error generating marketing message for asset %s: %s", asset_id, e
        )
        message = None

    if not message:
        addr = listing.get("address") or ""
        price = listing.get("price")
        rooms = listing.get("rooms")
        area = listing.get("netSqm")
        price_s = " במחיר {:,}₪".format(price) if price else ""
        rooms_s = "{} חדרים".format(int(rooms)) if rooms else "דירה"
        area_s = ' {} מ"ר'.format(int(area)) if area else ""
        message = "למכירה {}{} ב{}{}.".format(rooms_s, area_s, addr, price_s)
        is_ai_generated = False

    logger.info("Marketing message generated for asset %s: AI-generated: %s", asset_id, is_ai_generated)

    token = secrets.token_urlsafe(16)
    ShareToken.objects.create(asset=asset, token=token)
    share_url = "/r/{}".format(token)

    response_data = {"text": message, "share_url": share_url, "is_ai_generated": is_ai_generated}

    return Response(response_data)


@api_view(["GET"])
@permission_classes([AllowAny])
def asset_share_read_only(request, token):
    """Render a read-only view of an asset for sharing."""
    from django.utils import timezone

    try:
        share = ShareToken.objects.select_related("asset").get(token=token)
        if share.expires_at and share.expires_at < timezone.now():
            raise ShareToken.DoesNotExist
    except ShareToken.DoesNotExist:
        return Response(
            {"error": "Invalid or expired token"}, status=status.HTTP_404_NOT_FOUND
        )

    asset = share.asset
    address = " ".join(
        filter(None, [asset.street, str(asset.number or ""), asset.city])
    )
    context = {
        "asset": {
            "address": address,
            "price": asset.price,
            "rooms": asset.rooms,
            "area": asset.area,
            "neighborhood": asset.neighborhood,
        }
    }
    return render(request, "share_asset.html", context)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change user password endpoint."""
    try:
        data = json.loads(request.body.decode("utf-8"))
        current_password = data.get("current_password")
        new_password = data.get("new_password")

        if not current_password or not new_password:
            return Response(
                {"error": "Current password and new password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(new_password) < 8:
            return Response(
                {"error": "New password must be at least 8 characters long"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify current password
        user = request.user
        if not user.check_password(current_password):
            return Response(
                {"error": "Current password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if new password is different from current
        if user.check_password(new_password):
            return Response(
                {"error": "New password must be different from current password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update password
        user.set_password(new_password)
        user.save()

        return Response({"message": "Password changed successfully"})

    except json.JSONDecodeError:
        return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Alert views
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def alert_rules(request):
    """Handle alert rules - GET (list) or POST (create)."""
    if request.method == "GET":
        rules = AlertRule.objects.filter(user=request.user).order_by("-created_at")
        serializer = AlertRuleSerializer(rules, many=True)
        return Response({"rules": serializer.data})
    
    if request.method == "POST":
        data = parse_json(request)
        if not data:
            return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = AlertRuleSerializer(data=data)
        if serializer.is_valid():
            # Save with user from request - pass user object to save method
            serializer.save(user=request.user)
            _update_onboarding(request.user, "set_one_alert")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def alert_rule_detail(request, rule_id):
    """Handle individual alert rule - GET, PATCH, or DELETE."""
    try:
        rule = AlertRule.objects.get(id=rule_id, user=request.user)
    except AlertRule.DoesNotExist:
        return Response({"error": "Alert rule not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == "GET":
        serializer = AlertRuleSerializer(rule)
        return Response(serializer.data)
    
    if request.method == "PATCH":
        data = parse_json(request)
        if not data:
            return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = AlertRuleSerializer(rule, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == "DELETE":
        rule.delete()
        return Response({"message": "Alert rule deleted successfully"}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def alert_events(request):
    """Get alert events for the current user."""
    since = request.GET.get('since')
    events = AlertEvent.objects.filter(alert_rule__user=request.user)
    
    if since:
        try:
            since_dt = timezone.datetime.fromisoformat(since.replace('Z', '+00:00'))
            events = events.filter(occurred_at__gte=since_dt)
        except ValueError:
            return Response({"error": "Invalid since parameter"}, status=status.HTTP_400_BAD_REQUEST)
    
    events = events.order_by('-occurred_at')[:100]  # Limit to 100 most recent
    serializer = AlertEventSerializer(events, many=True)
    return Response({"events": serializer.data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def alert_test(request):
    """Send a test alert to verify channels are working."""
    
    user = request.user
    channels = []
    
    if getattr(user, 'notify_email', False) and user.email:
        from orchestration.alerts import EmailAlert
        channels.append(EmailAlert(user.email))
    
    if getattr(user, 'notify_whatsapp', False) and getattr(user, 'phone', None):
        from orchestration.alerts import WhatsAppAlert
        channels.append(WhatsAppAlert(user.phone))
    
    if not channels:
        return Response({"error": "No notification channels configured"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Send test message
    test_message = "נדלנר: זהו הודעת בדיקה. הערוצים שלך מוגדרים כראוי."
    
    try:
        for channel in channels:
            channel.send(test_message)
        
        return Response({"message": "Test alert sent successfully"}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error("Failed to send test alert: %s", e)
        return Response({"error": "Failed to send test alert"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Attribution API endpoints
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def asset_contributions(request, asset_id):
    """Get all contributions for a specific asset."""
    try:
        asset = Asset.objects.get(id=asset_id)
        contributions = AssetContribution.objects.filter(asset=asset).order_by('-created_at')
        serializer = AssetContributionSerializer(contributions, many=True)
        return Response({"contributions": serializer.data})
    except Asset.DoesNotExist:
        return Response({"error": "Asset not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error("Error fetching asset contributions: %s", e)
        return Response({"error": "Failed to fetch contributions"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_contributions(request):
    """Get all contributions made by the current user."""
    try:
        contributions = AssetContribution.objects.filter(user=request.user).order_by('-created_at')
        serializer = AssetContributionSerializer(contributions, many=True)
        return Response({"contributions": serializer.data})
    except Exception as e:
        logger.error("Error fetching user contributions: %s", e)
        return Response({"error": "Failed to fetch contributions"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get or create user profile with contribution statistics."""
    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response({"profile": serializer.data})
    except Exception as e:
        logger.error("Error fetching user profile: %s", e)
        return Response({"error": "Failed to fetch profile"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    """Update user profile preferences."""
    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({"profile": serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error("Error updating user profile: %s", e)
        return Response({"error": "Failed to update profile"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def top_contributors(request):
    """Get top contributors by various metrics."""
    try:
        # Get top contributors by assets created
        top_creators = UserProfile.objects.filter(
            assets_created__gt=0,
            public_profile=True
        ).order_by('-assets_created')[:10]
        
        # Get top contributors by total contributions
        top_contributors = UserProfile.objects.filter(
            contributions_made__gt=0,
            public_profile=True
        ).order_by('-contributions_made')[:10]
        
        # Get top contributors by reputation
        top_reputation = UserProfile.objects.filter(
            reputation_score__gt=0,
            public_profile=True
        ).order_by('-reputation_score')[:10]
        
        creators_serializer = UserProfileSerializer(top_creators, many=True)
        contributors_serializer = UserProfileSerializer(top_contributors, many=True)
        reputation_serializer = UserProfileSerializer(top_reputation, many=True)
        
        return Response({
            "top_creators": creators_serializer.data,
            "top_contributors": contributors_serializer.data,
            "top_reputation": reputation_serializer.data
        })
    except Exception as e:
        logger.error("Error fetching top contributors: %s", e)
        return Response({"error": "Failed to fetch top contributors"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_contribution(request, asset_id):
    """Add a new contribution to an asset."""
    try:
        asset = Asset.objects.get(id=asset_id)
        data = request.data.copy()
        data['asset'] = asset_id
        data['user'] = request.user.id
        
        serializer = AssetContributionSerializer(data=data)
        if serializer.is_valid():
            contribution = serializer.save()
            
            # Update asset's last_updated_by
            asset.last_updated_by = request.user
            asset.save(update_fields=['last_updated_by'])
            
            # Update user profile stats
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.update_contribution_stats(contribution.contribution_type)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Asset.DoesNotExist:
        return Response({"error": "Asset not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error("Error adding contribution: %s", e)
        return Response({"error": "Failed to add contribution"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_plan_info(request):
    """Get current user's plan information."""
    try:
        from .plan_service import PlanService
        plan_info = PlanService.get_user_plan_info(request.user)
        serializer = UserPlanInfoSerializer(plan_info)
        return Response(serializer.data)
    except Exception as e:
        logger.error("Error getting plan info for user {}: {}".format(request.user.email, e))
        return Response({"error": "Failed to get plan information"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([AllowAny])
def plan_types(request):
    """Get all available plan types."""
    try:
        from .models import PlanType
        plans = PlanType.objects.filter(is_active=True).order_by('price')
        serializer = PlanTypeSerializer(plans, many=True)
        return Response({"plans": serializer.data})
    except Exception as e:
        logger.error("Error getting plan types: {}".format(e))
        return Response({"error": "Failed to get plan types"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upgrade_plan(request):
    """Upgrade user to a new plan."""
    try:
        data = parse_json(request)
        if not data or not data.get("plan_name"):
            return Response({"error": "plan_name is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        from .plan_service import PlanService, PlanValidationError
        new_plan = PlanService.upgrade_user_plan(request.user, data["plan_name"])
        serializer = UserPlanSerializer(new_plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except PlanValidationError as e:
        logger.warning("Plan validation error for user {}: {}".format(request.user.email, e))
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error("Error upgrading plan for user {}: {}".format(request.user.email, e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sync_asset(request, asset_id):
    """Sync data for an existing asset using the data pipeline.
    
    This endpoint triggers the data pipeline to collect fresh data
    from all external sources for the specified asset.
    
    Expected JSON payload:
    - address: str - Address to sync (optional, uses asset's address if not provided)
    
    Returns:
    - 200: {"message": "Sync started", "asset_id": int} - Sync initiated successfully
    - 404: Asset not found
    - 400: Invalid request
    - 500: Server error
    """
    try:
        # Get the asset
        try:
            asset = Asset.objects.get(id=asset_id)
        except Asset.DoesNotExist:
            return Response({"error": "Asset not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Parse request data
        data = parse_json(request)
        if not data:
            data = {}
        
        # Use provided address or asset's address
        address = data.get("address", asset.address)
        if not address:
            return Response({"error": "No address provided and asset has no address"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract house number from address if not provided
        house_number = data.get("house_number")
        if not house_number and asset.number:
            house_number = asset.number
        elif not house_number:
            # Try to extract from address
            import re
            match = re.search(r'(\d+)', address)
            if match:
                house_number = int(match.group(1))
            else:
                house_number = 1  # Default fallback
        
        logger.info("Starting asset sync for asset %s with address %s %s", asset_id, address, house_number)
        
        # Update asset status
        asset.status = "syncing"
        asset.last_sync_started_at = timezone.now()
        asset.save(update_fields=["status", "last_sync_started_at"])
        
        # Check if Celery is enabled
        from django.conf import settings
        if hasattr(settings, 'CELERY_BROKER_URL') and settings.CELERY_BROKER_URL:
            # Use Celery task
            from .tasks import run_data_pipeline
            result = run_data_pipeline.delay(asset_id)
            job_id = result.id
            logger.info("Enqueued asset sync task with job ID: %s", job_id)
            message = f"סנכרון נתונים התחיל עבור {address} {house_number} (מזהה נכס: {asset_id}, מזהה משימה: {job_id})"
        else:
            # Run asynchronously in background thread when Celery is disabled
            import threading
            
            def run_sync_async():
                try:
                    from .tasks import run_data_pipeline
                    run_data_pipeline(asset_id)
                    logger.info("Background asset sync completed for asset %s", asset_id)
                except Exception as e:
                    logger.error("Background asset sync failed for asset %s: %s", asset_id, e)
                    # Update asset status to error
                    try:
                        asset_obj = Asset.objects.get(id=asset_id)
                        asset_obj.status = "failed"
                        asset_obj.last_enrich_error = str(e)
                        asset_obj.save()
                    except Exception as save_error:
                        logger.error("Failed to update asset status: %s", save_error)
            
            thread = threading.Thread(target=run_sync_async, daemon=True)
            thread.start()
            message = f"סנכרון נתונים התחיל עבור {address} {house_number} (מזהה נכס: {asset_id})"
        
        return Response({
            "message": message,
            "asset_id": asset_id,
            "address": address,
            "house_number": house_number,
            "status": "syncing"
        })
        
    except Exception as e:
        logger.error("Error starting asset sync for asset %s: %s", asset_id, e)
        return Response({"error": "שגיאה בהתחלת סנכרון הנתונים"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([AllowAny])
def asset_listings(request, asset_id):
    """Fetch similar listings for an asset from Yad2 and other sources."""
    try:
        try:
            asset = Asset.objects.get(id=asset_id)
        except Asset.DoesNotExist:
            return Response({"error": "Asset not found"}, status=status.HTTP_404_NOT_FOUND)

        limit = parse_int(request.GET.get("limit"), 10, minimum=1, maximum=100)
        offset = parse_int(request.GET.get("offset"), 0, minimum=0) or 0
        search = (request.GET.get("search") or "").strip()
        source_filter = (request.GET.get("source") or "all").strip().lower()
        property_type_filter = (request.GET.get("property_type") or "all").strip().lower()
        listing_type_filter = (
            request.GET.get("listing_type")
            or request.GET.get("listingType")
            or "all"
        ).strip().lower()
        ad_type_filter = (
            request.GET.get("ad_type")
            or request.GET.get("adType")
            or "all"
        ).strip().lower()
        rooms_filter = (request.GET.get("rooms") or request.GET.get("rooms_filter") or "all").strip()
        min_price = parse_int(request.GET.get("min_price") or request.GET.get("price_min"), None, minimum=0)
        max_price = parse_int(request.GET.get("max_price") or request.GET.get("price_max"), None, minimum=0)
        ordering = (request.GET.get("ordering") or "-date_posted").strip() or "-date_posted"

        listings_all = []
        seen_keys = set()

        # Include listings linked through the new Listing model
        for listing_obj in asset_listings_all(asset):
            normalized = normalize_listing_from_model(listing_obj)
            key = normalized["id"] or f"{normalized.get('source', 'external')}:{normalized.get('external_id') or listing_obj.id}"
            if key in seen_keys:
                continue
            seen_keys.add(key)
            listings_all.append(normalized)

        # Include legacy metadata listings (e.g., scraped Yad2 entries)
        yad2_listings = asset.get_property_value("yad2_listings", []) or []
        for idx, meta_listing in enumerate(yad2_listings):
            normalized = normalize_listing_from_meta(meta_listing or {}, idx)
            key = normalized["id"] or f"{normalized.get('source', 'yad2')}:{idx}"
            if key in seen_keys:
                continue
            seen_keys.add(key)
            listings_all.append(normalized)

        total_available = len(listings_all)

        # Build filter metadata from the full list
        sources_available = sorted(
            {listing.get("source") for listing in listings_all if listing.get("source")}
        )
        property_types_available = sorted(
            {listing.get("property_type") for listing in listings_all if listing.get("property_type")}
        )
        listing_types_available = sorted(
            {
                listing.get("listing_type") or listing.get("listingType")
                for listing in listings_all
                if listing.get("listing_type") or listing.get("listingType")
            }
        )
        ad_types_available = sorted(
            {
                listing.get("ad_type") or listing.get("adType")
                for listing in listings_all
                if listing.get("ad_type") or listing.get("adType")
            }
        )
        rooms_available = sorted(
            {
                format_rooms_value(listing.get("rooms"))
                for listing in listings_all
                if format_rooms_value(listing.get("rooms"))
            },
            key=lambda x: float(x.replace(",", ".")) if x else 0.0,
        )
        price_values = [
            listing.get("price") for listing in listings_all if isinstance(listing.get("price"), int)
        ]
        price_meta = {
            "min": min(price_values) if price_values else None,
            "max": max(price_values) if price_values else None,
        }

        search_lower = search.lower() if search else None
        rooms_filter_normalized = format_rooms_value(rooms_filter) if rooms_filter not in ("", "all") else None

        filtered_listings = []
        for listing in listings_all:
            listing_source = (listing.get("source") or "").lower()
            if source_filter not in ("", "all") and listing_source != source_filter:
                continue

            listing_property_type = (listing.get("property_type") or "").lower()
            if property_type_filter not in ("", "all") and listing_property_type != property_type_filter:
                continue

            listing_type_value = (listing.get("listing_type") or listing.get("listingType") or "").lower()
            if listing_type_filter not in ("", "all") and listing_type_value != listing_type_filter:
                continue

            listing_ad_type = (listing.get("ad_type") or listing.get("adType") or "").lower()
            if ad_type_filter not in ("", "all") and listing_ad_type != ad_type_filter:
                continue

            if min_price is not None:
                listing_price = listing.get("price")
                if listing_price is None or listing_price < min_price:
                    continue

            if max_price is not None:
                listing_price = listing.get("price")
                if listing_price is None or listing_price > max_price:
                    continue

            if rooms_filter_normalized:
                listing_rooms_display = listing.get("rooms_display") or format_rooms_value(listing.get("rooms"))
                if not listing_rooms_display or listing_rooms_display != rooms_filter_normalized:
                    continue

            if search_lower:
                searchable_values = [
                    listing.get("title") or "",
                    listing.get("address") or "",
                    listing.get("description") or "",
                ]
                if not any(search_lower in (value or "").lower() for value in searchable_values):
                    continue

            filtered_listings.append(listing)

        total_filtered = len(filtered_listings)

        ordering_field = ordering
        reverse = False
        if ordering_field.startswith("-"):
            reverse = True
            ordering_field = ordering_field[1:]

        allowed_fields = {"price", "date_posted", "rooms", "size", "source", "title"}
        if ordering_field not in allowed_fields:
            ordering_field = "date_posted"

        def sort_key(item):
            if ordering_field == "price":
                value = item.get("price")
                if value is None:
                    return float("-inf") if reverse else float("inf")
                return value
            if ordering_field == "rooms":
                value = parse_float(item.get("rooms"))
                if value is None:
                    return float("-inf") if reverse else float("inf")
                return value
            if ordering_field == "size":
                value = parse_float(item.get("size"))
                if value is None:
                    return float("-inf") if reverse else float("inf")
                return value
            if ordering_field == "source":
                return (item.get("source") or "").lower()
            if ordering_field == "title":
                return (item.get("title") or "").lower()

            # Default: date_posted
            parsed_date = parse_date_value(item.get("date_posted"))
            if parsed_date is None:
                return datetime.min.replace(tzinfo=timezone.utc)
            return parsed_date

        filtered_listings.sort(key=sort_key, reverse=reverse)

        paginated = filtered_listings[offset: offset + limit]

        response_data = {
            "results": paginated,
            "count": total_filtered,
            "total_all": total_available,
            "limit": limit,
            "offset": offset,
            "ordering": f"{'-' if reverse else ''}{ordering_field}",
            "filters": {
                "source": sources_available,
                "property_type": property_types_available,
                "listing_type": listing_types_available,
                "ad_type": ad_types_available,
                "rooms": rooms_available,
                "price": price_meta,
            },
        }

        return Response(response_data)

    except Exception as e:
        logger.error(f"Error fetching listings for asset {asset_id}: {e}")
        return Response({"error": "Failed to fetch listings"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([AllowAny])
def dashboard_market_data(request):
    """Get aggregated market data for dashboard charts."""
    try:
        from datetime import datetime, timedelta
        from collections import defaultdict
        
        # Get last 6 months of data
        now = datetime.now()
        six_months_ago = now - timedelta(days=180)
        
        # Aggregate government transaction data by month
        gov_transactions = RealEstateTransaction.objects.filter(
            date__gte=six_months_ago,
            price__isnull=False,
            price__gt=0
        ).values('date', 'price', 'area', 'rooms')
        
        # Aggregate Yad2 market data by month from asset metadata
        yad2_data = []
        assets_with_yad2 = Asset.objects.filter(
            meta__yad2_listings__isnull=False
        ).exclude(meta__yad2_listings=[])
        
        for asset in assets_with_yad2:
            yad2_listings = asset.get_property_value('yad2_listings', [])
            for listing in yad2_listings:
                if listing.get('price'):
                    # Use scraped_at if available, otherwise skip
                    date_field = listing.get('scraped_at') or listing.get('date_posted')
                    if date_field:
                        try:
                            date_scraped = datetime.fromisoformat(date_field.replace('Z', '+00:00'))
                            if date_scraped >= six_months_ago:
                                yad2_data.append({
                                    'date': date_scraped,
                                    'price': listing['price'],
                                    'area': listing.get('area'),
                                    'rooms': listing.get('rooms')
                                })
                        except (ValueError, TypeError):
                            continue
        
        # Group data by month
        gov_by_month = defaultdict(lambda: {'count': 0, 'volume': 0, 'prices': []})
        yad2_by_month = defaultdict(lambda: {'count': 0, 'volume': 0, 'prices': []})
        
        # Process government transactions
        for tx in gov_transactions:
            if tx['date']:
                month_key = tx['date'].strftime('%Y-%m')
                gov_by_month[month_key]['count'] += 1
                gov_by_month[month_key]['volume'] += tx['price']
                gov_by_month[month_key]['prices'].append(tx['price'])
        
        # Process Yad2 data
        for listing in yad2_data:
            month_key = listing['date'].strftime('%Y-%m')
            yad2_by_month[month_key]['count'] += 1
            yad2_by_month[month_key]['volume'] += listing['price']
            yad2_by_month[month_key]['prices'].append(listing['price'])
        
        # Hebrew month names mapping
        hebrew_months = {
            1: 'ינואר', 2: 'פברואר', 3: 'מרץ', 4: 'אפריל',
            5: 'מאי', 6: 'יוני', 7: 'יולי', 8: 'אוגוסט',
            9: 'ספטמבר', 10: 'אוקטובר', 11: 'נובמבר', 12: 'דצמבר'
        }
        
        # Build response data for last 6 months
        market_data = []
        for i in range(6):
            month_date = now - timedelta(days=30*i)
            month_key = month_date.strftime('%Y-%m')
            month_label = hebrew_months[month_date.month]
            
            gov_data = gov_by_month[month_key]
            yad2_data_month = yad2_by_month[month_key]
            
            # Calculate average prices
            gov_avg_price = sum(gov_data['prices']) / len(gov_data['prices']) if gov_data['prices'] else 0
            yad2_avg_price = sum(yad2_data_month['prices']) / len(yad2_data_month['prices']) if yad2_data_month['prices'] else 0
            
            market_data.append({
                'month': month_label,
                'avgPrice': int((gov_avg_price + yad2_avg_price) / 2) if gov_avg_price and yad2_avg_price else int(gov_avg_price or yad2_avg_price),
                'transactions': gov_data['count'],
                'volume': gov_data['volume'],
                'yad2_listings': yad2_data_month['count'],
                'yad2_volume': yad2_data_month['volume']
            })
        
        # Reverse to show oldest first
        market_data.reverse()
        
        return Response({
            'marketData': market_data,
            'summary': {
                'totalTransactions': sum(gov_by_month[m]['count'] for m in gov_by_month),
                'totalVolume': sum(gov_by_month[m]['volume'] for m in gov_by_month),
                'totalYad2Listings': sum(yad2_by_month[m]['count'] for m in yad2_by_month),
                'totalYad2Volume': sum(yad2_by_month[m]['volume'] for m in yad2_by_month)
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching dashboard market data: {e}")
        return Response({"error": "Failed to fetch market data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Agent Chat",
    description="Chat with the AI real estate agent",
    tags=["Agent"],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'message': {'type': 'string', 'description': 'User message'},
                'chat_history': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'role': {'type': 'string'},
                            'content': {'type': 'string'}
                        }
                    },
                    'description': 'Optional chat history'
                }
            },
            'required': ['message']
        }
    },
    responses={
        200: {
            'description': 'Agent response',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'response': {'type': 'string'}
                        }
                    }
                }
            }
        }
    }
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def agent_chat(request):
    """Chat with the AI real estate agent."""
    try:
        if RealEstateAgent is None:
            error_msg = "Agent not available. Please install langchain dependencies."
            if _agent_import_error:
                error_msg += f" Import error: {_agent_import_error}"
            return Response(
                {"error": error_msg},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        data = json.loads(request.body.decode("utf-8"))
        message = data.get("message")
        chat_history = data.get("chat_history", [])
        
        if not message:
            return Response(
                {"error": "Message is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get API token for agent
        api_token = None
        try:
            from .models import APIToken
            # Try to get or create an API token for the user
            api_token_obj = APIToken.objects.filter(user=request.user, is_active=True).first()
            if api_token_obj:
                api_token = api_token_obj.key
        except Exception:
            pass
        
        # Initialize agent
        def has_valid_api_key(provider: str) -> bool:
            if provider == "groq":
                key = os.getenv("GROQ_API_KEY") or getattr(settings, "GROQ_API_KEY", None)
            elif provider == "gemini":
                key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or 
                       getattr(settings, "GEMINI_API_KEY", None) or getattr(settings, "GOOGLE_API_KEY", None))
            elif provider == "openai":
                key = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)
            else:
                return False
            return bool(key and key.strip())
        
        llm_provider = os.getenv("AGENT_LLM_PROVIDER")
        if not llm_provider:
            llm_provider = getattr(settings, "LLM_DEFAULT_PROVIDER", None)
        
        if llm_provider and not has_valid_api_key(llm_provider):
            logger.warning(f"LLM provider '{llm_provider}' selected but no valid API key found. Auto-detecting provider...")
            llm_provider = None
        
        if not llm_provider:
            groq_key = os.getenv("GROQ_API_KEY") or getattr(settings, "GROQ_API_KEY", None)
            gemini_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or 
                         getattr(settings, "GEMINI_API_KEY", None) or getattr(settings, "GOOGLE_API_KEY", None))
            openai_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)
            
            if groq_key and groq_key.strip():
                llm_provider = "groq"
            elif gemini_key and gemini_key.strip():
                llm_provider = "gemini"
            elif openai_key and openai_key.strip():
                llm_provider = "openai"
            else:
                # Default fallback
                llm_provider = "openai"
        
        # Final validation - ensure we have a valid API key for the selected provider
        if not has_valid_api_key(llm_provider):
            return Response(
                {
                    "error": f"No valid API key found for provider '{llm_provider}'. "
                            f"Please set {llm_provider.upper()}_API_KEY environment variable or in Django settings."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        agent = RealEstateAgent(
            llm_provider=llm_provider,
            api_token=api_token,
            api_url=os.getenv("REALESTATE_API_URL", f"{request.scheme}://{request.get_host()}/api"),
            temperature=0.3
        )
        
        # Convert chat history format if needed
        formatted_history = []
        for msg in chat_history:
            if isinstance(msg, dict):
                formatted_history.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        # Get response from agent
        response = async_to_sync(agent.chat)(message, formatted_history)
        
        return Response({"response": response})
        
    except json.JSONDecodeError:
        return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Error in agent chat: %s", e)
        return Response(
            {"error": f"Failed to get agent response: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Agent Feedback",
    description="Submit feedback for agent responses",
    tags=["Agent"],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'message_id': {'type': 'string', 'description': 'Unique message identifier'},
                'feedback': {'type': 'string', 'enum': ['positive', 'negative'], 'description': 'Feedback type'},
                'message_content': {'type': 'string', 'description': 'The assistant message content'},
                'user_message': {'type': 'string', 'description': 'The user message that prompted this response'}
            },
            'required': ['message_id', 'feedback']
        }
    },
    responses={
        200: {
            'description': 'Feedback submitted successfully',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'success': {'type': 'boolean'},
                            'message': {'type': 'string'}
                        }
                    }
                }
            }
        }
    }
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def agent_feedback(request):
    """Submit feedback for agent responses."""
    try:
        data = json.loads(request.body.decode("utf-8"))
        message_id = data.get("message_id")
        feedback = data.get("feedback")
        message_content = data.get("message_content", "")
        user_message = data.get("user_message")
        
        if not message_id:
            return Response(
                {"error": "message_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if feedback not in ["positive", "negative"]:
            return Response(
                {"error": "feedback must be 'positive' or 'negative'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Log feedback for analytics/improvement
        logger.info(
            f"Agent feedback: user={request.user.id}, message_id={message_id}, "
            f"feedback={feedback}, content_length={len(message_content) if message_content else 0}"
        )
        
        # Track feedback in analytics
        try:
            track(
                "agent_feedback",
                user=request.user,
                metadata={
                    "message_id": message_id,
                    "feedback": feedback,
                    "message_length": len(message_content) if message_content else 0,
                    "has_user_message": bool(user_message)
                }
            )
        except Exception as e:
            logger.warning(f"Failed to track agent feedback: {e}")
        
        return Response({
            "success": True,
            "message": "Feedback submitted successfully"
        })
        
    except json.JSONDecodeError:
        return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Error in agent feedback: %s", e)
        return Response(
            {"error": f"Failed to submit feedback: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
