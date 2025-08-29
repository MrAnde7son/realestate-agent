# backend-django/core/views.py

import json
import os
import re
import time
import statistics
import urllib.parse
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

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from bidi.algorithm import get_display

from .models import Alert

# Import Django models
from .models import Asset, SourceRecord, RealEstateTransaction, Report

# Import utility functions
try:
    from utils.tabu_parser import parse_tabu_pdf, search_rows
except ImportError:
    def parse_tabu_pdf(file):
        return []

    def search_rows(rows, query):
        return rows

# Import tasks
from .tasks import run_data_pipeline

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = os.environ.get(
    'REPORTS_DIR',
    str((BASE_DIR.parent / 'realestate-broker-ui' / 'public' / 'reports').resolve())
)

# ----------------------------
# Robust Hebrew font loading
# ----------------------------
_HEBREW_FONT_NAME = None  # will be set by _ensure_hebrew_font()

def _try_register_font(path: Path, name: str) -> bool:
    try:
        if path and path.exists():
            pdfmetrics.registerFont(TTFont(name, str(path)))
            return True
        return False
    except Exception:
        return False

def _ensure_hebrew_font() -> str:
    """
    Ensure we have a Hebrew-capable font registered and return its font name.
    Priority:
      1) CORE_HEBREW_FONT_PATH / REPORT_HEBREW_FONT / HEBREW_FONT_PATH env
      2) Project fonts: core/fonts/NotoSansHebrew-Regular.ttf, core/fonts/DejaVuSans.ttf
      3) Common system paths: DejaVuSans, NotoSansHebrew
    """
    global _HEBREW_FONT_NAME
    if _HEBREW_FONT_NAME:
        return _HEBREW_FONT_NAME

    candidates = []

    # 1) Environment overrides
    for var in ("CORE_HEBREW_FONT_PATH", "REPORT_HEBREW_FONT", "HEBREW_FONT_PATH"):
        env_path = os.environ.get(var)
        if env_path:
            candidates.append((Path(env_path), "HebrewFont"))

    # 2) Project-bundled paths
    candidates.extend([
        (BASE_DIR / "core" / "fonts" / "NotoSansHebrew-Regular.ttf", "NotoHebrew"),
        (BASE_DIR / "core" / "fonts" / "DejaVuSans.ttf", "DejaVu"),
    ])

    # 3) Common system paths
    candidates.extend([
        (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"), "DejaVu"),
        (Path("/usr/local/share/fonts/DejaVuSans.ttf"), "DejaVu"),
        (Path("/usr/share/fonts/truetype/noto/NotoSansHebrew-Regular.ttf"), "NotoHebrew"),
        (Path("/Library/Fonts/Arial Unicode.ttf"), "ArialUnicode"),  # macOS fallback
        (Path("C:/Windows/Fonts/arialuni.ttf"), "ArialUnicode"),      # Windows fallback
    ])

    for path, name in candidates:
        if _try_register_font(path, name):
            _HEBREW_FONT_NAME = name
            return _HEBREW_FONT_NAME

    # If we get here, no Hebrew font was found
    _HEBREW_FONT_NAME = None
    return None

def _draw_hebrew(c: canvas.Canvas, x: float, y: float, text: str, align: str = "right"):
    """
    Draw Hebrew (RTL) text safely with BiDi visual reordering.
    Requires that a Hebrew-capable TTF font was registered.
    """
    # Ensure we have a font; if not, we still draw something legible in Latin
    font_name = _ensure_hebrew_font()
    if font_name:
        try:
            c.setFont(font_name, 12)
        except Exception:
            pass

    # BiDi reorder for visual display
    try:
        safe_text = get_display(text)
    except Exception:
        safe_text = text

    if align == "center":
        c.drawCentredString(x, y, safe_text)
    elif align == "right":
        c.drawRightString(x, y, safe_text)
    else:
        c.drawString(x, y, safe_text)

def parse_json(request):
    try:
        return json.loads(request.body.decode('utf-8'))
    except Exception:
        return None

# ----------------------------
# Auth endpoints (unchanged)
# ----------------------------

@api_view(['POST'])
@permission_classes([AllowAny])
def auth_login(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=email, password=password)

        if user is None:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)

        return Response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'company': getattr(user, 'company', ''),
                'role': getattr(user, 'role', ''),
                'is_verified': getattr(user, 'is_verified', False),
            }
        })

    except json.JSONDecodeError:
        return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def auth_register(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        email = data.get('email')
        password = data.get('password')
        username = data.get('username')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        company = data.get('company', '')
        role = data.get('role', '')

        if not email or not password or not username:
            return Response(
                {'error': 'Email, password, and username are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=email).exists():
            return Response({'error': 'User with this email already exists'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already taken'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            company=company,
            role=role
        )

        refresh = RefreshToken.for_user(user)

        return Response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'company': getattr(user, 'company', ''),
                'role': getattr(user, 'role', ''),
                'is_verified': getattr(user, 'is_verified', False),
            }
        }, status=status.HTTP_201_CREATED)

    except json.JSONDecodeError:
        return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auth_logout(request):
    try:
        return Response({'message': 'Logged out successfully'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def auth_profile(request):
    try:
        user = request.user
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'company': getattr(user, 'company', ''),
                'role': getattr(user, 'role', ''),
                'is_verified': getattr(user, 'is_verified', False),
                'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') else None,
                'language': getattr(user, 'language', ''),
                'timezone': getattr(user, 'timezone', ''),
                'currency': getattr(user, 'currency', ''),
                'date_format': getattr(user, 'date_format', ''),
                'notify_email': getattr(user, 'notify_email', False),
                'notify_whatsapp': getattr(user, 'notify_whatsapp', False),
                'notify_urgent': getattr(user, 'notify_urgent', False),
                'notification_time': getattr(user, 'notification_time', ''),
            }
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def auth_update_profile(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        user = request.user

        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'company' in data:
            user.company = data['company']
        if 'role' in data:
            user.role = data['role']

        user.save()

        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'company': getattr(user, 'company', ''),
                'role': getattr(user, 'role', ''),
                'is_verified': getattr(user, 'is_verified', False),
            }
        })

    except json.JSONDecodeError:
        return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def auth_refresh(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        refresh_token = data.get('refresh_token')

        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)

        return Response({
            'access_token': access_token,
            'refresh_token': str(refresh),
        })

    except json.JSONDecodeError:
        return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

