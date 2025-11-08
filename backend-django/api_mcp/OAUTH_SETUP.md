# OAuth 2.0 Setup for MCP Server

This guide explains how to set up OAuth 2.0 authentication for the MCP server to enable ChatGPT to access authenticated endpoints.

## Overview

The MCP server implements OAuth 2.0 Authorization Code flow with PKCE (Proof Key for Code Exchange) support. This allows ChatGPT to securely authenticate users and access their data.

## Architecture

```
ChatGPT
  ↓ Initiates OAuth flow
Authorization Endpoint (/mcp/oauth/authorize)
  ↓ User authenticates & authorizes
Authorization Code
  ↓ ChatGPT exchanges code
Token Endpoint (/mcp/oauth/token)
  ↓ Returns access token
API Token (Bearer token)
  ↓ Used in requests
Authenticated API Endpoints
```

## Endpoints

### 1. Authorization Endpoint
- **URL**: `/mcp/oauth/authorize` (MCP-specific) or `/api/oauth/authorize` (general-purpose)
- **Method**: GET, POST
- **Purpose**: User authorization page

**Query Parameters:**
- `response_type`: Must be `code`
- `client_id`: Client identifier (any string, ChatGPT will use its own)
- `redirect_uri`: Where to redirect after authorization
- `scope`: Space-separated scopes (e.g., `read write assets`)
- `state`: Optional state parameter for CSRF protection
- `code_challenge`: PKCE code challenge (optional)
- `code_challenge_method`: `S256` or `plain` (default: `S256`)

### 2. Token Endpoint
- **URL**: `/mcp/oauth/token` (MCP-specific) or `/api/oauth/token` (general-purpose)
- **Method**: POST
- **Purpose**: Exchange authorization code for access token

**Request Body (JSON or form-encoded):**
```json
{
  "grant_type": "authorization_code",
  "code": "authorization_code_from_authorize_endpoint",
  "redirect_uri": "same_as_in_authorize",
  "client_id": "same_as_in_authorize",
  "code_verifier": "pkce_code_verifier_if_used"
}
```

**Response:**
```json
{
  "access_token": "api_token_value",
  "token_type": "Bearer",
  "expires_in": null,
  "scope": "read write assets"
}
```

### 3. Metadata Endpoint
- **URL**: `/mcp/oauth/metadata` (MCP-specific) or `/api/oauth/metadata` (general-purpose)

**Note**: The metadata endpoint automatically detects which path it was called from and returns appropriate endpoint URLs.
- **Method**: GET
- **Purpose**: OAuth server metadata discovery

**Response:**
```json
{
  "issuer": "https://yourdomain.com",
  "authorization_endpoint": "https://yourdomain.com/mcp/oauth/authorize",
  "token_endpoint": "https://yourdomain.com/mcp/oauth/token",
  "scopes_supported": ["read", "write", "assets", "deals", "crm"],
  "response_types_supported": ["code"],
  "code_challenge_methods_supported": ["plain", "S256"],
  "grant_types_supported": ["authorization_code"]
}
```

## Setup Steps

### 1. Run Migrations

```bash
cd backend-django
python manage.py migrate core
```

This creates the `OAuthAuthorizationCode` table in the core app for storing temporary authorization codes.

### 2. Configure Settings

Ensure your Django settings include:

```python
# In broker_backend/settings.py
INSTALLED_APPS = [
    # ... other apps
    'api_mcp',
]

# Templates directory
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,  # This enables template discovery
        # ...
    }
]
```

### 3. Deploy with HTTPS

OAuth requires HTTPS. For local testing, use:
- **ngrok**: `ngrok http 8000`
- **Cloudflare Tunnel**: For production-like testing

### 4. Configure ChatGPT Connector

1. Open ChatGPT → Settings → Apps & Connectors
2. Enable Developer mode
3. Click "Create" to add a new connector
4. Fill in:
   - **Connector Name**: Real Estate API
   - **Description**: Real estate API with OAuth authentication
   - **Connector URL**: `https://yourdomain.com/mcp`
   - **OAuth**: Enable OAuth
   - **Authorization URL**: `https://yourdomain.com/mcp/oauth/authorize`
   - **Token URL**: `https://yourdomain.com/mcp/oauth/token`
   - **Metadata URL**: `https://yourdomain.com/mcp/oauth/metadata` (optional)

## OAuth Flow

### Step 1: User Initiates Connection

