import json
import statistics
import re
import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path

from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, render
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

import logging

from openai import OpenAI

# Import Django models
from .models import (
    AlertRule,
    AlertEvent,
    Asset,
    SourceRecord,
    RealEstateTransaction,
    OnboardingProgress,
    ShareToken,
    AssetContribution,
    UserProfile,
)

from .listing_builder import build_listing
from .serializers import AlertRuleSerializer, AlertEventSerializer, AssetContributionSerializer, UserProfileSerializer

# Import utility functions
try:
    from utils.tabu_parser import parse_tabu_pdf, search_rows
except ImportError:

    def parse_tabu_pdf(file):
        """Fallback function for parsing tabu PDFs when utils module is not available."""
        return []

    def search_rows(rows, query):
        """Fallback function for searching rows when utils module is not available."""
        return rows


# Import tasks
from .tasks import run_data_pipeline
from .analytics import track, track_search, track_feature_usage

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
        # In a real application, you might want to blacklist the token
        # For now, we'll just return success
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
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "company": getattr(user, "company", ""),
                "role": getattr(user, "role", ""),
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
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "company": getattr(user, "company", ""),
                    "role": getattr(user, "role", ""),
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
        return Response(
            {"error": result["error"], **result.get("data", {})},
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
            "role": getattr(u, "role", "member"),
        }
    )


# Demo mode


@api_view(["POST"])
@permission_classes([AllowAny])
def demo_start(request):
    """Create a demo user and seed sample assets."""
    User = get_user_model()
    username = f"demo_{get_random_string(8)}"
    email = f"{username}@demo.local"
    password = get_random_string(12)
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name="Demo",
        last_name="User",
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
        Asset.objects.create(
            **data,
            status="done",
            is_demo=True,
            meta={"demo": True},
        )

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
        # Create a new asset for the address
        from .models import Asset

        asset = Asset.objects.create(
            scope_type="address",
            street=street,
            number=number,
            status="pending",
            meta={"radius": 150},
        )

        # Start enrichment pipeline
        try:
            run_data_pipeline.delay(asset.id)
            message = (
                f"Asset enrichment started for {street} {number} (Asset ID: {asset.id})"
            )
        except Exception as e:
            message = f"Asset created but enrichment failed: {str(e)}"

        # Return asset info
        assets = [
            {
                "id": asset.id,
                "source": "asset",
                "external_id": f"asset_{asset.id}",
                "title": f"Asset for {street} {number}",
                "address": f"{street} {number}",
                "status": asset.status,
                "message": message,
            }
        ]

        return JsonResponse(
            {"rows": assets, "message": message, "address": f"{street} {number}"}
        )
    except ValueError as e:
        return JsonResponse({"error": f"Validation error: {str(e)}"}, status=400)
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
                    {"message": f"Report {report_id} deleted successfully"}, status=200
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


