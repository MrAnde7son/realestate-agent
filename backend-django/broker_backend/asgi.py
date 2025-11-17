import os

from django.core.asgi import get_asgi_application
from starlette.applications import Starlette
from starlette.routing import Mount

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
        import logging
        logger = logging.getLogger(__name__)
        
        mcp_lifespan = None
        # Try multiple ways to get the lifespan
        if hasattr(mcp_app, 'lifespan'):
            mcp_lifespan = mcp_app.lifespan
            logger.info("FastMCP lifespan found on mcp_app.lifespan")
        elif hasattr(mcp_app, 'router') and hasattr(mcp_app.router, 'lifespan_context'):
            # Some Starlette apps store lifespan in router
            mcp_lifespan = mcp_app.router.lifespan_context
            logger.info("FastMCP lifespan found on mcp_app.router.lifespan_context")
        elif hasattr(mcp_app, 'app') and hasattr(mcp_app.app, 'lifespan'):
            # Try nested app
            mcp_lifespan = mcp_app.app.lifespan
            logger.info("FastMCP lifespan found on mcp_app.app.lifespan")
        
        if mcp_lifespan:
            # Verify it's callable (should be an async context manager)
            if callable(mcp_lifespan):
                logger.info("FastMCP lifespan is callable, will initialize task group on startup")
            else:
                logger.warning("FastMCP lifespan found but is not callable. Type: %s", type(mcp_lifespan))
        else:
            logger.error("FastMCP lifespan not found. mcp_app type: %s, dir: %s", 
                        type(mcp_app), [attr for attr in dir(mcp_app) if not attr.startswith('_')])
        
        # Create a routing ASGI app for Django (non-MCP paths)
        async def django_router(scope, receive, send):
            """Route non-MCP requests to Django."""
            await django_asgi_app(scope, receive, send)
        
        # Wrapper to route OAuth endpoints under /mcp to Django
        # These need to be explicitly routed before FastMCP gets them
        # Starlette strips the /mcp/oauth prefix, so we need to restore it for Django
        async def mcp_oauth_router(scope, receive, send):
            """Route OAuth requests under /mcp to Django."""
            # When mounted at /mcp/oauth, Starlette strips that prefix
            # Restore the full path so Django can match it correctly
            original_path = scope.get("path", "")
            scope = dict(scope)  # Create a copy to avoid mutating the original
            scope["path"] = "/mcp/oauth" + original_path
            await django_asgi_app(scope, receive, send)
        
        # Wrapper to route well-known endpoints under /mcp to Django
        # Starlette strips the /mcp/.well-known prefix, so we need to restore it for Django
        async def mcp_wellknown_router(scope, receive, send):
            """Route well-known requests under /mcp to Django."""
            # When mounted at /mcp/.well-known, Starlette strips that prefix
            # Restore the full path so Django can match it correctly
            original_path = scope.get("path", "")
            scope = dict(scope)  # Create a copy to avoid mutating the original
            scope["path"] = "/mcp/.well-known" + original_path
            await django_asgi_app(scope, receive, send)
        
        # Create Starlette application with proper lifespan handling
        # Route OAuth and well-known endpoints explicitly before mounting FastMCP
        # This ensures they go to Django, not FastMCP
        app_kwargs = {
            "routes": [
                # Explicitly route OAuth endpoints under /mcp to Django (before FastMCP)
                Mount("/mcp/oauth", app=mcp_oauth_router),
                Mount("/mcp/.well-known", app=mcp_wellknown_router),
                # Mount FastMCP app at /mcp for MCP protocol requests
                # This will handle everything under /mcp that doesn't match above routes
                Mount("/mcp", app=mcp_app),
                # Mount Django at root for everything else
                Mount("/", app=django_router),
            ],
        }
        
        # Only add lifespan if we found it (critical for FastMCP task group initialization)
        if mcp_lifespan:
            app_kwargs["lifespan"] = mcp_lifespan
            logger.info("Passing lifespan to Starlette application")
        else:
            logger.error("WARNING: No lifespan to pass to Starlette - FastMCP may not work!")
        
        application = Starlette(**app_kwargs)
    else:
        # FastMCP doesn't have http_app, use Django only
        application = django_asgi_app
except (ImportError, AttributeError) as e:
    # If MCP server is not available or doesn't support http_app, use Django only
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"MCP HTTP transport not available: {e}. Using Django ASGI only.")
    application = django_asgi_app