When a user connects the MCP server in ChatGPT, ChatGPT will:
1. Generate a `client_id` (e.g., `chatgpt-client-12345`)
2. Generate PKCE `code_verifier` and `code_challenge`
3. Redirect user to authorization endpoint

### Step 2: User Authorization

User is redirected to:
```
https://yourdomain.com/mcp/oauth/authorize?
  response_type=code&
  client_id=chatgpt-client-12345&
  redirect_uri=https://chatgpt.com/oauth/callback&
  scope=read write assets&
  code_challenge=...&
  code_challenge_method=S256&
  state=random_state_string
```

If user is not logged in, they'll be redirected to login first.

### Step 3: User Approves

User sees authorization page and clicks "Authorize". The server:
1. Creates an authorization code
2. Stores it temporarily (10 minute expiry)
3. Redirects back to `redirect_uri` with code

### Step 4: Token Exchange

ChatGPT exchanges the code for an access token:
```bash
POST /mcp/oauth/token
Content-Type: application/json

{
  "grant_type": "authorization_code",
  "code": "authorization_code",
  "redirect_uri": "https://chatgpt.com/oauth/callback",
  "client_id": "chatgpt-client-12345",
  "code_verifier": "pkce_code_verifier"
}
```

### Step 5: Using the Token

ChatGPT uses the access token in API requests:
```bash
GET /api/assets
Authorization: Bearer api_token_value
```

## Scopes

Available scopes:
- `read`: Read-only access to user data
- `write`: Modify user data
- `assets`: Access to assets
- `deals`: Access to deals
- `crm`: Access to CRM data

Scopes can be combined: `scope=read write assets`

## Security Features

1. **PKCE Support**: Prevents authorization code interception attacks
2. **Short-lived Codes**: Authorization codes expire in 10 minutes
3. **One-time Use**: Codes are marked as used after exchange
4. **State Parameter**: CSRF protection (handled by ChatGPT)
5. **HTTPS Required**: All OAuth endpoints require HTTPS

## Testing

### Test Authorization Endpoint

```bash
# Build authorization URL
AUTH_URL="https://yourdomain.com/mcp/oauth/authorize?response_type=code&client_id=test-client&redirect_uri=https://example.com/callback&scope=read"

# Open in browser (will redirect to login if not authenticated)
curl -L "$AUTH_URL"
```

### Test Token Exchange

```bash
# First get an authorization code from the authorize endpoint
# Then exchange it:
curl -X POST https://yourdomain.com/mcp/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "authorization_code",
    "code": "your_authorization_code",
    "redirect_uri": "https://example.com/callback",
    "client_id": "test-client"
  }'
```

### Test Metadata Endpoint

```bash
curl https://yourdomain.com/mcp/oauth/metadata
```

## Troubleshooting

### Issue: "Invalid authorization code"

**Solutions:**
1. Check that code hasn't expired (10 minute limit)
2. Verify code hasn't been used already
3. Ensure `client_id` and `redirect_uri` match the authorize request

### Issue: "Invalid code verifier"

**Solutions:**
1. Verify PKCE `code_verifier` matches the `code_challenge` from authorize
2. Check `code_challenge_method` is correct (`S256` or `plain`)

### Issue: User not redirected after login

**Solutions:**
1. Check that OAuth parameters are stored in session
2. Verify login redirect includes `next` parameter
3. Check session middleware is enabled

### Issue: Token not working in API requests

**Solutions:**
1. Verify token format: `Authorization: Bearer <token>`
2. Check token is valid: `APIToken.is_valid()`
3. Ensure user account is active
4. Check API endpoint requires authentication

## Integration with MCP Server

The MCP server automatically uses authenticated requests when:
1. User has completed OAuth flow
2. Access token is stored by ChatGPT
3. ChatGPT includes token in `Authorization` header

The MCP server's `_make_request` function will use the token from the `Authorization` header automatically.

## Next Steps

1. **Customize Scopes**: Add more granular scopes if needed
2. **Add Refresh Tokens**: Implement refresh token flow for long-lived sessions
3. **Audit Logging**: Log OAuth events for security monitoring
4. **Rate Limiting**: Add rate limiting to OAuth endpoints
5. **Client Registration**: Implement dynamic client registration if needed

## References

- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [PKCE RFC 7636](https://tools.ietf.org/html/rfc7636)
- [MCP Authorization Spec](https://developers.openai.com/apps-sdk/build/auth/)

