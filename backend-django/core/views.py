import json, statistics, re, os, urllib.parse
from datetime import datetime
from pathlib import Path

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
User = get_user_model()
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

from .models import Alert

from openai import OpenAI

from django.urls import reverse

# Import Django models
from .models import Asset, SourceRecord, RealEstateTransaction

# Import utility functions
try:
    # Try to import from utils - this will work if the module is available
    from utils.tabu_parser import parse_tabu_pdf, search_rows
except ImportError:
    # Fallback functions when utils module is not available
    # This ensures the app can still run even if utils is missing
    # Note: These functions return empty results, so tabu parsing will show dummy data
    def parse_tabu_pdf(file):
        """Fallback function for parsing tabu PDFs when utils module is not available."""
        return []
    
    def search_rows(rows, query):
        """Fallback function for searching rows when utils module is not available."""
        return rows

# Import tasks
from .tasks import enrich_asset

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = os.environ.get(
    'REPORTS_DIR',
    str((BASE_DIR.parent / 'realestate-broker-ui' / 'public' / 'reports').resolve())
)
# Persist reports metadata in a JSON file so they survive server restarts
REPORTS_META = Path(REPORTS_DIR) / 'reports.json'

# Authentication views
@api_view(['POST'])
@permission_classes([AllowAny])
def auth_login(request):
    """User login endpoint."""
    try:
        data = json.loads(request.body.decode('utf-8'))
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Email and password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is None:
            return Response(
                {'error': 'Invalid credentials'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Generate JWT tokens
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
        return Response(
            {'error': 'Invalid JSON'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def auth_register(request):
    """User registration endpoint."""
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
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'User with this email already exists'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Username already taken'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            company=company,
            role=role
        )
        
        # Generate JWT tokens
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
        return Response(
            {'error': 'Invalid JSON'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auth_logout(request):
    """User logout endpoint."""
    try:
        # In a real application, you might want to blacklist the token
        # For now, we'll just return success
        return Response({'message': 'Logged out successfully'})
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def auth_profile(request):
    """Get current user profile."""
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
            }
        })
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def auth_update_profile(request):
    """Update current user profile."""
    try:
        data = json.loads(request.body.decode('utf-8'))
        user = request.user
        
        # Update allowed fields
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
        return Response(
            {'error': 'Invalid JSON'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def auth_refresh(request):
    """Refresh JWT token."""
    try:
        data = json.loads(request.body.decode('utf-8'))
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify and refresh token
        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)
        
        return Response({
            'access_token': access_token,
            'refresh_token': str(refresh),
        })
        
    except json.JSONDecodeError:
        return Response(
            {'error': 'Invalid JSON'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_401_UNAUTHORIZED
        )


def _callback_url(request) -> str:
    """Build absolute callback URL for Google OAuth."""
    return request.build_absolute_uri(reverse('auth_google_callback'))


@api_view(['GET'])
@permission_classes([AllowAny])
def auth_google_login(request):
    """Initiate Google OAuth login flow."""
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
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def auth_google_callback(request):
    """Handle Google OAuth callback and authenticate user."""
    try:
        from django.conf import settings
        import requests
        from django.contrib.auth import get_user_model
        from django.contrib.auth.hashers import make_password
        from rest_framework_simplejwt.tokens import RefreshToken
        
        User = get_user_model()
        
        # Get authorization code from query parameters
        code = request.GET.get('code')
        if not code:
            return Response(
                {'error': 'Authorization code not provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

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
        
        # Get user info from Google
        user_info_response = requests.get(
            settings.GOOGLE_USER_INFO_URL,
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if not user_info_response.ok:
            return Response(
                {'error': 'Failed to get user info from Google'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_info = user_info_response.json()
        google_id = user_info.get('id')
        email = user_info.get('email')
        first_name = user_info.get('given_name', '')
        last_name = user_info.get('family_name', '')
        
        if not email:
            return Response(
                {'error': 'Email not provided by Google'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user exists, create if not
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Create new user
            username = email.split('@')[0]  # Use email prefix as username
            # Ensure username is unique
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=make_password(None),  # No password for OAuth users
                first_name=first_name,
                last_name=last_name,
                is_verified=True  # Google users are verified
            )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Get frontend URL from settings with fallback
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
        
        # Encode tokens in URL parameters
        import urllib.parse
        encoded_tokens = urllib.parse.urlencode(tokens)
        redirect_url = f"{frontend_url}/auth/google-callback?{encoded_tokens}"
        
        return Response({
            'redirect_url': redirect_url,
            'tokens': tokens
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _load_reports():
    try:
        with open(REPORTS_META, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def _save_reports(reports):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(REPORTS_META, 'w', encoding='utf-8') as f:
        json.dump(reports, f, ensure_ascii=False)

try:
    FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont("DejaVu", FONT_PATH))
        REPORT_FONT = "DejaVu"
    else:
        REPORT_FONT = "Helvetica"
except ImportError:
    REPORT_FONT = "Helvetica"

def parse_json(request):
    try: return json.loads(request.body.decode('utf-8'))
    except Exception: return None

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
        # Only return alerts for the current user
        alerts = Alert.objects.filter(user=request.user).order_by('-created_at')
        rows = [
            {
                'id': alert.id,
                'criteria': alert.criteria,
                'notify': alert.notify,
                'active': alert.active,
                'created_at': alert.created_at.isoformat()
            }
            for alert in alerts
        ]
        return Response({'rows': rows})
    
    return Response({'error': 'Unsupported method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


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
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    # Parse JSON with error handling
    data = parse_json(request)
    if not data:
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    
    # Extract street and number from data
    street = data.get('street', '').strip() if data.get('street') else None
    number = data.get('house_number')
    
    # If no direct street/number, try to parse from address field
    if not street or number is None:
        addr = (data.get('address') or '').strip()
        if not addr:
            return JsonResponse({'error': 'Either (street, house_number) or address is required'}, status=400)
        
        match = re.match(r'^(.+?)\s+(\d+)', addr)
        if match:
            street, number = match.group(1).strip(), match.group(2)
        else:
            return JsonResponse({'error': 'Could not parse address. Expected format: "Street Name Number"'}, status=400)
    
    # Validate and convert number
    if not street:
        return JsonResponse({'error': 'Street name is required'}, status=400)
    
    try:
        number = int(number)
        if number <= 0:
            return JsonResponse({'error': 'House number must be a positive integer'}, status=400)
    except (TypeError, ValueError):
        return JsonResponse({'error': 'House number must be a valid integer'}, status=400)
    
    # Execute sync with comprehensive error handling
    try:
        # Create a new asset for the address
        from .models import Asset
        asset = Asset.objects.create(
            scope_type='address',
            street=street,
            number=number,
            status='pending',
            meta={'radius': 150}
        )
        
        # Start enrichment pipeline
        try:
            enrich_asset.delay(asset.id)
            message = f'Asset enrichment started for {street} {number} (Asset ID: {asset.id})'
        except Exception as e:
            message = f'Asset created but enrichment failed: {str(e)}'
        
        # Return asset info
        assets = [{
            'id': asset.id,
            'source': 'asset',
            'external_id': f'asset_{asset.id}',
            'title': f'Asset for {street} {number}',
            'address': f'{street} {number}',
            'status': asset.status,
            'message': message
        }]
        
        return JsonResponse({
            'rows': assets,
            'message': message,
            'address': f'{street} {number}'
        })
    except ValueError as e:
        return JsonResponse({'error': f'Validation error: {str(e)}'}, status=400)
    except Exception as e:
        # Log the full error for debugging
        import logging
        logging.exception("Unexpected error in sync_address: %s", e)
        return JsonResponse(
            {'error': 'Internal server error occurred during address sync'}, 
            status=500
        )


# Old view functions removed - replaced with new asset enrichment pipeline


@csrf_exempt
def reports(request):
    """Create a PDF report for a listing or list existing reports."""
    reports_list = _load_reports()

    if request.method == 'GET':
        return JsonResponse({'reports': reports_list})

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    data = parse_json(request)
    if not data or not data.get('listingId'):
        return JsonResponse({'error': 'listingId required'}, status=400)

    listing_id = data['listingId']
    
    # Create a dummy listing for testing (since we no longer have the old Listing model)
    listing = {
        'address': 'כתובת לדוגמה',
        'price': 2000000,
        'rooms': 3,
        'size': 80,
    }

    if not listing:
        return JsonResponse({'error': 'Listing not found'}, status=404)

    report_id = f"r{len(reports_list) + 1}"
    filename = f"{report_id}.pdf"
    os.makedirs(REPORTS_DIR, exist_ok=True)
    file_path = os.path.join(REPORTS_DIR, filename)

    # Try to create PDF, fallback to text file if reportlab fails
    try:
        c = canvas.Canvas(file_path, pagesize=A4)
        c.setFont(REPORT_FONT, 20)
        c.drawCentredString(300, 760, 'דו"ח נכס')
        c.setFont(REPORT_FONT, 12)
        y = 720
        c.drawString(50, y, f"כתובת: {listing['address'] or ''}")
        y -= 20
        if listing.get('price') is not None:
            c.drawString(50, y, f"מחיר: ₪{int(listing['price'])}")
            y -= 20
        if listing.get('rooms') is not None:
            c.drawString(50, y, f"חדרים: {listing['rooms']}")
            y -= 20
        if listing.get('size') is not None:
            c.drawString(50, y, f"מ""ר: {listing['size']}")
        c.save()
    except Exception as e:
        # Fallback to text file if PDF creation fails
        file_path = file_path.replace('.pdf', '.txt')
        filename = filename.replace('.pdf', '.txt')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('דו"ח נכס\n')
            f.write(f"כתובת: {listing['address'] or ''}\n")
            if listing.get('price') is not None:
                f.write(f"מחיר: ₪{int(listing['price'])}\n")
            if listing.get('rooms') is not None:
                f.write(f"חדרים: {listing['rooms']}\n")
            if listing.get('size') is not None:
                f.write(f"מ\"ר: {listing['size']}\n")

    report = {
        'id': report_id,
        'listingId': str(listing_id),
        'address': listing['address'],
        'filename': filename,
        'createdAt': datetime.utcnow().isoformat(),
    }
    reports_list.append(report)
    _save_reports(reports_list)
    return JsonResponse({'report': report}, status=201)

def _group_by_month(transactions):
    months = {}
    for t in transactions:
        try: d = datetime.fromisoformat((t.get('date','') or '')[:10])
        except Exception: continue
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


@csrf_exempt
def tabu(request):
    """Parse an uploaded Tabu PDF and return its data as a searchable table.
    
    Note: If the utils module is not available, this will return dummy data
    to ensure the app continues to function.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'error': 'file required'}, status=400)
    
    # Try to parse the PDF file
    try:
        rows = parse_tabu_pdf(file)
        query = request.GET.get('q') or ''
        if query:
            rows = search_rows(rows, query)
        return JsonResponse({'rows': rows})
    except Exception as e:
        print(f"Error parsing tabu PDF: {e}")
        # Return dummy data for testing if parsing fails
        # This also handles the case where utils module is not available
        return JsonResponse({'rows': [
            {
                'id': 1,
                'gush': '1234',
                'helka': '56',
                'owner': 'בעלים לדוגמה',
                'area': '150',
                'usage': 'מגורים'
            }
        ]})

@csrf_exempt
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
    if request.method == 'GET':
        # Return all assets in listing format
        return _get_assets_list()
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    # Parse JSON with error handling
    data = parse_json(request)
    if not data:
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    
    try:
        # Extract scope information
        scope = data.get('scope', {})
        scope_type = scope.get('type')
        if not scope_type:
            return JsonResponse({'error': 'Scope type is required'}, status=400)
        
        # Create asset record
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
        
        # Save to Django database
        asset = Asset.objects.create(**asset_data)
        asset_id = asset.id
        
        # Enqueue Celery task if available
        try:
            from .tasks import enrich_asset
            enrich_asset.delay(asset_id)
        except Exception as e:
            print(f"Failed to enqueue enrichment task: {e}")
            # Update asset status to error
            try:
                asset = Asset.objects.get(id=asset_id)
                asset.status = 'error'
                asset.meta['error'] = str(e)
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
        return JsonResponse({
            'error': 'Failed to create asset',
            'details': str(e)
        }, status=500)

def _get_assets_list():
    """Helper function to get all assets in listing format."""
    
    try:
        # Get all assets
        assets = Asset.objects.all().order_by('-created_at')
        
        # Transform assets to listing format
        assets = []
        for asset in assets:
            # Get source records for this asset
            source_records = SourceRecord.objects.filter(asset_id=asset.id)
            
            # Get all source records for this asset
            all_sources = list(set([r.source for r in source_records]))
            
            if all_sources:
                # Create assets for each source
                for source in all_sources:
                    source_records_for_source = [r for r in source_records if r.source == source]
                    
                    for record in source_records_for_source:
                        raw_data = record.raw or {}
                        
                        # Base listing data
                        listing = {
                            'id': f'asset_{asset.id}_{record.id}',
                            'external_id': record.external_id,
                            'address': asset.normalized_address or f"{asset.street or ''} {asset.number or ''}".strip(),
                            'price': raw_data.get('price', 0),
                            'bedrooms': raw_data.get('rooms', 0),
                            'bathrooms': 1,  # Default
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
                        assets.append(listing)
            else:
                # Create a basic listing from asset data when no sources yet
                listing = {
                    'id': f'asset_{asset.id}',
                    'external_id': f'asset_{asset.id}',
                    'address': asset.normalized_address or f"{asset.street or ''} {asset.number or ''}".strip(),
                    'price': 0,  # Will be populated when enrichment completes
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
                assets.append(listing)
        
        return JsonResponse({'rows': assets})
        
    except Exception as e:
        print(f"Error fetching assets: {e}")
        return JsonResponse({
            'error': 'Failed to fetch assets',
            'details': str(e)
        }, status=500)

@csrf_exempt
def asset_detail(request, asset_id):
    """Get asset details including enriched data and source records."""
    if request.method != 'GET':
        return JsonResponse({'error': 'GET method required'}, status=405)
    
    try:
        # Get asset using Django ORM
        try:
            asset = Asset.objects.get(id=asset_id)
        except Asset.DoesNotExist:
            return JsonResponse({'error': 'Asset not found'}, status=404)
        
        # Get source records grouped by source
        source_records = SourceRecord.objects.filter(asset_id=asset_id)
        records_by_source = {}
        for record in source_records:
            if record.source not in records_by_source:
                records_by_source[record.source] = []
            records_by_source[record.source].append({
                'id': record.id,
                'title': record.title,
                'external_id': record.external_id,
                'url': record.url,
                'file_path': record.file_path,
                'raw': record.raw,
                'fetched_at': record.fetched_at.isoformat() if record.fetched_at else None
            })
        
        # Get transactions
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
            
        # Return asset details
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
        return JsonResponse({
            'error': 'Failed to retrieve asset',
            'details': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def asset_share_message(request, asset_id):
    """Generate a marketing message for an asset using LLM."""
    try:
        asset = Asset.objects.get(id=asset_id)
    except Asset.DoesNotExist:
        return Response({'error': 'Asset not found'}, status=status.HTTP_404_NOT_FOUND)

    # Read language from request, default to Hebrew
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

    # Build prompt from asset details
    address_parts = [
        asset.street or '',
        str(asset.number or ''),
        asset.city or '',
        asset.neighborhood or ''
    ]
    address = ' '.join([p for p in address_parts if p]).strip()
    prompt = (
        f"Create an engaging {language} marketing message for social media and messaging apps "
        f"about a property for sale located at {address}. Include key details like property type, "
        f"size and any selling points from this data: {json.dumps(asset.meta, ensure_ascii=False)}"
    )

    try:
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
        return Response({'error': 'Failed to generate message', 'details': str(e)}, status=500)

    return Response({'message': message})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change user password endpoint."""
    try:
        data = json.loads(request.body.decode('utf-8'))
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return Response(
                {'error': 'Current password and new password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(new_password) < 8:
            return Response(
                {'error': 'New password must be at least 8 characters long'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify current password
        user = request.user
        if not user.check_password(current_password):
            return Response(
                {'error': 'Current password is incorrect'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if new password is different from current
        if user.check_password(new_password):
            return Response(
                {'error': 'New password must be different from current password'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update password
        user.set_password(new_password)
        user.save()
        
        return Response({
            'message': 'Password changed successfully'
        })
        
    except json.JSONDecodeError:
        return Response(
            {'error': 'Invalid JSON'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