def _callback_url(request) -> str:
    return request.build_absolute_uri(reverse('auth_google_callback'))

@api_view(['GET'])
@permission_classes([AllowAny])
def auth_google_login(request):
    try:
        from django.conf import settings

        redirect_uri = _callback_url(request)
        params = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'offline',
            'prompt': 'consent',
        }
        auth_url = f"{settings.GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
        return Response({'auth_url': auth_url})

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def auth_google_callback(request):
    try:
        import requests
        from django.conf import settings
        from django.contrib.auth import get_user_model
        from django.contrib.auth.hashers import make_password
        from rest_framework_simplejwt.tokens import RefreshToken

        User = get_user_model()

        code = request.GET.get('code')
        if not code:
            return Response({'error': 'Authorization code not provided'}, status=status.HTTP_400_BAD_REQUEST)

        redirect_uri = _callback_url(request)
        token_data = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
        }

        token_response = requests.post(settings.GOOGLE_TOKEN_URL, data=token_data, timeout=10)
        token_info = token_response.json()
        if token_response.status_code != 200:
            return Response(token_info, status=status.HTTP_400_BAD_REQUEST)

        access_token = token_info.get('access_token')

        user_info_response = requests.get(
            settings.GOOGLE_USER_INFO_URL,
            headers={'Authorization': f'Bearer {access_token}'}
        )

        if not user_info_response.ok:
            return Response({'error': 'Failed to get user info from Google'}, status=status.HTTP_400_BAD_REQUEST)

        user_info = user_info_response.json()
        email = user_info.get('email')
        first_name = user_info.get('given_name', '')
        last_name = user_info.get('family_name', '')

        if not email:
            return Response({'error': 'Email not provided by Google'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            username = email.split('@')[0]
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=email,
                password=make_password(None),
                first_name=first_name,
                last_name=last_name,
                is_verified=True
            )

        refresh = RefreshToken.for_user(user)

        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        tokens = {
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'company': getattr(user, 'company', ''),
                'role': getattr(user, 'role', ''),
                'is_verified': getattr(user, 'is_verified', False),
            }
        }

        encoded_tokens = urllib.parse.urlencode(tokens)
        redirect_url = f"{frontend_url}/auth/google-callback?{encoded_tokens}"
        return redirect(redirect_url)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ----------------------------
