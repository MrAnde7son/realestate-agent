import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'broker_backend.settings')

# Get Django ASGI application
django_asgi_app = get_asgi_application()

# Try to mount FastMCP HTTP transport if available
try:
    from api_mcp.server import mcp
    
    # Check if FastMCP supports http_app method
    if hasattr(mcp, 'http_app'):
        # Mount FastMCP HTTP app at /mcp (without trailing slash for consistency)
        mcp_app = mcp.http_app(path="/mcp")
        
        # Create ASGI application that routes /mcp* to FastMCP and everything else to Django
        async def application(scope, receive, send):
            if scope["type"] == "http":
                path = scope.get("path", "")
                # Route MCP requests to FastMCP app (support both /mcp and /mcp/)
                if path.startswith("/mcp"):
                    await mcp_app(scope, receive, send)
                else:
                    # Route everything else to Django
                    await django_asgi_app(scope, receive, send)
            else:
                # For non-HTTP requests (websockets, etc.), use Django
                await django_asgi_app(scope, receive, send)
    else:
        # FastMCP doesn't have http_app, use Django only
        application = django_asgi_app
except (ImportError, AttributeError) as e:
    # If MCP server is not available or doesn't support http_app, use Django only
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"MCP HTTP transport not available: {e}. Using Django ASGI only.")
    application = django_asgi_app
