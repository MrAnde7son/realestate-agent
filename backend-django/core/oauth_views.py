# -*- coding: utf-8 -*-
"""
OAuth 2.0 views for authentication flows.

Provides OAuth 2.0 Authorization Code flow endpoints for MCP server, API clients,
and other third-party integrations.
"""
import json
import logging
from urllib.parse import urlencode
from django.http import JsonResponse, HttpResponseRedirect, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import timedelta

from .models import OAuthAuthorizationCode, APIToken

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def oauth_authorize(request: HttpRequest):
    """
    OAuth 2.0 Authorization endpoint.
    
    GET: Show authorization page
    POST: Handle user authorization decision
    """
    # Get OAuth parameters
    response_type = request.GET.get('response_type', '')
    client_id = request.GET.get('client_id', '')
    redirect_uri = request.GET.get('redirect_uri', '')
    scope = request.GET.get('scope', '')
    state = request.GET.get('state', '')
    code_challenge = request.GET.get('code_challenge', '')
    code_challenge_method = request.GET.get('code_challenge_method', 'S256')
    
    # Validate required parameters
    if response_type != 'code':
        return JsonResponse({
            'error': 'unsupported_response_type',
            'error_description': 'Only authorization code flow is supported'
        }, status=400)
    
    if not client_id or not redirect_uri:
        return JsonResponse({
            'error': 'invalid_request',
            'error_description': 'client_id and redirect_uri are required'
        }, status=400)
    
    # Handle POST (user authorization decision)
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'unauthorized',
                'error_description': 'User must be authenticated'
            }, status=401)
        
        # Check if user approved
        approved = request.POST.get('approved') == 'true'
        
        if not approved:
            # User denied authorization
            error_params = {
                'error': 'access_denied',
                'error_description': 'User denied the request'
            }
            if state:
                error_params['state'] = state
            
            redirect_url = f"{redirect_uri}?{urlencode(error_params)}"
            return HttpResponseRedirect(redirect_url)
        
        # User approved - create authorization code
        auth_code = OAuthAuthorizationCode.generate_code()
        expires_at = timezone.now() + timedelta(minutes=10)  # 10 minute expiry
        
        OAuthAuthorizationCode.objects.create(
            code=auth_code,
            user=request.user,
            client_id=client_id,
            redirect_uri=redirect_uri,
            code_challenge=code_challenge if code_challenge else None,
            code_challenge_method=code_challenge_method if code_challenge else 'plain',
            scope=scope,
            expires_at=expires_at
        )
        
        # Redirect with authorization code
        params = {
            'code': auth_code,
        }
        if state:
            params['state'] = state
        
        redirect_url = f"{redirect_uri}?{urlencode(params)}"
        return HttpResponseRedirect(redirect_url)
    
    # Handle GET - show authorization page
    # If user is not authenticated, redirect to login
    if not request.user.is_authenticated:
        # Store OAuth params in session for after login
        request.session['oauth_params'] = {
            'response_type': response_type,
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': scope,
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': code_challenge_method,
        }
        # Redirect to login with return URL
        login_url = f"/api/auth/login?next={request.get_full_path()}"
        return redirect(login_url)
    
    # User is authenticated - show authorization page
    scopes = scope.split() if scope else []
    scope_descriptions = {
        'read': 'לקרוא את הנתונים שלך',
        'write': 'לשנות את הנתונים שלך',
        'assets': 'לגשת לנכסים שלך',
        'deals': 'לגשת לעסקאות שלך',
        'crm': 'לגשת לנתוני CRM שלך',
    }
    
    context = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scopes': [scope_descriptions.get(s, s) for s in scopes],
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': code_challenge_method,
    }
    
    # Simple HTML form for authorization
    return render(request, 'oauth/authorize.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def oauth_token(request: HttpRequest):
    """
    OAuth 2.0 Token endpoint.
    
    Exchanges authorization code for access token.
    """
    # Parse request body (can be form-encoded or JSON)
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'invalid_request',
                'error_description': 'Invalid JSON'
            }, status=400)
    else:
        data = request.POST
    
    grant_type = data.get('grant_type', '')
    
    if grant_type != 'authorization_code':
        return JsonResponse({
            'error': 'unsupported_grant_type',
            'error_description': f'Grant type {grant_type} is not supported'
        }, status=400)
    
    code = data.get('code', '')
    redirect_uri = data.get('redirect_uri', '')
    client_id = data.get('client_id', '')
    code_verifier = data.get('code_verifier', '')
    
    if not code:
        return JsonResponse({
            'error': 'invalid_request',
            'error_description': 'Authorization code is required'
        }, status=400)
    
    # Find authorization code
    try:
        auth_code = OAuthAuthorizationCode.objects.get(code=code)
    except OAuthAuthorizationCode.DoesNotExist:
        return JsonResponse({
            'error': 'invalid_grant',
            'error_description': 'Invalid authorization code'
        }, status=400)
    
    # Validate authorization code
    if not auth_code.is_valid():
        return JsonResponse({
            'error': 'invalid_grant',
            'error_description': 'Authorization code expired or already used'
        }, status=400)
    
    # Verify client_id and redirect_uri match
    if auth_code.client_id != client_id:
        return JsonResponse({
            'error': 'invalid_client',
            'error_description': 'Client ID mismatch'
        }, status=400)
    
    if auth_code.redirect_uri != redirect_uri:
        return JsonResponse({
            'error': 'invalid_request',
            'error_description': 'Redirect URI mismatch'
        }, status=400)
    
    # Verify PKCE if code challenge was provided
    if auth_code.code_challenge:
        if not code_verifier:
            return JsonResponse({
                'error': 'invalid_request',
                'error_description': 'code_verifier is required for PKCE'
            }, status=400)
        
        if not auth_code.verify_code_verifier(code_verifier):
            return JsonResponse({
                'error': 'invalid_grant',
                'error_description': 'Invalid code verifier'
            }, status=400)
    
    # Mark code as used
    auth_code.mark_used()
    
    # Create or get API token for the user
    token_name = f"MCP OAuth Token ({client_id})"
    api_token = APIToken.objects.filter(
        user=auth_code.user,
        name=token_name
    ).first()
    
    if not api_token or not api_token.is_valid():
        # Create new token
        token_value = APIToken.generate_token()
        api_token = APIToken.objects.create(
            user=auth_code.user,
            name=token_name,
            token=token_value,
        )
    
    # Return access token
    return JsonResponse({
        'access_token': api_token.token,
        'token_type': 'Bearer',
        'expires_in': None,  # API tokens don't expire by default
        'scope': auth_code.scope,
    })


