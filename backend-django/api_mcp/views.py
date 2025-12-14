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


def _get_mcp_tools_list():
    """
    Get tools list from FastMCP server in MCP protocol format.
    
    Returns a list of tools formatted according to MCP protocol specification.
    """
    try:
        # Use the tool manager to get tools directly
        if hasattr(mcp, '_tool_manager'):
            tool_manager = mcp._tool_manager
            tools = []
            
            # Get all registered tools from _tools dict
            if hasattr(tool_manager, '_tools'):
                for tool_name, tool_obj in tool_manager._tools.items():
                    try:
                        tool_info = {
                            "name": tool_name,
                            "description": getattr(tool_obj, 'description', ''),
                        }
                        
                        # Get input schema - FastMCP FunctionTool has parameters dict
                        # The parameters dict contains the Pydantic model for the tool
                        if hasattr(tool_obj, 'parameters') and isinstance(tool_obj.parameters, dict):
                            # Parameters is a dict, try to get schema from the model if available
                            # For now, create a basic schema - FastMCP will handle the actual schema
                            # when tools are called via ASGI transport
                            tool_info["inputSchema"] = {
                                "type": "object",
                                "properties": {},
                                "description": "Tool parameters. See tool description for details."
                            }
                        elif hasattr(tool_obj, 'inputSchema'):
                            tool_info["inputSchema"] = tool_obj.inputSchema
                        else:
                            # Fallback: create minimal schema
                            tool_info["inputSchema"] = {
                                "type": "object",
                                "properties": {}
                            }
                        
                        tools.append(tool_info)
                    except Exception as e:
                        logger.warning(f"Error processing tool {tool_name}: {e}")
                        continue
            
            if tools:
                logger.info(f"Successfully retrieved {len(tools)} tools from FastMCP tool manager")
                return tools
        
        # Fallback: log warning
        logger.warning("Could not access FastMCP tool manager. Tools may not be available via Django view.")
        return []
        
    except Exception as e:
        logger.exception(f"Error getting MCP tools list: {e}")
        return []


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
            # Get available tools from the MCP server using our helper function
            tools_info = _get_mcp_tools_list()
            
            # Build OAuth metadata URL (MCP-specific endpoints for ChatGPT integration)
            base_url = request.build_absolute_uri('/').rstrip('/')
            oauth_metadata_url = f"{base_url}/mcp/oauth/metadata"
            oauth_well_known_url = f"{base_url}/mcp/.well-known/oauth-authorization-server"
            
            # Icon URL - ChatGPT will look for this in the metadata
            # ChatGPT can retrieve icons from:
            # 1. icon_url or logo_url in the MCP server metadata (this response)
            # 2. A favicon at the domain root (e.g., https://api.nadlaner.com/favicon.ico)
            # 3. Manual upload during connector creation
            # 
            # Use your marketing site's favicon or serve one from your API
            # Minimum size: 128x128px, recommended: 512x512px
            icon_url = "https://www.nadlaner.com/favicon.svg"  # Use marketing site favicon
            # Alternative: Serve from your API if you have static file serving configured
            # icon_url = f"{base_url}/static/favicon.ico"
            
            return JsonResponse({
                "name": "RealEstateAPI",
                "version": "1.0.0",
                "protocol_version": "2024-11-05",
                "status": "running",
                "tools_count": len(tools_info),
                "endpoint": "/mcp",
                "endpoints": ["/mcp", "/mcp/"],
                "icon_url": icon_url,  # Icon URL for ChatGPT connector
                "logo_url": icon_url,  # Alternative field name some clients may use
                "oauth": {
                    "authorization_endpoint": f"{base_url}/mcp/oauth/authorize",
                    "token_endpoint": f"{base_url}/mcp/oauth/token",
                    "metadata_endpoint": oauth_metadata_url,
                    "well_known_endpoint": oauth_well_known_url,
                    "scopes_supported": ["read", "write", "assets", "deals", "crm"],
                    "response_types_supported": ["code"],
                    "code_challenge_methods_supported": ["plain", "S256"],
                    "grant_types_supported": ["authorization_code"],
                    "note": "OAuth endpoints are also available at /api/oauth/* for general use"
                },
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
                # List available tools from FastMCP server
                try:
                    tools = _get_mcp_tools_list()
                    logger.info(f"Returning {len(tools)} tools for tools/list request")
                    return JsonResponse({
                        "jsonrpc": jsonrpc_version,
                        "id": request_id,
                        "result": {
                            "tools": tools
                        }
                    })
                except Exception as e:
                    logger.exception(f"Error listing tools: {e}")
                    return JsonResponse({
                        "jsonrpc": jsonrpc_version,
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": "Internal error",
                            "data": f"Failed to list tools: {str(e)}"
                        }
                    }, status=500)
            
            elif method == "tools/call":
                # Call a tool - Note: Tool calls require ASGI server with FastMCP HTTP transport
                params = body.get("params", {})
                tool_name = params.get("name")
                
                if not tool_name:
                    return JsonResponse({
                        "jsonrpc": jsonrpc_version,
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": "Invalid params",
                            "data": "Tool name is required"
                        }
                    }, status=400)
                
                # Tool calls are not supported via Django WSGI view
                # They require ASGI server with FastMCP HTTP transport
                return JsonResponse({
                    "jsonrpc": jsonrpc_version,
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": "Method not supported",
                        "data": "Tool calls require ASGI server with FastMCP HTTP transport. Please use uvicorn or daphne to run the server. See CHATGPT_INTEGRATION.md for setup instructions."
                    }
                }, status=501)
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