# Settings & Alerts
# ----------------------------

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_settings(request):
    user = request.user
    if request.method == 'GET':
        return Response({
            'language': getattr(user, 'language', ''),
            'timezone': getattr(user, 'timezone', ''),
            'currency': getattr(user, 'currency', ''),
            'date_format': getattr(user, 'date_format', ''),
            'notify_email': getattr(user, 'notify_email', False),
            'notify_whatsapp': getattr(user, 'notify_whatsapp', False),
            'notify_urgent': getattr(user, 'notify_urgent', False),
            'notification_time': getattr(user, 'notification_time', ''),
        })

    if request.method == 'PUT':
        data = parse_json(request)
        if not data:
            return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)

        for field in [
            'language', 'timezone', 'currency', 'date_format',
            'notify_email', 'notify_whatsapp', 'notify_urgent',
            'notification_time'
        ]:
            if field in data:
                setattr(user, field, data[field])
        user.save()

        return Response({
            'language': user.language,
            'timezone': user.timezone,
            'currency': user.currency,
            'date_format': user.date_format,
            'notify_email': user.notify_email,
            'notify_whatsapp': user.notify_whatsapp,
            'notify_urgent': user.notify_urgent,
            'notification_time': user.notification_time,
        })

    return Response({'error': 'Unsupported method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def alerts(request):
    if request.method == 'POST':
        data = parse_json(request)
        if not data:
            return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)

        alert = Alert.objects.create(
            user=request.user,
            criteria=data.get('criteria') or {},
            notify=data.get('notify') or []
        )
        return Response({
            'id': alert.id,
            'created_at': alert.created_at.isoformat()
        }, status=status.HTTP_201_CREATED)

    if request.method == 'GET':
        user_alerts = Alert.objects.filter(user=request.user).order_by('-created_at')
        rows = [{
            'id': alert.id,
            'criteria': alert.criteria,
            'notify': alert.notify,
            'active': alert.active,
            'created_at': alert.created_at.isoformat()
        } for alert in user_alerts]
        return Response({'rows': rows})

    return Response({'error': 'Unsupported method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

# ----------------------------
# Address sync (unchanged)
# ----------------------------

@csrf_exempt
def sync_address(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    data = parse_json(request)
    if not data:
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)

    street = data.get('street', '').strip() if data.get('street') else None
    number = data.get('house_number')

    if not street or number is None:
        addr = (data.get('address') or '').strip()
        if not addr:
            return JsonResponse({'error': 'Either (street, house_number) or address is required'}, status=400)

        match = re.match(r'^(.+?)\s+(\d+)', addr)
        if match:
            street, number = match.group(1).strip(), match.group(2)
        else:
            return JsonResponse({'error': 'Could not parse address. Expected format: "Street Name Number"'}, status=400)

    if not street:
        return JsonResponse({'error': 'Street name is required'}, status=400)

    try:
        number = int(number)
        if number <= 0:
            return JsonResponse({'error': 'House number must be a positive integer'}, status=400)
    except (TypeError, ValueError):
        return JsonResponse({'error': 'House number must be a valid integer'}, status=400)

    try:
        asset = Asset.objects.create(
            scope_type='address',
            street=street,
            number=number,
            status='pending',
            meta={'radius': 150}
        )

        try:
            run_data_pipeline.delay(asset.id)
            message = f'Asset enrichment started for {street} {number} (Asset ID: {asset.id})'
        except Exception as e:
            message = f'Asset created but enrichment failed: {str(e)}'

        assets = [{
            'id': asset.id,
            'source': 'asset',
            'external_id': f'asset_{asset.id}',
            'title': f'Asset for {street} {number}',
            'address': f'{street} {number}',
            'status': asset.status,
            'message': message
        }]

        return JsonResponse({'rows': assets, 'message': message, 'address': f'{street} {number}'})
    except ValueError as e:
        return JsonResponse({'error': f'Validation error: {str(e)}'}, status=400)
    except Exception as e:
        import logging
        logging.exception("Unexpected error in sync_address: %s", e)
        return JsonResponse({'error': 'Internal server error occurred during address sync'}, status=500)

# ----------------------------
# Reports (PDF) — fixed Hebrew
# ----------------------------

@csrf_exempt
def reports(request):
    """Create a PDF report for a listing or list existing reports."""
    if request.method == 'GET':
        reports_list = []
        for report in Report.objects.all().order_by('-generated_at'):
            reports_list.append({
                'id': report.id,
                'assetId': report.asset.id if report.asset else None,
                'address': report.title or 'N/A',
                'filename': report.filename,
                'createdAt': report.generated_at.isoformat(),
                'status': report.status,
                'pages': report.pages,
                'fileSize': report.file_size,
            })
        return JsonResponse({'reports': reports_list})

    if request.method == 'DELETE':
        data = parse_json(request)
        if not data or not data.get('reportId'):
            return JsonResponse({'error': 'reportId required'}, status=400)

        try:
            report_id = int(data['reportId'])
            report = Report.objects.get(id=report_id)
            if report.delete_report():
                return JsonResponse({'message': f'Report {report_id} deleted successfully'}, status=200)
            else:
                return JsonResponse({'error': 'Failed to delete report'}, status=500)
        except Report.DoesNotExist:
            return JsonResponse({'error': 'Report not found'}, status=404)
        except ValueError:
            return JsonResponse({'error': 'Invalid report ID'}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'Error deleting report', 'details': str(e)}, status=500)

    if request.method != 'POST':
        return JsonResponse({'error': 'POST or DELETE required'}, status=405)

    data = parse_json(request)
    if not data or not data.get('assetId'):
        return JsonResponse({'error': 'assetId required'}, status=400)

    asset_id = data['assetId']

    mock_assets = {
        1: {
            'address': 'רחוב הרצל 123, תל אביב',
            'city': 'תל אביב',
            'neighborhood': 'מרכז העיר',
            'type': 'דירה',
            'price': 2850000,
            'bedrooms': 3,
            'bathrooms': 2,
            'netSqm': 85,
            'area': 85,
            'pricePerSqm': 33529,
            'remainingRightsSqm': 45,
            'program': 'תמ״א 38',
            'lastPermitQ': 'Q2/24',
            'noiseLevel': 2,
            'competition1km': 'בינוני',
            'zoning': 'מגורים א׳',
            'priceGapPct': -5.2,
            'expectedPriceRange': '2.7M - 3.0M',
            'modelPrice': 3000000,
            'confidencePct': 85,
            'capRatePct': 3.2,
            'rentEstimate': 9500,
            'riskFlags': [],
            'features': ['מעלית', 'חניה', 'מרפסת', 'משופצת'],
            'contactInfo': {
                'agent': 'יוסי כהן',
                'phone': '050-1234567',
                'email': 'yossi@example.com'
            },
            'documents': [
                {'name': 'נסח טאבו', 'type': 'tabu'},
                {'name': 'תשריט בית משותף', 'type': 'condo_plan'},
                {'name': 'היתר בנייה', 'type': 'permit'},
                {'name': 'זכויות בנייה', 'type': 'rights'},
                {'name': 'שומת מכרעת', 'type': 'appraisal_decisive'},
                {'name': 'שומת רמ״י', 'type': 'appraisal_rmi'}
            ]
        }
    }

    if asset_id not in mock_assets:
        return JsonResponse({'error': 'Asset not found'}, status=404)

    listing = mock_assets[asset_id]

    # Create report record
    report = Report.objects.create(
        asset=None,
        report_type='asset',
        status='generating',
        filename='',
        file_path='',
        title=listing['address'],
        description=f'Asset report for {listing["address"]}',
        pages=4,
    )

    filename = f"r{report.id}.pdf"
    os.makedirs(REPORTS_DIR, exist_ok=True)
    file_path = os.path.join(REPORTS_DIR, filename)

    report.filename = filename
    report.file_path = file_path
    report.save()

    start_time = time.time()

    try:
        c = canvas.Canvas(file_path, pagesize=A4)
        PAGE_WIDTH, PAGE_HEIGHT = A4
        RIGHT_MARGIN = PAGE_WIDTH - 50

        # Ensure Hebrew font before writing Hebrew text
        font_name = _ensure_hebrew_font()
        hebrew_font_ready = font_name is not None

        # Title
        try:
            if hebrew_font_ready:
                c.setFont(font_name, 20)
                _draw_hebrew(c, 300, 760, 'דו"ח נכס - ניתוח כללי', align='center')
            else:
                # Clear notice in English when font missing
                c.setFont("Helvetica", 11)
                c.drawCentredString(300, 770, 'Hebrew font not found - add core/fonts/NotoSansHebrew-Regular.ttf')
                c.setFont("Helvetica", 20)
                c.drawCentredString(300, 750, 'Asset Report - General Analysis')
        except Exception:
            c.setFont("Helvetica", 20)
            c.drawCentredString(300, 760, 'Asset Report - General Analysis')

        # Section: Asset Details
        y = 720
        if hebrew_font_ready:
            c.setFont(font_name, 14)
            _draw_hebrew(c, RIGHT_MARGIN, y, 'פרטי הנכס')
            y -= 25
            c.setFont(font_name, 12)
            _draw_hebrew(c, RIGHT_MARGIN, y, f"כתובת: {listing['address']}"); y -= 20
            _draw_hebrew(c, RIGHT_MARGIN, y, f"עיר: {listing['city']}"); y -= 20
            _draw_hebrew(c, RIGHT_MARGIN, y, f"שכונה: {listing['neighborhood']}"); y -= 20
            _draw_hebrew(c, RIGHT_MARGIN, y, f"סוג: {listing['type']}"); y -= 20
            _draw_hebrew(c, RIGHT_MARGIN, y, f"מחיר: ₪{int(listing['price']):,}"); y -= 20
            _draw_hebrew(c, RIGHT_MARGIN, y, f"חדרי שינה: {listing['bedrooms']}"); y -= 20
            _draw_hebrew(c, RIGHT_MARGIN, y, f"חדרי רחצה: {listing['bathrooms']}"); y -= 20
            _draw_hebrew(c, RIGHT_MARGIN, y, f"שטח (מ\"ר): {listing['netSqm']}"); y -= 20
            _draw_hebrew(c, RIGHT_MARGIN, y, f"מחיר למ\"ר: ₪{listing['pricePerSqm']:,}"); y -= 20
        else:
            c.setFont("Helvetica", 14)
            c.drawString(50, y, 'Asset Details'); y -= 25
            c.setFont("Helvetica", 12)
            c.drawString(50, y, f"Address: {listing['address']}"); y -= 20
            c.drawString(50, y, f"City: {listing['city']}"); y -= 20
            c.drawString(50, y, f"Neighborhood: {listing['neighborhood']}"); y -= 20
            c.drawString(50, y, f"Type: {listing['type']}"); y -= 20
            c.drawString(50, y, f"Price: ₪{int(listing['price']):,}"); y -= 20
            c.drawString(50, y, f"Bedrooms: {listing['bedrooms']}"); y -= 20
            c.drawString(50, y, f"Bathrooms: {listing['bathrooms']}"); y -= 20
            c.drawString(50, y, f"Area (sqm): {listing['netSqm']}"); y -= 20
            c.drawString(50, y, f"Price per sqm: ₪{listing['pricePerSqm']:,}"); y -= 20

        # Section: Financial Analysis
        y -= 20
        if hebrew_font_ready:
            c.setFont(font_name, 14)
            _draw_hebrew(c, RIGHT_MARGIN, y, 'אנליזה פיננסית'); y -= 25
            c.setFont(font_name, 12)
            _draw_hebrew(c, RIGHT_MARGIN, y, f"מחיר מודל: ₪{listing['modelPrice']:,}"); y -= 20
            _draw_hebrew(c, RIGHT_MARGIN, y, f"פער מחיר: {listing['priceGapPct']}%"); y -= 20
            _draw_hebrew(c, RIGHT_MARGIN, y, f"שכירות משוערת: ₪{listing['rentEstimate']:,}"); y -= 20
            _draw_hebrew(c, RIGHT_MARGIN, y, f"תשואה שנתית: {listing['capRatePct']}%"); y -= 20
            _draw_hebrew(c, RIGHT_MARGIN, y, f"תחרות (1 ק\"מ): {listing['competition1km']}"); y -= 20
        else:
            c.setFont("Helvetica", 14)
            c.drawString(50, y, 'Financial Analysis'); y -= 25
            c.setFont("Helvetica", 12)
            c.drawString(50, y, f"Model price: ₪{listing['modelPrice']:,}"); y -= 20
            c.drawString(50, y, f"Price gap: {listing['priceGapPct']}%"); y -= 20
            c.drawString(50, y, f"Rent estimate: ₪{listing['rentEstimate']:,}"); y -= 20
            c.drawString(50, y, f"Cap rate: {listing['capRatePct']}%"); y -= 20
            c.drawString(50, y, f"Competition 1km: {listing['competition1km']}"); y -= 20

        # Investment Recommendation
        y -= 20
        price_gap = listing['priceGapPct']
        if price_gap < -10:
            recommendation = "הנכס במחיר אטרקטיבי מתחת לשוק"
        elif price_gap > 10:
            recommendation = "הנכס יקר יחסית לשוק"
        else:
            recommendation = "הנכס במחיר שוק הוגן"

        cap_component = listing['capRatePct'] * 20
        gap_component = (100 + price_gap) if price_gap < 0 else (100 - price_gap)
        overall_score = round((listing['confidencePct'] + cap_component + gap_component) / 3)

        if hebrew_font_ready:
            c.setFont(font_name, 14)
            _draw_hebrew(c, RIGHT_MARGIN, y, 'המלצת השקעה'); y -= 25
            c.setFont(font_name, 12)
            _draw_hebrew(c, RIGHT_MARGIN, y, f"ציון כללי: {overall_score}/100"); y -= 20
            _draw_hebrew(c, RIGHT_MARGIN, y, f"המלצה: {recommendation}")
        else:
            c.setFont("Helvetica", 14)
            c.drawString(50, y, 'Investment Recommendation'); y -= 25
            c.setFont("Helvetica", 12)
            c.drawString(50, y, f"Overall Score: {overall_score}/100"); y -= 20
            c.drawString(50, y, f"Recommendation: priced fairly/over/under relative to market")

        c.showPage()

        # Page 2: Plans
        if hebrew_font_ready:
            c.setFont(font_name, 20)
            _draw_hebrew(c, 300, 760, 'תוכניות וזכויות בנייה', align='center')
            c.setFont(font_name, 14)
            y = 720
            _draw_hebrew(c, RIGHT_MARGIN, y, 'תוכניות מקומיות ומפורטות'); y -= 25
            c.setFont(font_name, 12)
            _draw_hebrew(c, RIGHT_MARGIN, y, f"תוכנית נוכחית: {listing['program']}"); y -= 20
            _draw_hebrew(c, RIGHT_MARGIN, y, f"אזור תכנון: {listing['zoning']}"); y -= 20
            _draw_hebrew(c, RIGHT_MARGIN, y, f"יתרת זכויות: +{listing['remainingRightsSqm']} מ\"ר"); y -= 20
            _draw_hebrew(c, RIGHT_MARGIN, y, f"זכויות בנייה עיקריות: {listing['netSqm']} מ\"ר"); y -= 20

            y -= 20
            c.setFont(font_name, 14)
            _draw_hebrew(c, RIGHT_MARGIN, y, 'זכויות בנייה מפורטות'); y -= 25
            c.setFont(font_name, 12)
            _draw_hebrew(c, RIGHT_MARGIN, y, f"יתרת זכויות: {listing['remainingRightsSqm']} מ\"ר"); y -= 20
            extra_pct = round((listing['remainingRightsSqm'] / listing['netSqm']) * 100) if listing['netSqm'] else 0
            _draw_hebrew(c, RIGHT_MARGIN, y, f"אחוז זכויות נוספות: {extra_pct}%"); y -= 20
            rights_value = round((listing['pricePerSqm'] * listing['remainingRightsSqm'] * 0.7) / 1000)
            _draw_hebrew(c, RIGHT_MARGIN, y, f"שווי זכויות משוער: ₪{rights_value} אלף")
        else:
            c.setFont("Helvetica", 20)
            c.drawCentredString(300, 760, 'Plans and Building Rights')
            c.setFont("Helvetica", 12)
            y = 720
            c.drawString(50, y, f"Program: {listing['program']}"); y -= 20
            c.drawString(50, y, f"Zoning: {listing['zoning']}"); y -= 20

        c.showPage()

        # Page 3: Environment
        if hebrew_font_ready:
            c.setFont(font_name, 20)
            _draw_hebrew(c, 300, 760, 'מידע סביבתי', align='center')
            c.setFont(font_name, 14)
            y = 720
            _draw_hebrew(c, RIGHT_MARGIN, y, 'מידע סביבתי'); y -= 25
            c.setFont(font_name, 12)
            _draw_hebrew(c, RIGHT_MARGIN, y, f"רמת רעש: {listing['noiseLevel']}/5"); y -= 20
            _draw_hebrew(c, RIGHT_MARGIN, y, 'שטחים ציבוריים ≤300מ׳: כן'); y -= 20
            _draw_hebrew(c, RIGHT_MARGIN, y, 'מרחק אנטנה: 150מ׳'); y -= 20

            y -= 20
            c.setFont(font_name, 14)
            _draw_hebrew(c, RIGHT_MARGIN, y, 'סיכונים'); y -= 25
            c.setFont(font_name, 12)
            if listing['riskFlags']:
                for flag in listing['riskFlags']:
                    _draw_hebrew(c, RIGHT_MARGIN, y, f"• {flag}"); y -= 20
            else:
                _draw_hebrew(c, RIGHT_MARGIN, y, "אין סיכונים מיוחדים")
        else:
            c.setFont("Helvetica", 20)
            c.drawCentredString(300, 760, 'Environmental Information')
            c.setFont("Helvetica", 12)
            y = 720
            c.drawString(50, y, "Noise: 2/5")

        c.showPage()

        # Page 4: Documents & Summary
        if hebrew_font_ready:
            c.setFont(font_name, 20)
            _draw_hebrew(c, 300, 760, 'מסמכים וסיכום', align='center')
            c.setFont(font_name, 14)
            y = 720
            _draw_hebrew(c, RIGHT_MARGIN, y, 'מסמכים זמינים'); y -= 25
            c.setFont(font_name, 12)
            if listing['documents']:
                for doc in listing['documents']:
                    _draw_hebrew(c, RIGHT_MARGIN, y, f"• {doc['name']} ({doc['type']})"); y -= 20
            else:
                _draw_hebrew(c, RIGHT_MARGIN, y, "אין מסמכים זמינים")

            y -= 30
            c.setFont(font_name, 14)
            _draw_hebrew(c, RIGHT_MARGIN, y, 'פרטי קשר'); y -= 25
            c.setFont(font_name, 12)
            if listing['contactInfo']:
                _draw_hebrew(c, RIGHT_MARGIN, y, f"סוכן: {listing['contactInfo']['agent']}"); y -= 20
                _draw_hebrew(c, RIGHT_MARGIN, y, f"טלפון: {listing['contactInfo']['phone']}"); y -= 20
                _draw_hebrew(c, RIGHT_MARGIN, y, f"אימייל: {listing['contactInfo']['email']}")
        else:
            c.setFont("Helvetica", 20)
            c.drawCentredString(300, 760, 'Documents and Summary')

        c.save()

        generation_time = time.time() - start_time
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        report.mark_completed(file_size=file_size, pages=4, generation_time=generation_time)

    except Exception as e:
        report.mark_failed(str(e))
        return JsonResponse({'error': 'PDF generation failed', 'details': str(e)}, status=500)

    return JsonResponse({
        'report': {
            'id': report.id,
            'assetId': asset_id,
            'address': listing['address'],
            'filename': filename,
            'createdAt': report.generated_at.isoformat(),
            'status': report.status,
            'pages': report.pages,
            'fileSize': report.file_size,
        }
    }, status=201)

# ----------------------------
# Mortgage analyzer (unchanged)
# ----------------------------

def _group_by_month(transactions):
    months = {}
    for t in transactions:
        try:
            d = datetime.fromisoformat((t.get('date','') or '')[:10])
        except Exception:
            continue
        key = d.strftime('%Y-%m'); amt = float(t.get('amount') or 0)
        months.setdefault(key, {'income':0.0,'expense':0.0,'net':0.0,'txs':0})
        if amt >= 0: months[key]['income'] += amt
        else: months[key]['expense'] += abs(amt)
        months[key]['net'] += amt; months[key]['txs'] += 1
    return months

def _median(lst):
    lst = [x for x in lst if x is not None]
    if not lst: return 0.0
    try: return float(statistics.median(lst))
    except statistics.StatisticsError: return float(lst[0])

def _annuity_max_loan(payment, annual_rate_pct, term_years):
    r = (annual_rate_pct/100.0) / 12.0; n = term_years * 12
    if r <= 0: return payment * n
    return payment * (1 - (1 + r) ** (-n)) / r

@csrf_exempt
def mortgage_analyze(request):
    if request.method != 'POST': return JsonResponse({'error': 'POST required'}, status=405)
    data = parse_json(request)
    if not data: return JsonResponse({'error': 'Invalid JSON'}, status=400)
    price = float(data.get('property_price') or 0); savings = float(data.get('savings_total') or 0)
    annual_rate_pct = float(data.get('annual_rate_pct') or 4.5); term_years = int(data.get('term_years') or 25)
    transactions = data.get('transactions') or []
    months = _group_by_month(transactions); keys = sorted(months.keys())[-6:]
    incomes = [months[k]['income'] for k in keys]; expenses = [months[k]['expense'] for k in keys]
    med_income = _median(incomes); med_expense = _median(expenses); surplus = med_income - med_expense
    safety = med_income * 0.10
    recommended_payment = max(0.0, min(med_income * 0.30, surplus - safety))
    def annuity_max_loan(payment, annual_rate_pct, term_years):
        r = (annual_rate_pct/100.0)/12.0; n = term_years*12
        if r <= 0: return payment*n
        return payment * (1 - (1+r)**(-n)) / r
    max_loan_from_payment = annuity_max_loan(recommended_payment, annual_rate_pct, term_years)
    max_loan_by_ltv = price * 0.70 if price > 0 else max_loan_from_payment
    approved_loan_ceiling = min(max_loan_from_payment, max_loan_by_ltv)
    cash_needed = max(0.0, price - approved_loan_ceiling); cash_gap = max(0.0, cash_needed - savings)
    return JsonResponse({
        'metrics': { 'median_monthly_income': round(med_income), 'median_monthly_expense': round(med_expense), 'monthly_surplus_estimate': round(surplus) },
        'recommendation': { 'recommended_monthly_payment': round(recommended_payment), 'max_loan_from_payment': round(max_loan_from_payment), 'max_loan_by_ltv': round(max_loan_by_ltv), 'approved_loan_ceiling': round(approved_loan_ceiling), 'cash_gap_for_purchase': round(cash_gap) },
        'notes': ['אינפורמטיבי בלבד', f'LTV 70%, ריבית {annual_rate_pct}%, תקופה {term_years}y']
    })

# ----------------------------
# Tabu parsing (unchanged)
# ----------------------------

@csrf_exempt
def tabu(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'error': 'file required'}, status=400)
    try:
        rows = parse_tabu_pdf(file)
        query = request.GET.get('q') or ''
        if query:
            rows = search_rows(rows, query)
        return JsonResponse({'rows': rows})
    except Exception as e:
        print(f"Error parsing tabu PDF: {e}")
        return JsonResponse({'rows': [{
            'id': 1, 'gush': '1234', 'helka': '56', 'owner': 'בעלים לדוגמה', 'area': '150', 'usage': 'מגורים'
        }]})

# ----------------------------
# Assets list + details (fixed shadowing)
# ----------------------------

@csrf_exempt
def assets(request):
    if request.method == 'GET':
        return _get_assets_list()

    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    data = parse_json(request)
    if not data:
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)

    try:
        scope = data.get('scope', {})
        scope_type = scope.get('type')
        if not scope_type:
            return JsonResponse({'error': 'Scope type is required'}, status=400)

        asset_data = {
            'scope_type': scope_type,
            'city': data.get('city') or scope.get('city'),
            'neighborhood': data.get('neighborhood'),
            'street': data.get('street'),
            'number': data.get('number'),
            'gush': data.get('gush'),
            'helka': data.get('helka'),
            'status': 'pending',
            'meta': {
                'scope': scope,
                'raw_input': data,
                'radius': data.get('radius', 150)
            }
        }

        asset = Asset.objects.create(**asset_data)
        asset_id = asset.id

        try:
            run_data_pipeline.delay(asset_id)
        except Exception as e:
            print(f"Failed to enqueue enrichment task: {e}")
            try:
                asset = Asset.objects.get(id=asset_id)
                asset.status = 'error'
                meta = asset.meta or {}
                meta['error'] = str(e)
                asset.meta = meta
                asset.save()
            except Exception as save_error:
                print(f"Failed to update asset status: {save_error}")

        return JsonResponse({
            'id': asset_id,
            'status': asset_data['status'],
            'message': 'Asset created successfully, enrichment pipeline started'
        }, status=201)

    except Exception as e:
        print(f"Error creating asset: {e}")
        return JsonResponse({'error': 'Failed to create asset', 'details': str(e)}, status=500)

