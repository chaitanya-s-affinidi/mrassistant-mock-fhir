# Mr Assistant Mock FHIR

Mock hospital EHR system with MCP server for Mr Assistant AI integration demo.

## Structure

```
mrassistant-mock-fhir/
├── mcp-server/          # MCP server + HAPI FHIR
└── mcp-client-sample/   # Sample Python client CLI
```

## Quick Start

```bash
# 1. Install dependencies
make setup

# 2. Start HAPI FHIR + load mock data
make dev-up

# 3. Run MCP server (HTTP mode)
make server-http

# 4. Test with client
make client-demo
```

## Testing Tools

```bash
# Via client CLI
make search-patient NAME="John Smith" DOB="1985-03-15"
make list-practitioners SPECIALTY="cardiology"
make client-init   # List all tools

# Via Inspector UI
make inspect
```

## Documentation

| Doc | Description |
|-----|-------------|
| [Implementation Plan](mcp-server/docs/IMPLEMENTATION_PLAN.md) | Architecture, decision log |
| [MCP Tool Contracts](mcp-server/docs/MCP_TOOL_CONTRACTS.md) | JSON schemas for all tools |
| [Client Integration](mcp-server/docs/MCP_CLIENT_INTEGRATION.md) | Mr Assistant integration |
