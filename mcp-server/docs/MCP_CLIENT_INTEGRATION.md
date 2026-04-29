# MCP Client Integration Guide for Mr Assistant

This document explains how to integrate the Hospital FHIR MCP Server with Mr Assistant's voice agent.

## Transport Options

### Option 1: HTTP Transport (Recommended for Public Deployment)

For deployment behind ATG or any public endpoint, use the HTTP server mode:

```bash
# Start MCP server with HTTP transport
make http-server

# Server runs at http://localhost:3000
# Endpoints:
#   POST /mcp     - MCP JSON-RPC endpoint
#   GET  /health  - Health check
```

### Option 2: Stdio Transport (Local Development)

For local development, use stdio (JSON-RPC over stdin/stdout):

```bash
make run
```

---

## Public Deployment with ngrok

### Step 1: Setup ngrok

```bash
# Install ngrok
brew install ngrok

# Copy the example config
cp .env.ngrok.example .env.ngrok

# Edit .env.ngrok and add your auth token from:
# https://dashboard.ngrok.com/get-started/your-authtoken
```

**.env.ngrok:**
```
NGROK_AUTHTOKEN=your_actual_token_here
```

The script auto-detects your static domain from the ngrok API. If you don't have one, claim a free static domain at https://dashboard.ngrok.com/cloud-edge/domains.

### Step 2: Start the Stack

**Terminal 1 - FHIR Server:**
```bash
make dev-up
```

**Terminal 2 - MCP HTTP Server:**
```bash
make http-server
```

**Terminal 3 - ngrok Tunnel:**
```bash
make ngrok-up
# Auto-detects your static domain from ngrok API
```

### Step 3: Test the Public Endpoint

```bash
# Set your ngrok URL
export MCP_SERVER_URL=https://hospital-mcp.ngrok-free.app/mcp

# Test
make test-http
```

---

## Architecture (HTTP Mode)

```
┌─────────────────────────────────────────────────────────────┐
│ Mr Assistant Voice Agent                                    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ MCP HTTP Client                                      │   │
│  │                                                      │   │
│  │  POST https://hospital-mcp.ngrok-free.app/mcp       │   │
│  │       │                                              │   │
│  │       ▼                                              │   │
│  │   JSON-RPC Request/Response over HTTPS               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                         (via ATG)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Hospital Infrastructure                                      │
│                                                             │
│  ngrok tunnel (hospital-mcp.ngrok-free.app)                 │
│       │                                                     │
│       ▼                                                     │
│  MCP HTTP Server (this repo - port 3000)                    │
│       │                                                     │
│       ▼                                                     │
│  HAPI FHIR Server (port 8080)                               │
└─────────────────────────────────────────────────────────────┘
```

---

## HTTP API (for Mr Assistant / ATG)

All requests use **POST** to the `/mcp` endpoint with JSON-RPC 2.0 format.

### curl Examples

**Initialize Session:**
```bash
curl -X POST https://hospital-mcp.ngrok-free.app/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "mr-assistant", "version": "1.0.0"}
    }
  }'
```

**List Tools:**
```bash
curl -X POST https://hospital-mcp.ngrok-free.app/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}'
```

**Call a Tool (search_patients):**
```bash
curl -X POST https://hospital-mcp.ngrok-free.app/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "search_patients",
      "arguments": {
        "name": "Camila Lopez",
        "birth_date": "1985-03-15"
      }
    }
  }'
```

**Health Check:**
```bash
curl https://hospital-mcp.ngrok-free.app/health
```

---

## JSON-RPC Protocol

### Initialize Session

**Request** (stdin):
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "mr-assistant",
      "version": "1.0.0"
    }
  }
}
```

**Response** (stdout):
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {}
    },
    "serverInfo": {
      "name": "Hospital FHIR MCP Server",
      "version": "0.1.0"
    }
  }
}
```

### List Available Tools

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "search_patients",
        "description": "Search for a patient by name and date of birth",
        "inputSchema": {
          "type": "object",
          "properties": {
            "name": {"type": "string"},
            "birth_date": {"type": "string"}
          },
          "required": ["name", "birth_date"]
        }
      }
    ]
  }
}
```

### Call a Tool

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "search_patients",
    "arguments": {
      "name": "Camila Lopez",
      "birth_date": "1985-03-15"
    }
  }
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"found\": true, \"patient_id\": \"patient-001\", \"name\": \"Camila Lopez\"}"
      }
    ]
  }
}
```

---

## Python MCP HTTP Client Example

See [scripts/sample_mcp_http_client.py](../scripts/sample_mcp_http_client.py) for a complete implementation.