def _get_assets_list():
    try:
        qs = Asset.objects.all().order_by('-created_at')
        listings = []

        for asset in qs:
            source_records = SourceRecord.objects.filter(asset_id=asset.id)
            all_sources = list(set([r.source for r in source_records]))

            if all_sources:
                for source in all_sources:
                    source_records_for_source = [r for r in source_records if r.source == source]
                    for record in source_records_for_source:
                        raw_data = record.raw or {}
                        listing = {
                            'id': f'asset_{asset.id}_{record.id}',
                            'external_id': record.external_id,
                            'address': asset.normalized_address or f"{asset.street or ''} {asset.number or ''}".strip(),
                            'price': raw_data.get('price', 0),
                            'bedrooms': raw_data.get('rooms', 0),
                            'bathrooms': 1,
                            'area': raw_data.get('size', 0),
                            'type': raw_data.get('property_type', 'דירה'),
                            'status': 'active',
                            'images': raw_data.get('images', []),
                            'description': raw_data.get('description', ''),
                            'features': raw_data.get('features', []),
                            'contactInfo': {
                                'agent': raw_data.get('agent_name', ''),
                                'phone': raw_data.get('agent_phone', ''),
                                'email': raw_data.get('agent_email', '')
                            },
                            'city': asset.city or '',
                            'neighborhood': asset.neighborhood or '',
                            'netSqm': raw_data.get('size', 0),
                            'pricePerSqm': round(raw_data.get('price', 0) / raw_data.get('size', 0)) if raw_data.get('price', 0) and raw_data.get('size', 0) else 0,
                            'deltaVsAreaPct': 0,
                            'domPercentile': 50,
                            'competition1km': 'בינוני',
                            'zoning': 'מגורים א\'',
                            'riskFlags': [],
                            'priceGapPct': 0,
                            'expectedPriceRange': '',
                            'remainingRightsSqm': 0,
                            'program': '',
                            'lastPermitQ': '',
                            'noiseLevel': 2,
                            'greenWithin300m': True,
                            'schoolsWithin500m': True,
                            'modelPrice': raw_data.get('price', 0),
                            'confidencePct': 75,
                            'capRatePct': 3.0,
                            'antennaDistanceM': 150,
                            'shelterDistanceM': 100,
                            'rentEstimate': round(raw_data.get('price', 0) * 0.004) if raw_data.get('price', 0) else 0,
                            'asset_id': asset.id,
                            'asset_status': asset.status,
                            'sources': all_sources,
                            'primary_source': source
                        }
                        listings.append(listing)
            else:
                listing = {
                    'id': f'asset_{asset.id}',
                    'external_id': f'asset_{asset.id}',
                    'address': asset.normalized_address or f"{asset.street or ''} {asset.number or ''}".strip(),
                    'price': 0,
                    'bedrooms': 0,
                    'bathrooms': 1,
                    'area': 0,
                    'type': 'דירה',
                    'status': 'active' if asset.status == 'ready' else 'pending',
                    'images': [],
                    'description': f'נכס {asset.scope_type} - {asset.city or ""}',
                    'features': [],
                    'contactInfo': { 'agent': '', 'phone': '', 'email': '' },
                    'city': asset.city or '',
                    'neighborhood': asset.neighborhood or '',
                    'netSqm': 0,
                    'pricePerSqm': 0,
                    'deltaVsAreaPct': 0,
                    'domPercentile': 50,
                    'competition1km': 'בינוני',
                    'zoning': 'מגורים א\'',
                    'riskFlags': [],
                    'priceGapPct': 0,
                    'expectedPriceRange': '',
                    'remainingRightsSqm': 0,
                    'program': '',
                    'lastPermitQ': '',
                    'noiseLevel': 2,
                    'greenWithin300m': True,
                    'schoolsWithin500m': True,
                    'modelPrice': 0,
                    'confidencePct': 75,
                    'capRatePct': 3.0,
                    'antennaDistanceM': 150,
                    'shelterDistanceM': 100,
                    'rentEstimate': 0,
                    'asset_id': asset.id,
                    'asset_status': asset.status,
                    'sources': [],
                    'primary_source': 'asset'
                }
                listings.append(listing)

        return JsonResponse({'rows': listings})

    except Exception as e:
        print(f"Error fetching assets: {e}")
        return JsonResponse({'error': 'Failed to fetch assets', 'details': str(e)}, status=500)

