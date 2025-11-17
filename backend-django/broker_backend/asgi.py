import os

from django.core.asgi import get_asgi_application
from starlette.applications import Starlette

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
        
        # Get the lifespan from mcp_app
        # FastMCP's http_app returns a Starlette app with lifespan
        # The lifespan is a context manager function that initializes the task group
        mcp_lifespan = getattr(mcp_app, 'lifespan', None)
        
        # Log for debugging (helps identify issues in production)
        import logging
        logger = logging.getLogger(__name__)
        if mcp_lifespan:
            logger.info("FastMCP lifespan found, will initialize task group on startup")
        else:
            logger.warning("FastMCP lifespan not found on mcp_app. Task group may not initialize properly.")
        
        # Create a custom ASGI application that routes requests
        # This handles both MCP and Django routing while preserving lifespan
        async def routing_app(scope, receive, send):
            """Route requests to MCP or Django based on path."""
            if scope["type"] == "http":
                path = scope.get("path", "")
                # Route MCP requests to FastMCP app
                if path.startswith("/mcp"):
                    await mcp_app(scope, receive, send)
                else:
                    # Route everything else to Django
                    await django_asgi_app(scope, receive, send)
            else:
                # For non-HTTP requests (websockets, etc.), use Django
                await django_asgi_app(scope, receive, send)
        
        # Create Starlette application with proper lifespan handling
        # This ensures FastMCP's task group is properly initialized
        # The lifespan context manager will be called by uvicorn/ASGI server on startup
        # Each worker process will call the lifespan on startup
        # We wrap our routing app in Starlette to get lifespan support
        application_kwargs = {}
        
        # Only add lifespan if it exists (Starlette requires it for proper initialization)
        if mcp_lifespan:
            application_kwargs["lifespan"] = mcp_lifespan
        
        # Create a Starlette app that uses our routing function
        # We need to override the __call__ method to use our routing
        class RoutingStarletteApp(Starlette):
            def __init__(self, routing_func, **kwargs):
                super().__init__(routes=[], **kwargs)
                self._routing_func = routing_func
            
            async def __call__(self, scope, receive, send):
                await self._routing_func(scope, receive, send)
        
        application = RoutingStarletteApp(routing_app, **application_kwargs)
    else:
        # FastMCP doesn't have http_app, use Django only
        application = django_asgi_app
except (ImportError, AttributeError) as e:
    # If MCP server is not available or doesn't support http_app, use Django only
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"MCP HTTP transport not available: {e}. Using Django ASGI only.")
    application = django_asgi_app
