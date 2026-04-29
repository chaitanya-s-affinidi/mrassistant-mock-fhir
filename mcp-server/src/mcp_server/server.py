"""MCP Server entry point using FastMCP."""

import os
from mcp.server.fastmcp import FastMCP

from mcp_server.tools.patients import register_patient_tools
from mcp_server.tools.practitioners import register_practitioner_tools
from mcp_server.tools.slots import register_slot_tools
from mcp_server.tools.appointments import register_appointment_tools

# Initialize FastMCP server
mcp = FastMCP("Hospital FHIR MCP Server")

# Register all tools
register_patient_tools(mcp)
register_practitioner_tools(mcp)
register_slot_tools(mcp)
register_appointment_tools(mcp)


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