@csrf_exempt
def asset_detail(request, asset_id):
    if request.method != 'GET':
        return JsonResponse({'error': 'GET method required'}, status=405)

    try:
        try:
            asset = Asset.objects.get(id=asset_id)
        except Asset.DoesNotExist:
            return JsonResponse({'error': 'Asset not found'}, status=404)

        source_records = SourceRecord.objects.filter(asset_id=asset_id)
        records_by_source = {}
        for record in source_records:
            records_by_source.setdefault(record.source, []).append({
                'id': record.id,
                'title': record.title,
                'external_id': record.external_id,
                'url': record.url,
                'file_path': record.file_path,
                'raw': record.raw,
                'fetched_at': record.fetched_at.isoformat() if record.fetched_at else None
            })

        transactions = RealEstateTransaction.objects.filter(asset_id=asset_id)
        transaction_list = []
        for trans in transactions:
            transaction_list.append({
                'id': trans.id,
                'deal_id': trans.deal_id,
                'date': trans.date.isoformat() if trans.date else None,
                'price': trans.price,
                'rooms': trans.rooms,
                'area': trans.area,
                'floor': trans.floor,
                'address': trans.address,
                'raw': trans.raw,
                'fetched_at': trans.fetched_at.isoformat() if trans.fetched_at else None
            })

        return JsonResponse({
            'id': asset.id,
            'scope_type': asset.scope_type,
            'city': asset.city,
            'neighborhood': asset.neighborhood,
            'street': asset.street,
            'number': asset.number,
            'gush': asset.gush,
            'helka': asset.helka,
            'lat': asset.lat,
            'lon': asset.lon,
            'normalized_address': asset.normalized_address,
            'status': asset.status,
            'meta': asset.meta,
            'created_at': asset.created_at.isoformat() if asset.created_at else None,
            'records': records_by_source,
            'transactions': transaction_list
        })

    except Exception as e:
        print(f"Error retrieving asset {asset_id}: {e}")
        return JsonResponse({'error': 'Failed to retrieve asset', 'details': str(e)}, status=500)

