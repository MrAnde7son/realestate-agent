import json, statistics, re, os
from datetime import datetime
from pathlib import Path

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
try:
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.pagesizes import A4
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    # Dummy classes for when reportlab is not available
    class canvas:
        class Canvas:
            def __init__(self, *args, **kwargs):
                pass
            def setFont(self, *args, **kwargs):
                pass
            def drawCentredString(self, *args, **kwargs):
                pass
            def drawString(self, *args, **kwargs):
                pass
            def save(self):
                pass
    
    class pdfmetrics:
        @staticmethod
        def registerFont(*args, **kwargs):
            pass
    
    class TTFont:
        def __init__(self, *args, **kwargs):
            pass
    
    class A4:
        pass

from .models import Alert

# Import database models - using relative imports for Django compatibility
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from db.database import SQLAlchemyDatabase
    from db.models import (
        Listing,
        BuildingPermit,
        BuildingRights,
        DecisiveAppraisal,
        RamiValuation,
    )
    from utils.tabu_parser import parse_tabu_pdf, search_rows
    DB_AVAILABLE = True
except ImportError:
    # If external modules aren't available, create dummy classes
    class SQLAlchemyDatabase:
        def get_session(self):
            class DummySession:
                def query(self, model):
                    return DummyQuery()
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    pass
            return DummySession()
    
    class DummyQuery:
        def all(self):
            return []
        def order_by(self, field):
            return self
        def desc(self):
            return self
    
    class Listing:
        pass
    
    class BuildingPermit:
        pass
    
    class BuildingRights:
        pass
    
    class DecisiveAppraisal:
        pass
    
    class RamiValuation:
        pass
    
    def parse_tabu_pdf(file):
        return []
    
    def search_rows(rows, query):
        return rows
    
    DB_AVAILABLE = False

try:
    from .tasks import sync_address_sources
    TASKS_AVAILABLE = True
