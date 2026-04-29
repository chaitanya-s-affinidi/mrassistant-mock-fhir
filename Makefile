# Mr Assistant Mock FHIR - Root Makefile
# =======================================
# Orchestrates mcp-server and mcp-client-sample

.PHONY: help setup dev-up dev-down server-http client-demo client-init inspect clean

# Default target
help:
	@echo "Mr Assistant Mock FHIR"
	@echo ""
	@echo "Setup:"
	@echo "  make setup        Install dependencies for both projects"
	@echo ""
	@echo "Development:"
	@echo "  make dev-up       Start HAPI FHIR + load mock data"
	@echo "  make dev-down     Stop all services"
	@echo ""
	@echo "Server:"
	@echo "  make server-http  Run MCP server with HTTP transport (port 3000)"
	@echo "  make server-stdio Run MCP server in stdio mode"
	@echo "  make ngrok-up     Start ngrok tunnel"
	@echo "  make inspect      Launch MCP Inspector (browser UI)"
	@echo ""
	@echo "Client:"
	@echo "  make client-init  Test client connection + list tools"
	@echo "  make client-demo  Run full demo workflow"
	@echo ""
	@echo "Testing Tools (via client):"
	@echo "  make search-patient NAME=\"John Smith\" DOB=\"1985-03-15\""
	@echo "  make create-patient NAME=\"Jane Doe\" DOB=\"1990-01-01\" PHONE=\"+1234567890\""
	@echo "  make list-practitioners SPECIALTY=\"cardiology\""
	@echo "  make get-slots PRACTITIONER_ID=\"...\" DATE=\"2026-05-01\""
	@echo "  make book PATIENT_ID=\"...\" SLOT_ID=\"...\" REASON=\"checkup\""
	@echo "  make reschedule APPOINTMENT_ID=\"...\" NEW_SLOT_ID=\"...\""
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        Stop services, remove venvs"

# ===================
# Setup
# ===================

setup:
	cd mcp-server && uv sync
	cd mcp-client-sample && uv sync
	@echo ""
	@echo "✓ Both projects ready!"

# ===================
# Development
# ===================

dev-up:
	cd mcp-server && $(MAKE) dev-up

dev-down:
	cd mcp-server && $(MAKE) dev-down

# ===================
# Server Commands
# ===================

server-http:
	cd mcp-server && $(MAKE) http-server

server-stdio:
	cd mcp-server && $(MAKE) run

ngrok-up:
	cd mcp-server && $(MAKE) ngrok-up

inspect:
	cd mcp-server && $(MAKE) inspect

# ===================
# Client Commands
# ===================

# Default URL for local testing
MCP_SERVER_URL ?= http://localhost:3000/mcp

client-init:
	cd mcp-client-sample && MCP_SERVER_URL=$(MCP_SERVER_URL) $(MAKE) init

client-demo:
	cd mcp-client-sample && MCP_SERVER_URL=$(MCP_SERVER_URL) $(MAKE) demo

# ===================
# Tool Testing (via client CLI)
# ===================

search-patient:
	cd mcp-client-sample && MCP_SERVER_URL=$(MCP_SERVER_URL) $(MAKE) search-patient NAME="$(NAME)" DOB="$(DOB)"

create-patient:
	cd mcp-client-sample && MCP_SERVER_URL=$(MCP_SERVER_URL) $(MAKE) create-patient NAME="$(NAME)" DOB="$(DOB)" PHONE="$(PHONE)"

list-practitioners:
	cd mcp-client-sample && MCP_SERVER_URL=$(MCP_SERVER_URL) $(MAKE) list-practitioners SPECIALTY="$(SPECIALTY)"

get-slots:
	cd mcp-client-sample && MCP_SERVER_URL=$(MCP_SERVER_URL) $(MAKE) get-slots PRACTITIONER_ID="$(PRACTITIONER_ID)" DATE="$(DATE)"

book:
	cd mcp-client-sample && MCP_SERVER_URL=$(MCP_SERVER_URL) $(MAKE) book PATIENT_ID="$(PATIENT_ID)" SLOT_ID="$(SLOT_ID)" REASON="$(REASON)"

reschedule:
	cd mcp-client-sample && MCP_SERVER_URL=$(MCP_SERVER_URL) $(MAKE) reschedule APPOINTMENT_ID="$(APPOINTMENT_ID)" NEW_SLOT_ID="$(NEW_SLOT_ID)"

# ===================
# Cleanup
# ===================

clean:
	cd mcp-server && $(MAKE) clean
	cd mcp-client-sample && rm -rf .venv
	@echo "✓ All cleaned up"
