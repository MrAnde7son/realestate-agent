"""Model Context Protocol (MCP) server for Mavat.

This subpackage exposes a simple FastAPI application that wraps the
`MavatScraper` and exposes its functionality via HTTP.  The API
contract mirrors the tool semantics used in the ``yad2``, ``gov`` and
``rami`` MCP servers from the realestate‑agent project, albeit
implemented without the external ``fastmcp`` dependency for
simplicity.  Consumers can mount this app in a larger ASGI server or
run it stand‑alone for testing.
"""

from .server import create_app

__all__ = ["create_app"]