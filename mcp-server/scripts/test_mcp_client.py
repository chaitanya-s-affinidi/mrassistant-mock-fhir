#!/usr/bin/env python3
"""Example MCP client for Mr Assistant integration.

This demonstrates how to connect to the MCP server via stdio transport
and call tools programmatically.

Usage:
    uv run python scripts/test_mcp_client.py
"""

import asyncio
import json
import sys
import os


async def test_mcp_client():
    """Test MCP server via stdio client."""
    try:
        from mcp import ClientSession
        from mcp.client.stdio import stdio_client, StdioServerParameters
    except ImportError:
        print("✗ MCP client not installed")
        print("  Run: uv add mcp")
        sys.exit(1)
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    print("=" * 60)
    print("  MCP Client Test")
    print("=" * 60)
    print(f"\nConnecting to MCP server...")
    print(f"  Command: uv run mcp-server")
    print(f"  Cwd: {project_root}")
    
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "mcp-server"],
        cwd=project_root,
        env={
            **os.environ,
            "FHIR_BASE_URL": "http://localhost:8080/fhir",
            "TIMEZONE": "Asia/Singapore"
        }
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize session
                print("\nInitializing MCP session...")
                await session.initialize()
                print("✓ Session initialized")
                
                # List available tools
                print("\n" + "-" * 40)
                print("Available Tools:")
                print("-" * 40)
                tools_result = await session.list_tools()
                for tool in tools_result.tools:
                    print(f"  - {tool.name}: {tool.description[:50]}...")
                
                # Test 1: Search for patient
                print("\n" + "=" * 60)
                print("TEST 1: search_patients")
                print("=" * 60)
                result = await session.call_tool(
                    "search_patients",
                    arguments={
                        "name": "Camila Lopez",
                        "birth_date": "1985-03-15"
                    }
                )
                print(json.dumps(parse_result(result), indent=2))
                
                # Test 2: List practitioners
                print("\n" + "=" * 60)
                print("TEST 2: list_practitioners_by_specialty")
                print("=" * 60)
                result = await session.call_tool(
                    "list_practitioners_by_specialty",
                    arguments={
                        "specialty": "general-medicine"
                    }
                )
                print(json.dumps(parse_result(result), indent=2))
                
                # Test 3: Get available slots
                print("\n" + "=" * 60)
                print("TEST 3: get_available_slots")
                print("=" * 60)
                result = await session.call_tool(
                    "get_available_slots",
                    arguments={
                        "practitioner_id": "practitioner-001",
                        "date_timestamp": 1746374400  # May 5, 2026
                    }
                )
                print(json.dumps(parse_result(result), indent=2))
                
                # Test 4: Create appointment
                print("\n" + "=" * 60)
                print("TEST 4: create_appointment")
                print("=" * 60)
                result = await session.call_tool(
                    "create_appointment",
                    arguments={
                        "patient_id": "patient-001",
                        "slot_id": "slot-001",
                        "reason": "Annual checkup"
                    }
                )
                print(json.dumps(parse_result(result), indent=2))
                
                print("\n" + "=" * 60)
                print("✓ All MCP client tests completed!")
                print("=" * 60)
                
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure:")
        print("  1. FHIR server is running: make fhir-up")
        print("  2. Mock data is loaded: make load-data")
        sys.exit(1)


def parse_result(result):
    """Parse MCP tool result to dict."""
    if hasattr(result, 'content') and result.content:
        content = result.content[0]
        if hasattr(content, 'text'):
            try:
                return json.loads(content.text)
            except json.JSONDecodeError:
                return {"text": content.text}
    return {"raw": str(result)}


if __name__ == "__main__":
    asyncio.run(test_mcp_client())
