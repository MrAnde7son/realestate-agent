# -*- coding: utf-8 -*-
"""
Django views for exposing the MCP server via HTTP.

This module provides Django views to expose the FastMCP server at the /mcp endpoint.
For full MCP protocol support, FastMCP's HTTP transport should be used via ASGI mounting.
"""
import json
import logging

from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .server import mcp

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET", "POST", "OPTIONS"])
def mcp_endpoint(request: HttpRequest) -> HttpResponse:
    """
    Django view to expose the MCP server at /mcp endpoint.
    
    Handles MCP protocol requests and provides basic server information.
    For full MCP protocol support with tool calls, use FastMCP's HTTP transport
    via ASGI mounting (see broker_backend/asgi.py for ASGI integration).
    
    GET: Returns MCP server information and health status
    POST: Handles MCP protocol JSON-RPC messages (basic support)
    OPTIONS: Handles CORS preflight requests
    """
    
    # Handle CORS preflight
    if request.method == "OPTIONS":
        response = HttpResponse()
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response["Access-Control-Max-Age"] = "86400"
        return response
    
    # Handle GET requests (health check, server info)
    if request.method == "GET":
        try:
            # Get available tools from the MCP server
            tools_info = []
            if hasattr(mcp, 'list_tools'):
                try:
                    tools = mcp.list_tools()
                    tools_info = [
                        {
                            "name": tool.name if hasattr(tool, 'name') else str(tool),
                            "description": getattr(tool, 'description', '')
                        }
                        for tool in tools
                    ]
                except Exception as e:
                    logger.warning(f"Could not list MCP tools: {e}")
            
            return JsonResponse({
                "name": "RealEstateAPI",
                "version": "1.0.0",
                "protocol_version": "2024-11-05",
                "status": "running",
                "tools_count": len(tools_info),
                "endpoint": "/mcp",
                "endpoints": ["/mcp", "/mcp/"],
                "note": "For full MCP protocol support with tool calls, use FastMCP's HTTP transport via ASGI"
            })
        except Exception as e:
            logger.exception("Error in GET handler")
            return JsonResponse(
                {"error": str(e), "status": "error"},
                status=500
            )
    
    # Handle POST requests (MCP protocol JSON-RPC messages)
    if request.method == "POST":
        try:
            # Parse JSON request body
            try:
                body = json.loads(request.body)
            except json.JSONDecodeError as e:
                return JsonResponse(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error",
                            "data": str(e)
                        }
                    },
                    status=400
                )
            
            # Handle JSON-RPC 2.0 protocol
            jsonrpc_version = body.get("jsonrpc", "2.0")
            request_id = body.get("id")
            method = body.get("method")
            
            # Basic method handling
            if method == "initialize":
                # MCP initialize request
                return JsonResponse({
                    "jsonrpc": jsonrpc_version,
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "RealEstateAPI",
                            "version": "1.0.0"
                        }
                    }
                })
            elif method == "tools/list":
                # List available tools
                return JsonResponse({
                    "jsonrpc": jsonrpc_version,
                    "id": request_id,
                    "result": {
                        "tools": []
                    }
                })
            else:
                # Unknown method
                return JsonResponse({
                    "jsonrpc": jsonrpc_version,
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}",
                        "data": "For full MCP protocol support, use FastMCP's HTTP transport"
                    }
                }, status=404)
            
        except Exception as e:
            logger.exception("Error handling MCP POST request")
            return JsonResponse(
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": "Internal error",
                        "data": str(e)
                    }
                },
                status=500
            )
    
    return JsonResponse(
        {"error": "Method not allowed"},
        status=405
    )

