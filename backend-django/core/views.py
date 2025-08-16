import json, statistics
from datetime import datetime
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .models import Alert

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
