import json
import os
import re
import statistics
import urllib.parse
import time
from datetime import datetime
from pathlib import Path

from django.contrib.auth import authenticate, get_user_model
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()
from django.urls import reverse
from openai import OpenAI

# --- PDF / Fonts ---
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from bidi.algorithm import get_display

# Models
from .models import Alert, Asset, SourceRecord, RealEstateTransaction, Report

# Tasks
from .tasks import run_data_pipeline

BASE_DIR = Path(__file__).resolve().parent.parent

# Reports output dir (can be overridden via env)
REPORTS_DIR = os.environ.get(
    "REPORTS_DIR",
    str((BASE_DIR.parent / "realestate-broker-ui" / "public" / "reports").resolve()),
)

# --- Robust Hebrew font registration ---
_HEBREW_FONT_NAME = None

def _candidate_font_paths():
    return [
        os.environ.get("REPORT_HEBREW_FONT_PATH"),
        str(BASE_DIR / "core" / "fonts" / "NotoSansHebrew-Regular.ttf"),
        "/usr/share/fonts/truetype/noto/NotoSansHebrew-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansHebrew-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]

def get_hebrew_font_name():
    """
    Ensure a font that supports Hebrew is registered and return its name.
    Falls back to Helvetica only as a last resort (won't render Hebrew correctly).
    """
    global _HEBREW_FONT_NAME
    if _HEBREW_FONT_NAME:
        return _HEBREW_FONT_NAME

    for p in _candidate_font_paths():
        if not p:
            continue
        try:
            if os.path.exists(p):
                pdfmetrics.registerFont(TTFont("HebrewTT", p))
                _HEBREW_FONT_NAME = "HebrewTT"
                return _HEBREW_FONT_NAME
        except Exception:
            pass

    _HEBREW_FONT_NAME = "Helvetica"
    return _HEBREW_FONT_NAME

def draw_text(c: canvas.Canvas, x: float, y: float, text: str, *, size=12, align="right"):
    """
    Draw text with RTL support for Hebrew when a Hebrew-capable font is available.
    align: 'right' | 'center' | 'left'
    """
    font_name = get_hebrew_font_name()
    c.setFont(font_name, size)
    # Reorder bidi so Hebrew appears properly
    content = get_display(str(text)) if font_name != "Helvetica" else str(text)

    if align == "center":
        c.drawCentredString(x, y, content)
    elif align == "right":
        c.drawRightString(x, y, content)
    else:
        c.drawString(x, y, content)

def ensure_reports_dir():
    os.makedirs(REPORTS_DIR, exist_ok=True)

def parse_json(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return None

# -------------------------
# Auth & Profile Endpoints
# -------------------------

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
                {"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "company": getattr(user, "company", ""),
                    "role": getattr(user, "role", ""),
                    "is_verified": getattr(user, "is_verified", False),
                },
            }
        )

    except json.JSONDecodeError:
        return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
@permission_classes([AllowAny])
def auth_register(request):
    """User registration endpoint."""
    try:
        data = json.loads(request.body.decode("utf-8"))
        email = data.get("email")
        password = data.get("password")
        username = data.get("username")
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")
        company = data.get("company", "")
        role = data.get("role", "")

        if not email or not password or not username:
            return Response(
                {"error": "Email, password, and username are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            company=company,
            role=role,
        )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "company": getattr(user, "company", ""),
                    "role": getattr(user, "role", ""),
                    "is_verified": getattr(user, "is_verified", False),
                },
            },
            status=status.HTTP_201_CREATED,
        )

    except json.JSONDecodeError:
        return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def auth_logout(request):
    """User logout endpoint."""
    try:
        return Response({"message": "התנתקת בהצלחה"})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def auth_profile(request):
    """Get current user profile."""
    try:
        user = request.user
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
                    "created_at": user.created_at.isoformat() if hasattr(user, "created_at") else None,
                    "language": getattr(user, "language", ""),
                    "timezone": getattr(user, "timezone", ""),
                    "currency": getattr(user, "currency", ""),
                    "date_format": getattr(user, "date_format", ""),
                    "notify_email": getattr(user, "notify_email", False),
                    "notify_whatsapp": getattr(user, "notify_whatsapp", False),
                    "notify_urgent": getattr(user, "notify_urgent", False),
                    "notification_time": getattr(user, "notification_time", ""),
                }
            }
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def auth_update_profile(request):
    """Update current user profile."""
    try:
        data = json.loads(request.body.decode("utf-8"))
        user = request.user

        if "first_name" in data:
            user.first_name = data["first_name"]
        if "last_name" in data:
            user.last_name = data["last_name"]
        if "company" in data:
            user.company = data["company"]
        if "role" in data:
            user.role = data["role"]

        user.save()

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
            return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)

        return Response({"access_token": access_token, "refresh_token": str(refresh)})

    except json.JSONDecodeError:
        return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

