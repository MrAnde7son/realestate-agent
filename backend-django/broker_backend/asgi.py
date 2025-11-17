import os

from django.core.asgi import get_asgi_application
from starlette.applications import Starlette
from starlette.routing import Route, Mount

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
        
        # Create a routing function that delegates to Django for non-MCP paths
        async def django_route(scope, receive, send):
            """Route non-MCP requests to Django."""
            await django_asgi_app(scope, receive, send)
        
        # Create Starlette application with proper lifespan handling
        # This ensures FastMCP's task group is properly initialized
        # The lifespan context manager will be called by uvicorn/ASGI server on startup
        # Each worker process will call the lifespan on startup
        application_kwargs = {
            "routes": [
                # Mount MCP app at /mcp path
                Mount("/mcp", app=mcp_app),
                # Route root path to Django
                Route("/", endpoint=django_route),
                # Route everything else to Django (catch-all route)
                Route("/{rest_of_path:path}", endpoint=django_route),
            ],
        }
        
        # Only add lifespan if it exists (Starlette requires it for proper initialization)
        if mcp_lifespan:
            application_kwargs["lifespan"] = mcp_lifespan
        
        application = Starlette(**application_kwargs)
    else:
        # FastMCP doesn't have http_app, use Django only
        application = django_asgi_app
except (ImportError, AttributeError) as e:
    # If MCP server is not available or doesn't support http_app, use Django only
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"MCP HTTP transport not available: {e}. Using Django ASGI only.")
    application = django_asgi_app
