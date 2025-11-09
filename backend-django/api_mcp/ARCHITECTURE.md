# MCP Server Architecture

## Overview

The MCP (Model Context Protocol) server is exposed at `/mcp` and provides tools for ChatGPT and other LLM integrations. OAuth 2.0 authentication is implemented in the `core` app for reuse across the application, while MCP-specific endpoints delegate to core functionality.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ChatGPT / LLM Client                      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ HTTPS
                        │
        ┌───────────────▼────────────────┐
        │   /mcp/* (MCP Endpoints)      │
        │   - /mcp (main endpoint)      │
        │   - /mcp/oauth/* (OAuth)      │
        └───────────────┬────────────────┘
                        │
        ┌───────────────▼────────────────┐
        │      api_mcp app               │
        │   - MCP protocol handling     │
        │   - Tool registration          │
        │   - Delegates to core OAuth    │
        └───────────────┬────────────────┘
                        │
        ┌───────────────▼────────────────┐
        │      core app                  │
        │   - OAuth 2.0 implementation   │
        │   - OAuthAuthorizationCode     │
        │   - APIToken                   │
        │   - /api/oauth/* endpoints     │
        └───────────────┬────────────────┘
                        │
        ┌───────────────▼────────────────┐
        │   Django API (/api/*)         │
        │   - Assets, Deals, CRM, etc.  │
        └────────────────────────────────┘
```

## Components

### 1. MCP Server (`api_mcp` app)

**Purpose**: Expose MCP protocol endpoints for ChatGPT integration

**Endpoints**:
- `/mcp` - Main MCP endpoint (health check, server info)
- `/mcp/oauth/authorize` - OAuth authorization (delegates to core)
- `/mcp/oauth/token` - OAuth token exchange (delegates to core)
- `/mcp/oauth/metadata` - OAuth metadata (delegates to core)

**Files**:
- `server.py` - FastMCP server with tool definitions
- `views.py` - Django views for MCP endpoint
- `urls.py` - URL routing (delegates OAuth to core)

### 2. OAuth Implementation (`core` app)

**Purpose**: General-purpose OAuth 2.0 authentication for all integrations

**Endpoints**:
- `/api/oauth/authorize` - General OAuth authorization
- `/api/oauth/token` - General OAuth token exchange
- `/api/oauth/metadata` - General OAuth metadata

**Models**:
- `OAuthAuthorizationCode` - Temporary authorization codes
- `APIToken` - Access tokens for authenticated requests

**Files**:
- `models.py` - OAuth models
- `oauth_views.py` - OAuth endpoints
- `oauth.py` - OAuth utilities (PKCE helpers)
- `urls.py` - OAuth URL routing

## OAuth Flow

### For ChatGPT MCP Integration

1. **User connects MCP server in ChatGPT**
   - ChatGPT initiates OAuth flow
   - Redirects to `/mcp/oauth/authorize`

2. **Authorization**
   - User authenticates (if not logged in)
   - User approves access
   - Authorization code generated

3. **Token Exchange**
   - ChatGPT exchanges code at `/mcp/oauth/token`
   - Receives API token (Bearer token)

4. **Authenticated Requests**
   - ChatGPT includes token in `Authorization: Bearer <token>` header
   - MCP server uses token for API requests

### For Other Integrations

Same flow but using `/api/oauth/*` endpoints instead of `/mcp/oauth/*`.

## Benefits of This Architecture

1. **Reusability**: OAuth is in `core` app, usable by any integration
2. **Separation of Concerns**: MCP-specific logic stays in `api_mcp`
3. **Maintainability**: Single OAuth implementation to maintain
4. **Flexibility**: Can add more OAuth consumers without duplicating code

## Usage Examples

### ChatGPT Integration

```bash
# 1. Health check
curl https://yourdomain.com/mcp

# 2. OAuth authorization (user redirected here)
https://yourdomain.com/mcp/oauth/authorize?response_type=code&client_id=chatgpt&redirect_uri=...

# 3. Token exchange (ChatGPT does this)
curl -X POST https://yourdomain.com/mcp/oauth/token \
  -d 'grant_type=authorization_code&code=...'

# 4. Use token in API requests
curl https://yourdomain.com/api/assets \
  -H "Authorization: Bearer <token>"
```

### General API Client Integration

```bash
# Use general OAuth endpoints
https://yourdomain.com/api/oauth/authorize?...
https://yourdomain.com/api/oauth/token
```

## Configuration

### Environment Variables

```bash
REALESTATE_API_URL=http://127.0.0.1:8000/api
REALESTATE_API_TOKEN=optional-token-for-server-to-server
ENABLE_EXTERNAL_MCP_TOOLS=false  # Set to true for external tools
```

### Django Settings

```python
INSTALLED_APPS = [
    # ...
    'core',      # OAuth implementation
    'api_mcp',   # MCP endpoints
]
```

## Migration

Run migrations to create OAuth tables:

```bash
python manage.py migrate core
```

This creates:
- `OAuthAuthorizationCode` table (temporary auth codes)
- Uses existing `APIToken` table (access tokens)

## Security

- **PKCE Support**: Prevents authorization code interception
- **Short-lived Codes**: Authorization codes expire in 10 minutes
- **Single-use Codes**: Codes are marked as used after exchange
- **HTTPS Required**: OAuth endpoints require HTTPS
- **Token Validation**: API tokens validated on each request

## Future Enhancements

- Refresh token support for long-lived sessions
- Client registration endpoint
- Scope-based permissions
- Rate limiting per client
- Audit logging for OAuth events