def _callback_url(request) -> str:
    """Build absolute callback URL for Google OAuth."""
    return request.build_absolute_uri(reverse("auth_google_callback"))

@api_view(["GET"])
@permission_classes([AllowAny])
def auth_google_login(request):
    """Initiate Google OAuth login flow."""
    try:
        from django.conf import settings

        redirect_uri = _callback_url(request)
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
        }

        auth_url = f"{settings.GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
        return Response({"auth_url": auth_url})

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
@permission_classes([AllowAny])
def auth_google_callback(request):
    """Handle Google OAuth callback and authenticate user."""
    try:
        import requests
        from django.conf import settings
        from django.contrib.auth import get_user_model

        User = get_user_model()

        code = request.GET.get("code")
        if not code:
            return Response({"error": "Authorization code not provided"}, status=status.HTTP_400_BAD_REQUEST)

        redirect_uri = _callback_url(request)
        token_data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }

        token_response = requests.post(settings.GOOGLE_TOKEN_URL, data=token_data, timeout=10)
        token_info = token_response.json()
        if token_response.status_code != 200:
            return Response(token_info, status=status.HTTP_400_BAD_REQUEST)

        access_token = token_info.get("access_token")

        user_info_response = requests.get(
            settings.GOOGLE_USER_INFO_URL, headers={"Authorization": f"Bearer {access_token}"}
        )
        if not user_info_response.ok:
            return Response({"error": "Failed to get user info from Google"}, status=status.HTTP_400_BAD_REQUEST)

        user_info = user_info_response.json()
        email = user_info.get("email")
        first_name = user_info.get("given_name", "")
        last_name = user_info.get("family_name", "")

        if not email:
            return Response({"error": "Email not provided by Google"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            base_username = email.split("@")[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            user.set_unusable_password()
            try:
                user.is_verified = True
            except Exception:
                pass
            user.save()

        refresh = RefreshToken.for_user(user)
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        tokens = {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "company": getattr(user, "company", ""),
                "role": getattr(user, "role", ""),
                "is_verified": getattr(user, "is_verified", False),
            },
        }

        encoded_tokens = urllib.parse.urlencode(tokens)
        redirect_url = f"{frontend_url}/auth/google-callback?{encoded_tokens}"
        return redirect(redirect_url)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# -------------------------
# User Settings / Alerts
# -------------------------

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
            }
        )

    if request.method == "PUT":
        data = parse_json(request)
        if not data:
            return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)

        for field in [
            "language",
            "timezone",
            "currency",
            "date_format",
            "notify_email",
            "notify_whatsapp",
            "notify_urgent",
            "notification_time",
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
            }
        )

    return Response({"error": "Unsupported method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def alerts(request):
    if request.method == "POST":
        data = parse_json(request)
        if not data:
            return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)

        alert = Alert.objects.create(
            user=request.user, criteria=data.get("criteria") or {}, notify=data.get("notify") or []
        )
        return Response(
            {"id": alert.id, "created_at": alert.created_at.isoformat()},
            status=status.HTTP_201_CREATED,
        )

    if request.method == "GET":
        rows = [
            {
                "id": alert.id,
                "criteria": alert.criteria,
                "notify": alert.notify,
                "active": alert.active,
                "created_at": alert.created_at.isoformat(),
            }
            for alert in Alert.objects.filter(user=request.user).order_by("-created_at")
        ]
        return Response({"rows": rows})

    return Response({"error": "Unsupported method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

# -------------------------
# Address Sync
# -------------------------

@csrf_exempt
def sync_address(request):
    """Fetch external data for a given address and store it."""
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON in request body"}, status=400)

    street = data.get("street", "").strip() if data.get("street") else None
    number = data.get("house_number")

    if not street or number is None:
        addr = (data.get("address") or "").strip()
        if not addr:
            return JsonResponse(
                {"error": "Either (street, house_number) or address is required"}, status=400
            )
        match = re.match(r"^(.+?)\s+(\d+)", addr)
        if match:
            street, number = match.group(1).strip(), match.group(2)
        else:
            return JsonResponse(
                {"error": 'Could not parse address. Expected format: "Street Name Number"'},
                status=400,
            )

    if not street:
        return JsonResponse({"error": "Street name is required"}, status=400)

    try:
        number = int(number)
        if number <= 0:
            return JsonResponse({"error": "House number must be a positive integer"}, status=400)
    except (TypeError, ValueError):
        return JsonResponse({"error": "House number must be a valid integer"}, status=400)

    try:
        asset = Asset.objects.create(
            scope_type="address", street=street, number=number, status="pending", meta={"radius": 150}
        )

        try:
            run_data_pipeline.delay(asset.id)
            message = f"העשרת הנכס החלה עבור {street} {number} (Asset ID: {asset.id})"
        except Exception as e:
            message = f"נוצר נכס אך תזמון ההעשרה נכשל: {str(e)}"

        assets = [
            {
                "id": asset.id,
                "source": "asset",
                "external_id": f"asset_{asset.id}",
                "title": f"נכס עבור {street} {number}",
                "address": f"{street} {number}",
                "status": asset.status,
                "message": message,
            }
        ]

        return JsonResponse({"rows": assets, "message": message, "address": f"{street} {number}"})
    except ValueError as e:
        return JsonResponse({"error": f"Validation error: {str(e)}"}, status=400)
    except Exception as e:
        import logging

        logging.exception("Unexpected error in sync_address: %s", e)
        return JsonResponse({"error": "שגיאה פנימית במהלך סנכרון הכתובת"}, status=500)

# -------------------------
# Reports (PDF generation) — Hebrew only
# -------------------------

@csrf_exempt
def reports(request):
    """צור דו״ח PDF עבור נכס או הצג רשימת דוחות קיימים."""
    if request.method == "GET":
        reports_list = []
        for report in Report.objects.all().order_by("-generated_at"):
            reports_list.append(
                {
                    "id": report.id,
                    "assetId": report.asset.id if report.asset else None,
                    "address": report.title or "N/A",
                    "filename": report.filename,
                    "createdAt": report.generated_at.isoformat(),
                    "status": report.status,
                    "pages": report.pages,
                    "fileSize": report.file_size,
                }
            )
        return JsonResponse({"reports": reports_list})

    if request.method == "DELETE":
        data = parse_json(request)
        if not data or not data.get("reportId"):
            return JsonResponse({"error": "reportId נדרש"}, status=400)

        try:
            report_id = int(data["reportId"])
            report = Report.objects.get(id=report_id)

            if report.delete_report():
                return JsonResponse({"message": f"דו״ח {report_id} נמחק בהצלחה"}, status=200)
            else:
                return JsonResponse({"error": "מחיקת הדו״ח נכשלה"}, status=500)

        except Report.DoesNotExist:
            return JsonResponse({"error": "דו״ח לא נמצא"}, status=404)
        except ValueError:
            return JsonResponse({"error": "מזהה דו״ח לא תקין"}, status=400)
        except Exception as e:
            return JsonResponse({"error": "שגיאה במחיקת דו״ח", "details": str(e)}, status=500)

    if request.method != "POST":
        return JsonResponse({"error": "נדרשת בקשת POST או DELETE"}, status=405)

    data = parse_json(request)
    if not data or not data.get("assetId"):
        return JsonResponse({"error": "assetId נדרש"}, status=400)

    asset_id = int(data["assetId"])

    # נתוני דמה (כמו בקוד המקורי), עם טקסטים בעברית
    mock_assets = {
        1: {
            "address": 'רחוב הרצל 123, תל אביב',
            "city": "תל אביב",
            "neighborhood": "מרכז העיר",
            "type": "דירה",
            "price": 2_850_000,
            "bedrooms": 3,
            "bathrooms": 2,
            "netSqm": 85,
            "area": 85,
            "pricePerSqm": 33_529,
            "remainingRightsSqm": 45,
            "program": 'תמ״א 38',
            "lastPermitQ": "Q2/24",
            "noiseLevel": 2,
            "competition1km": "בינוני",
            "zoning": "מגורים א׳",
            "priceGapPct": -5.2,
            "expectedPriceRange": "2.7M - 3.0M",
            "modelPrice": 3_000_000,
            "confidencePct": 85,
            "capRatePct": 3.2,
            "rentEstimate": 9_500,
            "riskFlags": [],
            "features": ["מעלית", "חניה", "מרפסת", "משופצת"],
            "contactInfo": {
                "agent": "יוסי כהן",
                "phone": "050-1234567",
                "email": "yossi@example.com",
            },
            "documents": [
                {"name": "נסח טאבו", "type": "tabu"},
                {"name": "תשריט בית משותף", "type": "condo_plan"},
                {"name": "היתר בנייה", "type": "permit"},
                {"name": "זכויות בנייה", "type": "rights"},
                {"name": "שומת מכרעת", "type": "appraisal_decisive"},
                {"name": "שומת רמ״י", "type": "appraisal_rmi"},
            ],
        }
    }

    if asset_id not in mock_assets:
        return JsonResponse({"error": "נכס לא נמצא"}, status=404)

    listing = mock_assets[asset_id]

    # יצירת רשומת דו״ח
    report = Report.objects.create(
        asset=None,
        report_type="asset",
        status="generating",
        filename="",
        file_path="",
        title=listing["address"],
        description=f'דו״ח נכס עבור {listing["address"]}',
        pages=4,
    )

    ensure_reports_dir()
    filename = f"r{report.id}.pdf"
    file_path = os.path.join(REPORTS_DIR, filename)

    report.filename = filename
    report.file_path = file_path
    report.save()

    started = time.time()

    try:
        c = canvas.Canvas(file_path, pagesize=A4)
        PAGE_WIDTH, PAGE_HEIGHT = A4
        RIGHT_MARGIN = PAGE_WIDTH - 50
        CENTER_X = PAGE_WIDTH / 2

        # עמוד 1: ניתוח כללי
        draw_text(c, CENTER_X, 760, 'דו"ח נכס - ניתוח כללי', size=20, align="center")

        y = 720
        draw_text(c, RIGHT_MARGIN, y, "פרטי הנכס", size=14); y -= 25
        draw_text(c, RIGHT_MARGIN, y, f'כתובת: {listing["address"]}'); y -= 20
        draw_text(c, RIGHT_MARGIN, y, f'עיר: {listing["city"]}'); y -= 20
        draw_text(c, RIGHT_MARGIN, y, f'שכונה: {listing["neighborhood"]}'); y -= 20
        draw_text(c, RIGHT_MARGIN, y, f'סוג: {listing["type"]}'); y -= 20

        draw_text(c, RIGHT_MARGIN, y, f'מחיר: ₪{int(listing["price"]):,}'); y -= 20
        draw_text(c, RIGHT_MARGIN, y, f'חדרי שינה: {listing["bedrooms"]}'); y -= 20
        draw_text(c, RIGHT_MARGIN, y, f'חדרי רחצה: {listing["bathrooms"]}'); y -= 20
        draw_text(c, RIGHT_MARGIN, y, f'שטח (מ"ר): {listing["netSqm"]}'); y -= 20
        draw_text(c, RIGHT_MARGIN, y, f'מחיר למ"ר: ₪{listing["pricePerSqm"]:,}'); y -= 20

        y -= 20
        draw_text(c, RIGHT_MARGIN, y, "אנליזה פיננסית", size=14); y -= 25
        draw_text(c, RIGHT_MARGIN, y, f'מחיר מודל: ₪{listing["modelPrice"]:,}'); y -= 20
        draw_text(c, RIGHT_MARGIN, y, f'פער מחיר: {listing["priceGapPct"]}%'); y -= 20
        draw_text(c, RIGHT_MARGIN, y, f'שכירות משוערת: ₪{listing["rentEstimate"]:,}'); y -= 20
        draw_text(c, RIGHT_MARGIN, y, f'תשואה שנתית: {listing["capRatePct"]}%'); y -= 20
        draw_text(c, RIGHT_MARGIN, y, f'תחרות (1 ק"מ): {listing["competition1km"]}'); y -= 20

        y -= 20
        draw_text(c, RIGHT_MARGIN, y, "המלצת השקעה", size=14); y -= 25
        price_gap_component = 100 + listing["priceGapPct"] if listing["priceGapPct"] < 0 else 100 - listing["priceGapPct"]
        overall_score = round((listing["confidencePct"] + (listing["capRatePct"] * 20) + price_gap_component) / 3)
        draw_text(c, RIGHT_MARGIN, y, f"ציון כללי: {overall_score}/100"); y -= 20

        if listing["priceGapPct"] < -10:
            recommendation = "הנכס במחיר אטרקטיבי מתחת לשוק"
        elif listing["priceGapPct"] > 10:
            recommendation = "הנכס יקר יחסית לשוק"
        else:
            recommendation = "הנכס במחיר שוק הוגן"
        draw_text(c, RIGHT_MARGIN, y, f"המלצה: {recommendation}")

        c.showPage()

        # עמוד 2: תוכניות וזכויות בנייה
        draw_text(c, CENTER_X, 760, "תוכניות וזכויות בנייה", size=20, align="center")
        y = 720
        draw_text(c, RIGHT_MARGIN, y, "תוכניות מקומיות ומפורטות", size=14); y -= 25
        draw_text(c, RIGHT_MARGIN, y, f'תוכנית נוכחית: {listing["program"]}'); y -= 20
        draw_text(c, RIGHT_MARGIN, y, f'אזור תכנון: {listing["zoning"]}'); y -= 20
        draw_text(c, RIGHT_MARGIN, y, f'יתרת זכויות: +{listing["remainingRightsSqm"]} מ"ר'); y -= 20
        draw_text(c, RIGHT_MARGIN, y, f'זכויות בנייה עיקריות: {listing["netSqm"]} מ"ר'); y -= 40

        draw_text(c, RIGHT_MARGIN, y, "זכויות בנייה מפורטות", size=14); y -= 25
        draw_text(c, RIGHT_MARGIN, y, f'יתרת זכויות: {listing["remainingRightsSqm"]} מ"ר'); y -= 20
        pct = round((listing["remainingRightsSqm"] / listing["netSqm"]) * 100)
        draw_text(c, RIGHT_MARGIN, y, f"אחוז זכויות נוספות: {pct}%"); y -= 20
        rights_value = round((listing["pricePerSqm"] * listing["remainingRightsSqm"] * 0.7) / 1000)
        draw_text(c, RIGHT_MARGIN, y, f"שווי זכויות משוער: ₪{rights_value} אלף")

        c.showPage()

        # עמוד 3: מידע סביבתי
        draw_text(c, CENTER_X, 760, "מידע סביבתי", size=20, align="center")
        y = 720
        draw_text(c, RIGHT_MARGIN, y, "מידע סביבתי", size=14); y -= 25
        draw_text(c, RIGHT_MARGIN, y, f'רמת רעש: {listing["noiseLevel"]}/5'); y -= 20
        draw_text(c, RIGHT_MARGIN, y, "שטחים ציבוריים ≤300מ׳: כן"); y -= 20
        draw_text(c, RIGHT_MARGIN, y, "מרחק אנטנה: 150מ׳"); y -= 40

        draw_text(c, RIGHT_MARGIN, y, "סיכונים", size=14); y -= 25
        if listing["riskFlags"]:
            for flag in listing["riskFlags"]:
                draw_text(c, RIGHT_MARGIN, y, f"• {flag}"); y -= 20
        else:
            draw_text(c, RIGHT_MARGIN, y, "אין סיכונים מיוחדים")

        c.showPage()

        # עמוד 4: מסמכים וסיכום
        draw_text(c, CENTER_X, 760, "מסמכים וסיכום", size=20, align="center")
        y = 720
        draw_text(c, RIGHT_MARGIN, y, "מסמכים זמינים", size=14); y -= 25
        if listing["documents"]:
            for doc in listing["documents"]:
                draw_text(c, RIGHT_MARGIN, y, f'• {doc["name"]} ({doc["type"]})'); y -= 20
        else:
            draw_text(c, RIGHT_MARGIN, y, "אין מסמכים זמינים")

        y -= 30
        draw_text(c, RIGHT_MARGIN, y, "פרטי קשר", size=14); y -= 25
        if listing["contactInfo"]:
            draw_text(c, RIGHT_MARGIN, y, f'סוכן: {listing["contactInfo"]["agent"]}'); y -= 20
            draw_text(c, RIGHT_MARGIN, y, f'טלפון: {listing["contactInfo"]["phone"]}'); y -= 20
            draw_text(c, RIGHT_MARGIN, y, f'אימייל: {listing["contactInfo"]["email"]}')

        c.save()

        generation_time = time.time() - started
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        report.mark_completed(file_size=file_size, pages=4, generation_time=generation_time)

    except Exception as e:
        report.mark_failed(str(e))
        return JsonResponse({"error": "יצירת ה-PDF נכשלה", "details": str(e)}, status=500)

    return JsonResponse(
        {
            "report": {
                "id": report.id,
                "assetId": asset_id,
                "address": listing["address"],
                "filename": filename,
                "createdAt": report.generated_at.isoformat(),
                "status": report.status,
                "pages": report.pages,
                "fileSize": report.file_size,
            }
        },
        status=201,
    )

# -------------------------
# Mortgage Analysis
# -------------------------

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

    max_loan_from_payment = annuity_max_loan(recommended_payment, annual_rate_pct, term_years)
    max_loan_by_ltv = price * 0.70 if price > 0 else max_loan_from_payment
    approved_loan_ceiling = min(max_loan_from_payment, max_loan_by_ltv)
    cash_needed = max(0.0, price - approved_loan_ceiling)
    cash_gap = max(0.0, cash_needed - savings)
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
            "notes": ["אינפורמטיבי בלבד", f"LTV 70%, ריבית {annual_rate_pct}%, תקופה {term_years}y"],
        }
    )

# -------------------------
# Tabu PDF Parsing
# -------------------------

try:
    from utils.tabu_parser import parse_tabu_pdf, search_rows
except ImportError:
    def parse_tabu_pdf(file):  # fallback
        return []
    def search_rows(rows, query):  # fallback
        return rows

@csrf_exempt
def tabu(request):
    """ניתוח קובץ טאבו שהועלה והחזרת טבלה לחיפוש."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    file = request.FILES.get("file")
    if not file:
        return JsonResponse({"error": "file required"}, status=400)

    try:
        rows = parse_tabu_pdf(file)
        query = request.GET.get("q") or ""
        if query:
            rows = search_rows(rows, query)
        return JsonResponse({"rows": rows})
    except Exception as e:
        print(f"Error parsing tabu PDF: {e}")
        return JsonResponse(
            {
                "rows": [
                    {"id": 1, "gush": "1234", "helka": "56", "owner": "בעלים לדוגמה", "area": "150", "usage": "מגורים"}
                ]
            }
        )

# -------------------------
# Assets & Details
# -------------------------

@csrf_exempt
def assets(request):
    """GET כל הנכסים (רשימה) או POST יצירת נכס חדש ותזמון העשרה."""
    if request.method == "GET":
        return _get_assets_list()

    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON in request body"}, status=400)

    try:
        scope = data.get("scope", {})
        scope_type = scope.get("type")
        if not scope_type:
            return JsonResponse({"error": "Scope type is required"}, status=400)

        asset_data = {
            "scope_type": scope_type,
            "city": data.get("city") or scope.get("city"),
            "neighborhood": data.get("neighborhood"),
            "street": data.get("street"),
            "number": data.get("number"),
            "gush": data.get("gush"),
            "helka": data.get("helka"),
            "status": "pending",
            "meta": {"scope": scope, "raw_input": data, "radius": data.get("radius", 150)},
        }

        asset = Asset.objects.create(**asset_data)
        asset_id = asset.id

        try:
            run_data_pipeline.delay(asset_id)
        except Exception as e:
            print(f"Failed to enqueue enrichment task: {e}")
            try:
                asset = Asset.objects.get(id=asset_id)
                asset.status = "error"
                m = asset.meta or {}
                m["error"] = str(e)
                asset.meta = m
                asset.save()
            except Exception as save_error:
                print(f"Failed to update asset status: {save_error}")

        return JsonResponse(
            {"id": asset_id, "status": asset_data["status"], "message": "נכס נוצר בהצלחה, העשרה תוזמנה"},
            status=201,
        )

    except Exception as e:
        print(f"Error creating asset: {e}")
        return JsonResponse({"error": "Failed to create asset", "details": str(e)}, status=500)

def _get_assets_list():
    """Helper להחזרת כל הנכסים בפורמט רשימות."""
    try:
        qs = Asset.objects.all().order_by("-created_at")
        rows = []

        for asset in qs:
            source_records = SourceRecord.objects.filter(asset_id=asset.id)
            all_sources = list(set([r.source for r in source_records]))

            if all_sources:
                for source in all_sources:
                    for record in [r for r in source_records if r.source == source]:
                        raw_data = record.raw or {}
                        listing = {
                            "id": f"asset_{asset.id}_{record.id}",
                            "external_id": record.external_id,
                            "address": asset.normalized_address or f"{(asset.street or '').strip()} {(asset.number or '')}".strip(),
                            "price": raw_data.get("price", 0),
                            "bedrooms": raw_data.get("rooms", 0),
                            "bathrooms": 1,
                            "area": raw_data.get("size", 0),
                            "type": raw_data.get("property_type", "דירה"),
                            "status": "active",
                            "images": raw_data.get("images", []),
                            "description": raw_data.get("description", ""),
                            "features": raw_data.get("features", []),
                            "contactInfo": {
                                "agent": raw_data.get("agent_name", ""),
                                "phone": raw_data.get("agent_phone", ""),
                                "email": raw_data.get("agent_email", ""),
                            },
                            "city": asset.city or "",
                            "neighborhood": asset.neighborhood or "",
                            "netSqm": raw_data.get("size", 0),
                            "pricePerSqm": round(raw_data.get("price", 0) / raw_data.get("size", 0))
                            if raw_data.get("price", 0) and raw_data.get("size", 0)
                            else 0,
                            "deltaVsAreaPct": 0,
                            "domPercentile": 50,
                            "competition1km": "בינוני",
                            "zoning": "מגורים א'",
                            "riskFlags": [],
                            "priceGapPct": 0,
                            "expectedPriceRange": "",
                            "remainingRightsSqm": 0,
                            "program": "",
                            "lastPermitQ": "",
                            "noiseLevel": 2,
                            "greenWithin300m": True,
                            "schoolsWithin500m": True,
                            "modelPrice": raw_data.get("price", 0),
                            "confidencePct": 75,
                            "capRatePct": 3.0,
                            "antennaDistanceM": 150,
                            "shelterDistanceM": 100,
                            "rentEstimate": round(raw_data.get("price", 0) * 0.004) if raw_data.get("price", 0) else 0,
                            "asset_id": asset.id,
                            "asset_status": asset.status,
                            "sources": all_sources,
                            "primary_source": source,
                        }
                        rows.append(listing)
            else:
                listing = {
                    "id": f"asset_{asset.id}",
                    "external_id": f"asset_{asset.id}",
                    "address": asset.normalized_address or f"{(asset.street or '').strip()} {(asset.number or '')}".strip(),
                    "price": 0,
                    "bedrooms": 0,
                    "bathrooms": 1,
                    "area": 0,
                    "type": "דירה",
                    "status": "active" if asset.status == "ready" else "pending",
                    "images": [],
                    "description": f"נכס {asset.scope_type} - {asset.city or ''}",
                    "features": [],
                    "contactInfo": {"agent": "", "phone": "", "email": ""},
                    "city": asset.city or "",
                    "neighborhood": asset.neighborhood or "",
                    "netSqm": 0,
                    "pricePerSqm": 0,
                    "deltaVsAreaPct": 0,
                    "domPercentile": 50,
                    "competition1km": "בינוני",
                    "zoning": "מגורים א'",
                    "riskFlags": [],
                    "priceGapPct": 0,
                    "expectedPriceRange": "",
                    "remainingRightsSqm": 0,
                    "program": "",
                    "lastPermitQ": "",
                    "noiseLevel": 2,
                    "greenWithin300m": True,
                    "schoolsWithin500m": True,
                    "modelPrice": 0,
                    "confidencePct": 75,
                    "capRatePct": 3.0,
                    "antennaDistanceM": 150,
                    "shelterDistanceM": 100,
                    "rentEstimate": 0,
                    "asset_id": asset.id,
                    "asset_status": asset.status,
                    "sources": [],
                    "primary_source": "asset",
                }
                rows.append(listing)

        return JsonResponse({"rows": rows})

    except Exception as e:
        print(f"Error fetching assets: {e}")
        return JsonResponse({"error": "Failed to fetch assets", "details": str(e)}, status=500)

@csrf_exempt
def asset_detail(request, asset_id):
    """קבלת פירוט נכס כולל נתוני העשרה ורשומות מקור."""
    if request.method != "GET":
        return JsonResponse({"error": "GET method required"}, status=405)

    try:
        try:
            asset = Asset.objects.get(id=asset_id)
        except Asset.DoesNotExist:
            return JsonResponse({"error": "נכס לא נמצא"}, status=404)

        source_records = SourceRecord.objects.filter(asset_id=asset_id)
        records_by_source = {}
        for record in source_records:
            records_by_source.setdefault(record.source, []).append(
                {
                    "id": record.id,
                    "title": record.title,
                    "external_id": record.external_id,
                    "url": record.url,
                    "file_path": record.file_path,
                    "raw": record.raw,
                    "fetched_at": record.fetched_at.isoformat() if record.fetched_at else None,
                }
            )

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
                    "fetched_at": trans.fetched_at.isoformat() if trans.fetched_at else None,
                }
            )

        return JsonResponse(
            {
                "id": asset.id,
                "scope_type": asset.scope_type,
                "city": asset.city,
                "neighborhood": asset.neighborhood,
                "street": asset.street,
                "number": asset.number,
                "gush": asset.gush,
                "helka": asset.helka,
                "lat": asset.lat,
                "lon": asset.lon,
                "normalized_address": asset.normalized_address,
                "status": asset.status,
                "meta": asset.meta,
                "created_at": asset.created_at.isoformat() if asset.created_at else None,
                "records": records_by_source,
                "transactions": transaction_list,
            }
        )

    except Exception as e:
        print(f"Error retrieving asset {asset_id}: {e}")
        return JsonResponse({"error": "Failed to retrieve asset", "details": str(e)}, status=500)

# -------------------------
# Marketing Message via LLM
# -------------------------

@api_view(["POST"])
@permission_classes([AllowAny])
def asset_share_message(request, asset_id):
    """יצירת הודעת שיווק לנכס באמצעות LLM."""
    try:
        asset = Asset.objects.get(id=asset_id)
    except Asset.DoesNotExist:
        return Response({"error": "נכס לא נמצא"}, status=status.HTTP_404_NOT_FOUND)

    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except json.JSONDecodeError:
        data = {}

    language_code = (data.get("language", "he") or "he").lower()
    supported = {"he": "Hebrew", "en": "English", "ru": "Russian", "fr": "French", "es": "Spanish", "ar": "Arabic"}
    language = supported.get(language_code, "Hebrew")

    address_parts = [asset.street or "", str(asset.number or ""), asset.city or "", asset.neighborhood or ""]
    address = " ".join([p for p in address_parts if p]).strip()
    prompt = (
        f"Create an engaging {language} marketing message for social media and messaging apps "
        f"about a property for sale located at {address}. Include key details like property type, "
        f"size and any selling points from this data: {json.dumps(asset.meta, ensure_ascii=False)}"
    )

    try:
        if not os.environ.get("OPENAI_API_KEY"):
            return Response(
                {
                    "error": "OpenAI API key not configured",
                    "details": "OPENAI_API_KEY environment variable is missing",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        client = OpenAI()
        completion = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": f"You write short real estate marketing messages in {language}."},
                {"role": "user", "content": prompt},
            ],
        )
        message = completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating marketing message: {str(e)}")
        return Response({"error": "Failed to generate message", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": message})