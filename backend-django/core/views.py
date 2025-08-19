import json, statistics, re, os
from datetime import datetime
from pathlib import Path

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from reportlab.pdfgen import canvas

from .models import Alert

from db.database import SQLAlchemyDatabase
from db.models import (
    Listing,
    BuildingPermit,
    BuildingRights,
    DecisiveAppraisal,
    RamiValuation,
)
from .tasks import sync_address_sources
from utils.tabu_parser import parse_tabu_pdf, search_rows

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = os.environ.get(
    'REPORTS_DIR',
    str((BASE_DIR.parent / 'realestate-broker-ui' / 'public' / 'reports').resolve())
)
REPORTS = []

def parse_json(request):
    try: return json.loads(request.body.decode('utf-8'))
    except Exception: return None

@csrf_exempt
def alerts(request):
    if request.method == 'POST':
        data = parse_json(request)
        if not data: return HttpResponseBadRequest('Invalid JSON')
        alert = Alert.objects.create(user_id=data.get('user_id') or 'unknown', criteria=data.get('criteria') or {}, notify=data.get('notify') or [])
        return JsonResponse({'id': alert.id, 'created_at': alert.created_at.isoformat()})
    if request.method == 'GET':
        rows = list(Alert.objects.values('id','user_id','criteria','notify','active','created_at').order_by('-id'))
        return JsonResponse({'rows': rows})
    return HttpResponseBadRequest('Unsupported method')


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
        listings = sync_address_sources(street, number)
        return JsonResponse({
            'rows': listings,
            'message': f'Successfully synced data for {street} {number}',
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
    if request.method == 'GET':
        return JsonResponse({'reports': REPORTS})

    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')

    data = parse_json(request)
    if not data or not data.get('listingId'):
        return HttpResponseBadRequest('listingId required')

    listing_id = data['listingId']
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

    report_id = f"r{len(REPORTS) + 1}"
    filename = f"{report_id}.pdf"
    os.makedirs(REPORTS_DIR, exist_ok=True)
    file_path = os.path.join(REPORTS_DIR, filename)

    c = canvas.Canvas(file_path)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(300, 760, 'דו"ח נכס')
    c.setFont("Helvetica", 12)
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

    report = {
        'id': report_id,
        'listingId': str(listing_id),
        'address': listing['address'],
        'filename': filename,
        'createdAt': datetime.utcnow().isoformat(),
    }
    REPORTS.append(report)
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
    rows = parse_tabu_pdf(file)
    query = request.GET.get('q') or ''
    if query:
        rows = search_rows(rows, query)
    return JsonResponse({'rows': rows})
