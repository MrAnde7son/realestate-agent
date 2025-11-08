# ChatGPT Integration Guide

This guide explains how to connect the MCP server to ChatGPT.

## Current Status

The MCP server is exposed at `/mcp/` endpoint in your Django backend. There are two ways it can be accessed:

1. **Django View** (`/mcp/` via WSGI) - Basic protocol support, health checks
2. **FastMCP HTTP Transport** (via ASGI) - Full MCP protocol support with tool calls

## Prerequisites

1. **HTTPS Access**: ChatGPT requires HTTPS. For local development, use:
   - [ngrok](https://ngrok.com/) - `ngrok http 8000`
   - [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
   - Or deploy to a server with HTTPS

2. **ASGI Server**: For full MCP protocol support, ensure you're running Django with an ASGI server:
   ```bash
   # Using Uvicorn
   uvicorn broker_backend.asgi:application --host 0.0.0.0 --port 8000
   
   # Or using Daphne
   daphne -b 0.0.0.0 -p 8000 broker_backend.asgi:application
   ```

## Connecting to ChatGPT

### Step 1: Enable Developer Mode in ChatGPT

1. Open ChatGPT
2. Navigate to **Settings**
3. Go to **Apps & Connectors**
4. Scroll to **Advanced settings**
5. Enable **Developer mode**

### Step 2: Add Your MCP Server as a Connector

1. In **Apps & Connectors**, click **Create**
2. Fill in the details:
   - **Connector Name**: Real Estate API (or your preferred name)
   - **Description**: Real estate API tools for assets, deals, CRM, and calculations
   - **Connector URL**: `https://yourdomain.com/mcp` or `https://yourdomain.com/mcp/` (both work, must be HTTPS)
3. Click **Create**

### Step 3: Authenticate (if required)

If your MCP server requires authentication:
- You'll be prompted to log in
- Authorize ChatGPT to access your server
- Follow the on-screen instructions

### Step 4: Verify Connection

Once connected, ChatGPT should be able to:
- List available tools
- Call tools like `list_assets`, `get_asset`, `analyze_mortgage`, etc.
- Use the tools in conversations

## Testing the Connection

### Test Health Check

```bash
# Both work (with or without trailing slash)
curl https://yourdomain.com/mcp
curl https://yourdomain.com/mcp/
```

Should return:
```json
{
  "name": "RealEstateAPI",
  "version": "1.0.0",
  "protocol_version": "2024-11-05",
  "status": "running",
  "endpoint": "/mcp",
  "endpoints": ["/mcp", "/mcp/"]
}
```

### Test MCP Initialize

```bash
curl -X POST https://yourdomain.com/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    }
  }'
```

### Test Tools List

```bash
curl -X POST https://yourdomain.com/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'
```

## Troubleshooting

### Issue: ChatGPT can't connect

**Solutions:**
1. Ensure the server is accessible via HTTPS (not HTTP)
2. Check that CORS headers are properly set
3. Verify the URL is `/mcp` or `/mcp/` (both work)
4. Check server logs for errors

### Issue: Tools not showing up

**Solutions:**
1. Ensure you're using ASGI server (not WSGI) for full protocol support
2. Check that FastMCP's `http_app()` method is available
3. Verify tools are registered in `api_mcp/server.py`
4. Check server logs for import errors

### Issue: Tool calls failing

**Solutions:**
1. Verify API authentication token is set: `REALESTATE_API_TOKEN`
2. Check API base URL: `REALESTATE_API_URL`
3. Review server logs for detailed error messages
4. Ensure the backend API is accessible from the MCP server

## Architecture

```
ChatGPT
  ↓ HTTPS
Your Backend (/mcp or /mcp/)
  ↓ ASGI Routing
FastMCP HTTP Transport
  ↓ Tool Calls
Django API (/api/*)
  ↓
Your Services
```

## Environment Variables

Ensure these are set:

```bash
REALESTATE_API_URL=http://127.0.0.1:8000/api  # Backend API URL
REALESTATE_API_TOKEN=your-jwt-token           # Optional, for authenticated requests
ENABLE_EXTERNAL_MCP_TOOLS=false                # Set to true to enable external tools
```

## Next Steps

1. **Deploy with HTTPS**: Use a service like Render, Railway, or AWS
2. **Set up Authentication**: If needed, implement OAuth or API key authentication
3. **Monitor Usage**: Track tool calls and API usage
4. **Optimize**: Adjust tool registration based on usage patterns

## References

- [OpenAI MCP Documentation](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://fastmcp.wiki/)
- [ChatGPT Connector Guide](https://developers.openai.com/apps-sdk/deploy/connect-chatgpt)