@csrf_exempt
@require_http_methods(["POST"])
def oauth_register(request: HttpRequest):
    """
    OAuth 2.0 Dynamic Client Registration endpoint (RFC 7591).
    
    Allows clients like ChatGPT to dynamically register themselves.
    For MCP servers, we accept any client registration and return the client_id.
    """
    # Parse request body (can be form-encoded or JSON)
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'invalid_request',
                'error_description': 'Invalid JSON'
            }, status=400)
    else:
        # Convert POST data to dict
        data = dict(request.POST)
        # Convert single-item lists to values
        data = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in data.items()}
    
    # Extract client information
    client_name = data.get('client_name', 'MCP Client')
    redirect_uris = data.get('redirect_uris', [])
    if isinstance(redirect_uris, str):
        redirect_uris = [redirect_uris]
    
    # Generate or use provided client_id
    client_id = data.get('client_id')
    if not client_id:
        # Generate a simple client_id (in production, you might want to store this)
        import secrets
        client_id = f"mcp-client-{secrets.token_urlsafe(16)}"
    
    # Generate client_secret (optional for public clients)
    client_secret = data.get('client_secret')
    if not client_secret and data.get('token_endpoint_auth_method') != 'none':
        import secrets
        client_secret = secrets.token_urlsafe(32)
    
    # Determine base path for OAuth endpoints
    base_url = request.build_absolute_uri('/').rstrip('/')
    path = request.path
    if '/mcp/oauth' in path:
        oauth_base = f'{base_url}/mcp/oauth'
    else:
        oauth_base = f'{base_url}/api/oauth'
    
    # Return client registration response (RFC 7591 format)
    response_data = {
        'client_id': client_id,
        'client_id_issued_at': int(timezone.now().timestamp()),
        'client_name': client_name,
        'redirect_uris': redirect_uris,
        'grant_types': ['authorization_code'],
        'response_types': ['code'],
        'token_endpoint_auth_method': data.get('token_endpoint_auth_method', 'client_secret_basic'),
        'scope': ' '.join(['read', 'write', 'assets', 'deals', 'crm']),
    }
    
    # Include client_secret if provided/generated (only on initial registration)
    if client_secret:
        response_data['client_secret'] = client_secret
        response_data['client_secret_expires_at'] = 0  # 0 means never expires
    
    return JsonResponse(response_data, status=201)


@require_http_methods(["GET"])
def oauth_metadata(request: HttpRequest):
    """
    OAuth 2.0 Authorization Server Metadata endpoint.
    
    Returns OAuth server metadata for discovery.
    Automatically detects if called from /mcp/oauth/*, /mcp/.well-known/*, or /api/oauth/* 
    and returns appropriate endpoints.
    """
    base_url = request.build_absolute_uri('/').rstrip('/')
    path = request.path
    
    # Determine base path for OAuth endpoints based on request path
    # Check for MCP context (either /mcp/oauth/* or /mcp/.well-known/*)
    if '/mcp/oauth' in path or '/mcp/.well-known' in path:
        # Called from MCP endpoint - return MCP-specific OAuth URLs
        oauth_base = f'{base_url}/mcp/oauth'
    else:
        # Called from general API endpoint - return general OAuth URLs
        oauth_base = f'{base_url}/api/oauth'
    
    return JsonResponse({
        'issuer': base_url,
        'authorization_endpoint': f'{oauth_base}/authorize',
        'token_endpoint': f'{oauth_base}/token',
        'registration_endpoint': f'{oauth_base}/register',  # RFC 7591 Dynamic Client Registration
        'scopes_supported': ['read', 'write', 'assets', 'deals', 'crm'],
        'response_types_supported': ['code'],
        'code_challenge_methods_supported': ['plain', 'S256'],
        'grant_types_supported': ['authorization_code'],
        'token_endpoint_auth_methods_supported': ['client_secret_basic', 'client_secret_post', 'none'],
    })