def report_file(request, filename):
    """Serve a generated report PDF from the backend."""
    report = report_service.get_report_by_filename(filename)
    if not report or not os.path.exists(report.file_path):
        raise Http404("Report not found")
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
                f"LTV 70%, ריבית {annual_rate_pct}%, תקופה {term_years}y",
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
        rows = parse_tabu_pdf(file)
        query = request.GET.get("q") or ""
        if query:
            rows = search_rows(rows, query)
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
                        "gush": "1234",
                        "helka": "56",
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
        "gush": "string",
        "helka": "string",
        "radius": "integer"
    }
    """
    if request.method == "GET":
        # Return all assets in listing format
        return _get_assets_list()

    if request.method == "DELETE":
        data = parse_json(request)
        if not data or not data.get("assetId"):
            return Response({"error": "assetId required"}, status=400)

        try:
            asset_id = int(data["assetId"])
            asset = Asset.objects.get(id=asset_id)

            if asset.delete_asset():
                return Response(
                    {"message": f"Asset {asset_id} deleted successfully"}, status=200
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
    cache_key = f"assets_post_{ip}"
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
        
        # Create asset record with attribution
        asset_data = {
            "scope_type": scope_type,
            "city": data.get("city") or scope.get("city"),
            "neighborhood": data.get("neighborhood"),
            "street": data.get("street"),
            "number": data.get("number"),
            "apartment": data.get("apartment"),
            "gush": data.get("gush"),
            "helka": data.get("helka"),
            "subhelka": data.get("subhelka"),
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
                description=f"נוצר נכס עבור {scope_type}: {data.get('city', 'מיקום לא ידוע')}",
                source='manual'
            )
            
            # Update user profile stats
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.update_contribution_stats('creation')
        
        logger.info("Asset creation - User: %s, Authenticated: %s", 
                   user, is_authenticated)
        if is_authenticated:
            track("asset_create", user=user, asset_id=asset_id)
        else:
            track("asset_create", asset_id=asset_id)
        
        # Track feature usage
        track_feature_usage("asset_creation", user=user, asset_id=asset_id)
        _update_onboarding(user, "add_first_asset")

        # Enqueue Celery task if available
        job_id = None
        try:
            result = run_data_pipeline.delay(asset_id)
            job_id = result.id
        except Exception as e:
            logger.error("Failed to enqueue enrichment task: %s", e)
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


def _get_assets_list():
    """Helper function to get all assets in listing format."""

    try:
        assets_qs = Asset.objects.all().order_by("-created_at")
        rows = []
        for asset in assets_qs:
            srcs = SourceRecord.objects.filter(asset_id=asset.id).order_by(
                "-fetched_at"
            )
            rows.append(build_listing(asset, srcs))
        return Response({"rows": rows})
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
        # Get asset using Django ORM with attribution data
        try:
            asset = Asset.objects.select_related('created_by', 'last_updated_by').get(id=asset_id)
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
        transactions = RealEstateTransaction.objects.filter(asset_id=asset_id)
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

        # Get attribution information
        attribution_info = {}
        if asset.created_by:
            attribution_info["created_by"] = {
                "id": asset.created_by.id,
                "email": asset.created_by.email,
                "name": f"{asset.created_by.first_name} {asset.created_by.last_name}".strip() or asset.created_by.email,
            }
        if asset.last_updated_by:
            attribution_info["last_updated_by"] = {
                "id": asset.last_updated_by.id,
                "email": asset.last_updated_by.email,
                "name": f"{asset.last_updated_by.first_name} {asset.last_updated_by.last_name}".strip() or asset.last_updated_by.email,
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
                    "name": f"{contrib.user.first_name} {contrib.user.last_name}".strip() or contrib.user.email,
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
        serializer = AssetSerializer(asset)
        asset_data = serializer.data
        
        # Add additional data not in the serializer
        asset_data.update({
            "attribution": attribution_info,
            "recent_contributions": contributions_list,
            "records": records_by_source,
            "transactions": transaction_list,
        })
        
        return JsonResponse(asset_data)

    except Exception as e:
        logger.error("Error retrieving asset %s: %s", asset_id, e)
        return JsonResponse(
            {"error": "Failed to retrieve asset", "details": str(e)}, status=500
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
    logger.info(
        "Generating marketing message for asset %s in %s",
        asset_id,
        language,
    )

    data_json = json.dumps(listing, ensure_ascii=False)
    prompt = (
        f"Create an engaging {language} marketing message for social media and messaging apps about a property for sale. "
        f"Use this data:\n{data_json}\n"
    )

    message = None
    if os.environ.get("OPENAI_API_KEY"):
        try:
            client = OpenAI()
            completion = client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {
                        "role": "system",
                        "content": f"You write short real estate marketing messages in {language}.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            message = completion.choices[0].message.content.strip()
        except Exception as e:
            logger.exception("Error generating marketing message for asset %s: %s", asset_id, e)
            message = None

    if not message:
        addr = listing.get("address") or ""
        price = listing.get("price")
        rooms = listing.get("rooms")
        area = listing.get("netSqm")
        price_s = f" במחיר {price:,.0f}₪" if price else ""
        rooms_s = f"{int(rooms)} חדרים" if rooms else "דירה"
        area_s = f' {int(area)} מ"ר' if area else ""
        message = f"למכירה {rooms_s}{area_s} ב{addr}{price_s}."

    logger.info("Marketing message generated for asset %s", asset_id)

    token = secrets.token_urlsafe(16)
    ShareToken.objects.create(asset=asset, token=token)
    share_url = f"/r/{token}"

    return Response({"text": message, "share_url": share_url})


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
