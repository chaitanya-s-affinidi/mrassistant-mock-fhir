"""HTTP wrapper for MCP Server.

This wraps the MCP server to expose it via HTTP POST endpoint,
allowing it to be deployed behind a public URL (e.g., ngrok).

MCP normally uses stdio (JSON-RPC over stdin/stdout), but for
network deployment we need HTTP transport.

Usage:
    uv run python -m mcp_server.http_server

Environment:
    MCP_HTTP_PORT: Port to listen on (default: 3000)
    FHIR_BASE_URL: FHIR server URL
    TIMEZONE: Timezone for slot display
"""

import asyncio
import json
import os
import sys
from typing import Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aiohttp import web
from mcp_server.fhir import get_fhir_client

# Import tool implementations
from mcp_server.tools.patients import register_patient_tools
from mcp_server.tools.practitioners import register_practitioner_tools
from mcp_server.tools.slots import register_slot_tools
from mcp_server.tools.appointments import register_appointment_tools
from mcp.server.fastmcp import FastMCP


# Create MCP instance and register tools
mcp = FastMCP("Hospital FHIR MCP Server")
register_patient_tools(mcp)
register_practitioner_tools(mcp)
register_slot_tools(mcp)
register_appointment_tools(mcp)


# Tool registry for direct invocation
TOOLS = {}
for tool in mcp._tool_manager._tools.values():
    TOOLS[tool.name] = tool.fn


def get_tool_schemas() -> list[dict]:
    """Get JSON schemas for all registered tools."""
    schemas = []
    for tool in mcp._tool_manager._tools.values():
        schema = {
            "name": tool.name,
            "description": tool.fn.__doc__ or "",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        # Extract parameters from function signature
        import inspect
        sig = inspect.signature(tool.fn)
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            prop = {"type": "string"}  # Default to string
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    prop["type"] = "integer"
                elif param.annotation == bool:
                    prop["type"] = "boolean"
                elif param.annotation == float:
                    prop["type"] = "number"
            schema["inputSchema"]["properties"][param_name] = prop
            if param.default == inspect.Parameter.empty:
                schema["inputSchema"]["required"].append(param_name)
        schemas.append(schema)
    return schemas


async def handle_mcp_request(request: web.Request) -> web.Response:
    """Handle MCP JSON-RPC requests over HTTP.
    
    Supports:
    - initialize
    - tools/list
    - tools/call
    """
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32700, "message": "Parse error"}
        }, status=400)
    
    jsonrpc = body.get("jsonrpc", "2.0")
    request_id = body.get("id")
    method = body.get("method", "")
    params = body.get("params", {})
    
    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "Hospital FHIR MCP Server",
                    "version": "0.1.0"
                }
            }
        
        elif method == "tools/list":
            result = {"tools": get_tool_schemas()}
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name not in TOOLS:
                return web.json_response({
                    "jsonrpc": jsonrpc,
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}"
                    }
                }, status=404)
            
            # Call the tool
            tool_result = TOOLS[tool_name](**arguments)
            
            # Format response
            if isinstance(tool_result, dict):
                text = json.dumps(tool_result)
            else:
                text = str(tool_result)
            
            result = {
                "content": [{"type": "text", "text": text}]
            }
        
        else:
            return web.json_response({
                "jsonrpc": jsonrpc,
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }, status=404)
        
        return web.json_response({
            "jsonrpc": jsonrpc,
            "id": request_id,
            "result": result
        })
    
    except Exception as e:
        return web.json_response({
            "jsonrpc": jsonrpc,
            "id": request_id,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }, status=500)


async def handle_health(request: web.Request) -> web.Response:
    """Health check endpoint."""
    # Check FHIR connectivity
    try:
        client = get_fhir_client()
        import httpx
        response = httpx.get(f"{client.base_url}/metadata", timeout=5.0)
        fhir_ok = response.status_code == 200
    except Exception:
        fhir_ok = False
    
    return web.json_response({
        "status": "ok" if fhir_ok else "degraded",
        "fhir_connected": fhir_ok,
        "tools_available": list(TOOLS.keys())
    })


def create_app() -> web.Application:
    """Create the aiohttp application."""
    app = web.Application()
    
    # CORS middleware for browser clients
    @web.middleware
    async def cors_middleware(request, handler):
        if request.method == "OPTIONS":
            response = web.Response()
        else:
            response = await handler(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    
    app.middlewares.append(cors_middleware)
    
    # Routes
    app.router.add_post("/mcp", handle_mcp_request)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/", handle_health)  # Root returns health too
    
    return app


def main():
    """Run the HTTP server."""
    port = int(os.getenv("MCP_HTTP_PORT", "3000"))
    
    print("=" * 60)
    print("  Hospital FHIR MCP Server (HTTP Mode)")
    print("=" * 60)
    print(f"\nListening on: http://0.0.0.0:{port}")
    print(f"FHIR Server:  {os.getenv('FHIR_BASE_URL', 'http://localhost:8080/fhir')}")
    print(f"\nEndpoints:")
    print(f"  POST /mcp     - MCP JSON-RPC endpoint")
    print(f"  GET  /health  - Health check")
    print(f"\nTools available: {list(TOOLS.keys())}")
    print("=" * 60)
    
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=port, print=None)


if __name__ == "__main__":
    main()