```python
import httpx
import json

class MCPHttpClient:
    """HTTP client for MCP server."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self._request_id = 0
        self._client = httpx.Client(timeout=30.0)
    
    def call_tool(self, name: str, arguments: dict) -> dict:
        """Call an MCP tool."""
        self._request_id += 1
        
        response = self._client.post(
            self.base_url,
            json={
                "jsonrpc": "2.0",
                "id": self._request_id,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments}
            }
        )
        
        result = response.json()
        if "error" in result:
            raise Exception(result["error"]["message"])
        
        content = result["result"]["content"][0]["text"]
        return json.loads(content)


# Usage
client = MCPHttpClient("https://hospital-mcp.ngrok-free.app/mcp")

# Search patient
patient = client.call_tool("search_patients", {
    "name": "Camila Lopez",
    "birth_date": "1985-03-15"
})

# Get slots
slots = client.call_tool("get_available_slots", {
    "practitioner_id": "practitioner-001",
    "date_timestamp": 1746374400
})

# Book appointment
appointment = client.call_tool("create_appointment", {
    "patient_id": patient["patient_id"],
    "slot_id": slots["slots"][0]["slot_id"],
    "reason": "Annual checkup"
})
```

---

## Voice Agent Workflow Integration

### Workflow Variables

Store these in Mr Assistant workflow variables:

| Variable | Populated By | Used By |
|----------|--------------|---------|
| `{{patient_name}}` | User input | search_patients |
| `{{birth_date}}` | User input | search_patients |
| `{{patient_id}}` | search_patients result | create_appointment |
| `{{reason}}` | User input | Specialty mapping |
| `{{specialty}}` | Prompt engineering | list_practitioners_by_specialty |
| `{{practitioner_id}}` | list_practitioners result | get_available_slots |
| `{{practitioner_name}}` | list_practitioners result | Confirmation message |
| `{{preferred_date}}` | User input (as timestamp) | get_available_slots |
| `{{slot_id}}` | get_available_slots result | create_appointment |

### Workflow Node Actions

**Node 1: Identity Verification**
```
Action: Call search_patients(name={{patient_name}}, birth_date={{birth_date}})
If found=true: Store {{patient_id}}, proceed to Node 2
If found=false: Go to New Patient Registration node
```

**Node 1b: New Patient Registration**
```
Action: Call create_patient(name={{patient_name}}, birth_date={{birth_date}}, phone={{phone}})
Store {{patient_id}}, proceed to Node 2
```

**Node 2: Get Practitioner**
```
Action: Call list_practitioners_by_specialty(specialty={{specialty}})
Store {{practitioner_id}}, {{practitioner_name}}
Proceed to Node 3
```

**Node 3: Get Slots**
```
Action: Call get_available_slots(practitioner_id={{practitioner_id}}, date_timestamp={{preferred_date}})
Present slots to user
Store selected {{slot_id}}
```

**Node 4: Book Appointment**
```
Action: Call create_appointment(patient_id={{patient_id}}, slot_id={{slot_id}}, reason={{reason}})
If success=true: Confirm to user
If error=slot_unavailable: Re-fetch slots, retry
```

---

## Testing

### 1. Direct Tool Test (no MCP protocol)
```bash
make test-tools
```

### 2. MCP Stdio Client Test (local)
```bash
make test-mcp
```

### 3. MCP HTTP Client Test (public endpoint)
```bash
# Start HTTP server first
make http-server  # Terminal 1

# Then test
export MCP_SERVER_URL=http://localhost:3000/mcp
make test-http    # Terminal 2
```

### 4. FHIR Endpoint Test (curl)
```bash
make test-curl
```

### 5. Interactive MCP Inspector
```bash
make inspect
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FHIR_BASE_URL` | `http://localhost:8080/fhir` | HAPI FHIR server URL |
| `TIMEZONE` | `Asia/Singapore` | Timezone for slot display |

---

## Deployment Architecture

For production deployment (Hospital IT):

```
Mr Assistant MCP HTTP Client 
         │
         ▼
    ATG (Mr Assistant side)
         │
    ═══ encrypted ═══
         │
    ATG (Hospital side)
         │
         ▼
    ngrok / Load Balancer
         │
         ▼
    MCP HTTP Server (port 3000)
         │
         ▼
    HAPI FHIR (internal, port 8080)
```

### Production Checklist

1. **Replace ngrok with proper infrastructure** — Load balancer, API Gateway, or direct public IP
2. **Add authentication** — API keys or OAuth tokens in request headers
3. **TLS termination** — Ensure HTTPS at the edge
4. **Rate limiting** — Prevent abuse
5. **Audit logging** — Log all tool calls with timestamps and caller info

