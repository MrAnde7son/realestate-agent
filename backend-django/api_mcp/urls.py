# -*- coding: utf-8 -*-
"""
URL patterns for the MCP server endpoint.

MCP-specific endpoints that delegate to core OAuth functionality.
This allows MCP to expose OAuth endpoints under /mcp/oauth/* for ChatGPT integration
while reusing the general-purpose OAuth implementation in core.
"""

from django.urls import path
from . import views
from core import oauth_views

urlpatterns = [
    path("", views.mcp_endpoint, name="mcp_endpoint"),
    # OAuth 2.0 endpoints - delegate to core OAuth views
    # These are exposed under /mcp/oauth/* for ChatGPT MCP integration
    path("oauth/authorize", oauth_views.oauth_authorize, name="mcp_oauth_authorize"),
    path("oauth/token", oauth_views.oauth_token, name="mcp_oauth_token"),
    path(
        "oauth/register", oauth_views.oauth_register, name="mcp_oauth_register"
    ),  # RFC 7591 Dynamic Client Registration
    path("oauth/metadata", oauth_views.oauth_metadata, name="mcp_oauth_metadata"),
    # Well-known OAuth discovery endpoints for ChatGPT auto-discovery
    # ChatGPT may check either of these endpoints for OAuth configuration
    path(
        ".well-known/oauth-authorization-server",
        oauth_views.oauth_metadata,
        name="mcp_oauth_well_known",
    ),
    path(
        ".well-known/openid-configuration",
        oauth_views.oauth_metadata,
        name="mcp_oauth_openid_config",
    ),
]