except ImportError:
    # Create a dummy function if tasks module isn't available
    def sync_address_sources(street, number):
        return []
    TASKS_AVAILABLE = False

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
    - 200: {"rows": [...]} - List of found listings
    - 400: Error message for invalid input
    - 500: Error message for server errors
    """
    if request.method != 'POST':
        return HttpResponseBadRequest('POST method required')
    
    # Parse JSON with error handling
    data = parse_json(request)
    if not data:
        return HttpResponseBadRequest('Invalid JSON in request body')
    
    # Extract street and number from data
    street = data.get('street', '').strip() if data.get('street') else None
    number = data.get('house_number')
    
    # If no direct street/number, try to parse from address field
    if not street or number is None:
        addr = (data.get('address') or '').strip()
        if not addr:
            return HttpResponseBadRequest('Either (street, house_number) or address is required')
        
        match = re.match(r'^(.+?)\s+(\d+)', addr)
        if match:
            street, number = match.group(1).strip(), match.group(2)
        else:
            return HttpResponseBadRequest('Could not parse address. Expected format: "Street Name Number"')
    
    # Validate and convert number
    if not street:
        return HttpResponseBadRequest('Street name is required')
    
    try:
        number = int(number)
        if number <= 0:
            return HttpResponseBadRequest('House number must be a positive integer')
    except (TypeError, ValueError):
        return HttpResponseBadRequest('House number must be a valid integer')
    
    # Execute sync with comprehensive error handling
    try:
        if not DB_AVAILABLE or not TASKS_AVAILABLE:
            # Return dummy data for testing
            listings = [
                {
                    'id': 1,
                    'source': 'demo',
                    'external_id': 'demo_123',
                    'title': f'נכס לדוגמה ב{street} {number}',
                    'price': 2500000,
                    'address': f'{street} {number}',
                    'rooms': 4,
                    'floor': 2,
                    'size': 120,
                    'property_type': 'דירה',
                    'description': 'נכס לדוגמה לבדיקת המערכת',
                    'images': [],
                    'contact_info': {'phone': '050-123-4567'},
                    'features': ['מרפסת', 'חניה', 'מעלית'],
                    'url': '#',
                    'date_posted': datetime.now().isoformat(),
                    'scraped_at': datetime.now().isoformat(),
                }
            ]
            message = f'Demo data for {street} {number} (external dependencies not available)'
        else:
            listings = sync_address_sources(street, number)
            message = f'Successfully synced data for {street} {number}'
        
        return JsonResponse({
            'rows': listings,
            'message': message,
            'address': f'{street} {number}'
        })
    except ValueError as e:
        return HttpResponseBadRequest(f'Validation error: {str(e)}')
    except Exception as e:
        # Log the full error for debugging
        import logging
        logging.exception("Unexpected error in sync_address: %s", e)
        return JsonResponse(
            {'error': 'Internal server error occurred during address sync'}, 
            status=500
        )


def listings(request):
    """Return all listings from the SQL database."""
    if not DB_AVAILABLE:
        return JsonResponse({'rows': [], 'message': 'External database not available'})
    
    db = SQLAlchemyDatabase()
    with db.get_session() as session:
        rows = session.query(Listing).order_by(Listing.id.desc()).all()
        data = [
            {
                'id': l.id,
                'source': l.source,
                'external_id': l.external_id,
                'title': l.title,
                'price': l.price,
                'address': l.address,
                'rooms': l.rooms,
                'floor': l.floor,
                'size': l.size,
                'property_type': l.property_type,
                'description': l.description,
                'images': l.images,
                'contact_info': l.contact_info,
                'features': l.features,
                'url': l.url,
                'date_posted': l.date_posted,
                'scraped_at': l.scraped_at.isoformat() if l.scraped_at else None,
            }
            for l in rows
        ]
    return JsonResponse({'rows': data})


def building_permits(request):
    """Return stored building permits."""
    if not DB_AVAILABLE:
        return JsonResponse({'rows': [], 'message': 'External database not available'})
    
    db = SQLAlchemyDatabase()
    with db.get_session() as session:
        rows = session.query(BuildingPermit).order_by(BuildingPermit.id.desc()).all()
        data = [
            {
                'id': p.id,
                'permission_num': p.permission_num,
                'request_num': p.request_num,
                'url': p.url,
                'gush': p.gush,
                'helka': p.helka,
                'data': p.data,
                'scraped_at': p.scraped_at.isoformat() if p.scraped_at else None,
            }
            for p in rows
        ]
    return JsonResponse({'rows': data})


def building_rights(request):
    """Return stored building rights pages."""
    if not DB_AVAILABLE:
        return JsonResponse({'rows': [], 'message': 'External database not available'})
    
    db = SQLAlchemyDatabase()
    with db.get_session() as session:
        rows = session.query(BuildingRights).order_by(BuildingRights.id.desc()).all()
        data = [
            {
                'id': r.id,
                'gush': r.gush,
                'helka': r.helka,
                'file_path': r.file_path,
                'content_type': r.content_type,
                'data': r.data,
                'scraped_at': r.scraped_at.isoformat() if r.scraped_at else None,
            }
            for r in rows
        ]
    return JsonResponse({'rows': data})


def decisive_appraisals(request):
    """Return decisive appraisal decisions."""
    if not DB_AVAILABLE:
        return JsonResponse({'rows': [], 'message': 'External database not available'})
    
    db = SQLAlchemyDatabase()
    with db.get_session() as session:
        rows = session.query(DecisiveAppraisal).order_by(DecisiveAppraisal.id.desc()).all()
        data = [
            {
                'id': d.id,
                'title': d.title,
                'date': d.date,
                'appraiser': d.appraiser,
                'committee': d.committee,
                'pdf_url': d.pdf_url,
                'data': d.data,
                'scraped_at': d.scraped_at.isoformat() if d.scraped_at else None,
            }
            for d in rows
        ]
    return JsonResponse({'rows': data})


def rami_valuations(request):
    """Return RAMI valuation/plan records."""
    if not DB_AVAILABLE:
        return JsonResponse({'rows': [], 'message': 'External database not available'})
    
    db = SQLAlchemyDatabase()
    with db.get_session() as session:
        rows = session.query(RamiValuation).order_by(RamiValuation.id.desc()).all()
        data = [
            {
                'id': r.id,
                'plan_number': r.plan_number,
                'name': r.name,
                'data': r.data,
                'scraped_at': r.scraped_at.isoformat() if r.scraped_at else None,
            }
            for r in rows
        ]
    return JsonResponse({'rows': data})


@csrf_exempt
def reports(request):
    """Create a PDF report for a listing or list existing reports."""
    reports_list = _load_reports()

    if request.method == 'GET':
        return JsonResponse({'reports': reports_list})

    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    data = parse_json(request)
    if not data or not data.get('listingId'):
        return HttpResponseBadRequest('listingId required')

    listing_id = data['listingId']
    
    if not DB_AVAILABLE:
        # Create a dummy listing for testing
        listing = {
            'address': 'כתובת לדוגמה',
            'price': 2000000,
            'rooms': 3,
            'size': 80,
        }
    else:
        db = SQLAlchemyDatabase()
        with db.get_session() as session:
            l = session.get(Listing, int(listing_id))
            listing = (
                {
                    'address': l.address,
                    'price': l.price,
                    'rooms': l.rooms,
                    'size': l.size,
                }
                if l
                else None
            )

    if not listing:
        return JsonResponse({'error': 'Listing not found'}, status=404)

    report_id = f"r{len(reports_list) + 1}"
    filename = f"{report_id}.pdf"
    os.makedirs(REPORTS_DIR, exist_ok=True)
    file_path = os.path.join(REPORTS_DIR, filename)

    if REPORTLAB_AVAILABLE:
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
    else:
        # If reportlab is not available, create a simple text file
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
    if request.method != 'POST': return HttpResponseBadRequest('POST required')
    data = parse_json(request)
    if not data: return HttpResponseBadRequest('Invalid JSON')
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
    """Parse an uploaded Tabu PDF and return its data as a searchable table."""
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')
    file = request.FILES.get('file')
    if not file:
        return HttpResponseBadRequest('file required')
    
    if not DB_AVAILABLE:
        # Return dummy data for testing
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
    
    rows = parse_tabu_pdf(file)
    query = request.GET.get('q') or ''
    if query:
        rows = search_rows(rows, query)
    return JsonResponse({'rows': rows})
