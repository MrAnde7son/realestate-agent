"""Views exposing the MCP server via the Django application."""

from __future__ import annotations

import logging
from typing import Optional

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views import View

from .asgi_proxy import ASGIApplicationProxy

logger = logging.getLogger(__name__)

_mcp_import_error: Optional[str] = None

try:
    from .server import mcp
except Exception as exc:  # pragma: no cover - defensive branch
    _mcp_import_error = str(exc)
    mcp = None  # type: ignore[assignment]
    logger.exception("Failed to import MCP server", exc_info=exc)


class MCPAPIView(View):
    """Expose the FastMCP HTTP endpoint at the Django ``/mcp`` route."""

    http_method_names = ["get", "post", "delete", "options", "head"]

    _proxy: Optional[ASGIApplicationProxy] = (
        ASGIApplicationProxy(lambda: mcp.http_app(path="/mcp"))  # type: ignore[union-attr]
        if mcp is not None
        else None
    )

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if self._proxy is None:
            message = {
                "success": False,
                "error": "MCP server is not available",
            }
            if _mcp_import_error:
                message["details"] = _mcp_import_error
            return JsonResponse(message, status=503)

        return self._proxy.handle(request)
