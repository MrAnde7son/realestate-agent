import json
import requests
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from .models import UserSettings


def parse_json(request):
    try:
        return json.loads(request.body.decode('utf-8'))
    except Exception:
        return None


@csrf_exempt
def register(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST method required')
    data = parse_json(request)
    if not data:
        return HttpResponseBadRequest('Invalid JSON')
    username = data.get('username')
    password = data.get('password')
    email = data.get('email', '')
    if not username or not password:
        return HttpResponseBadRequest('username and password required')
    if User.objects.filter(username=username).exists():
        return HttpResponseBadRequest('Username already exists')
    user = User.objects.create_user(username=username, password=password, email=email)
    return JsonResponse({'id': user.id, 'username': user.username})


@csrf_exempt
def google(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST method required')
    data = parse_json(request)
    if not data:
        return HttpResponseBadRequest('Invalid JSON')
    token = data.get('token')
    if not token:
        return HttpResponseBadRequest('token required')
    try:
        resp = requests.get('https://oauth2.googleapis.com/tokeninfo', params={'id_token': token}, timeout=5)
        info = resp.json()
        email = info.get('email')
        if not email:
            return HttpResponseBadRequest('Invalid token')
        username = info.get('name') or email.split('@')[0]
        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                'email': email,
                'first_name': info.get('given_name', ''),
                'last_name': info.get('family_name', ''),
            },
        )
        login(request, user)
        return JsonResponse({'id': user.id, 'username': user.username, 'created': created})
    except Exception:
        return HttpResponseBadRequest('Failed to verify token')


@csrf_exempt
def login_view(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST method required')
    data = parse_json(request)
    if not data:
        return HttpResponseBadRequest('Invalid JSON')
    username = data.get('username')
    password = data.get('password')
    user = authenticate(request, username=username, password=password)
    if user is None:
        return HttpResponseBadRequest('Invalid credentials')
    login(request, user)
    return JsonResponse({'message': 'Logged in'})


@csrf_exempt
def logout_view(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('POST method required')
    logout(request)
    return JsonResponse({'message': 'Logged out'})


@csrf_exempt
def profile(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    if request.method == 'GET':
        u = request.user
        return JsonResponse({
            'username': u.username,
            'email': u.email,
            'first_name': u.first_name,
            'last_name': u.last_name,
        })
    if request.method == 'POST':
        data = parse_json(request)
        if not data:
            return HttpResponseBadRequest('Invalid JSON')
        for field in ['first_name', 'last_name', 'email']:
            if field in data:
                setattr(request.user, field, data[field])
        request.user.save()
        return JsonResponse({'message': 'Profile updated'})
    return HttpResponseBadRequest('Unsupported method')


@csrf_exempt
def user_settings(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    if request.method == 'GET':
        return JsonResponse(settings_obj.data)
    if request.method == 'POST':
        data = parse_json(request)
        if not data:
            return HttpResponseBadRequest('Invalid JSON')
        settings_obj.data.update(data)
        settings_obj.save()
        return JsonResponse(settings_obj.data)
    return HttpResponseBadRequest('Unsupported method')