# ----------------------------
# LLM marketing message (unchanged)
# ----------------------------

@api_view(['POST'])
@permission_classes([AllowAny])
def asset_share_message(request, asset_id):
    try:
        asset = Asset.objects.get(id=asset_id)
    except Asset.DoesNotExist:
        return Response({'error': 'Asset not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        data = {}

    language_code = data.get('language', 'he').lower()
    supported = {
        'he': 'Hebrew',
        'en': 'English',
        'ru': 'Russian',
        'fr': 'French',
        'es': 'Spanish',
        'ar': 'Arabic',
    }
    language = supported.get(language_code, 'Hebrew')

    address_parts = [asset.street or '', str(asset.number or ''), asset.city or '', asset.neighborhood or '']
    address = ' '.join([p for p in address_parts if p]).strip()
    prompt = (
        f"Create an engaging {language} marketing message for social media and messaging apps "
        f"about a property for sale located at {address}. Include key details like property type, "
        f"size and any selling points from this data: {json.dumps(asset.meta, ensure_ascii=False)}"
    )

    try:
        if not os.environ.get('OPENAI_API_KEY'):
            return Response(
                {'error': 'OpenAI API key not configured', 'details': 'OPENAI_API_KEY environment variable is missing'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        client = OpenAI()
        completion = client.chat.completions.create(
            model=os.environ.get('OPENAI_MODEL', 'gpt-4o-mini'),
            messages=[
                {"role": "system", "content": f"You write short real estate marketing messages in {language}."},
                {"role": "user", "content": prompt},
            ],
        )
        message = completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating marketing message: {str(e)}")
        return Response({'error': 'Failed to generate message', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'message': message})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password or not new_password:
            return Response({'error': 'Current password and new password are required'}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response({'error': 'New password must be at least 8 characters long'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not user.check_password(current_password):
            return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

        if user.check_password(new_password):
            return Response({'error': 'New password must be different from current password'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password changed successfully'})

    except json.JSONDecodeError:
        return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)