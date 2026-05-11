.PHONY: help install dev-up dev-down mcp-down fhir-up fhir-down fhir-logs load-data run http-server ngrok-up test test-tools test-mcp test-http test-curl inspect clean

# Default target
help:
	@echo "Hospital FHIR MCP Server"
	@echo ""
	@echo "Development:"
	@echo "  make dev-up      Start HAPI FHIR + MCP server, load mock data"
	@echo "  make dev-down    Stop all services (FHIR + MCP)"
	@echo "  make run         Run MCP server (stdio mode)"
	@echo ""
	@echo "HTTP Mode (for public deployment):"
	@echo "  make http-server Run MCP server with HTTP transport"
	@echo "  make ngrok-up    Start ngrok tunnel (auto-detects domain)"
	@echo ""
	@echo "Testing:"
	@echo "  make test-tools  Test MCP tools directly (no protocol)"
	@echo "  make test-mcp    Test via MCP client (stdio)"
	@echo "  make test-http   Test via MCP HTTP client"
	@echo "  make test-curl   Test FHIR endpoints with curl"
	@echo "  make inspect     Launch MCP Inspector (browser UI)"
	@echo ""
	@echo "Individual commands:"
	@echo "  make install     Install Python dependencies"
	@echo "  make fhir-up     Start HAPI FHIR server"
	@echo "  make fhir-down   Stop HAPI FHIR server"
	@echo "  make fhir-logs   Tail HAPI FHIR logs"
	@echo "  make load-data   Load mock FHIR data"
	@echo "  make test        Run all tests"
	@echo "  make clean       Remove virtual env and docker volumes"

# Install dependencies
install:
	uv sync

# Start everything for development
dev-up: fhir-up
	@echo "Waiting for HAPI FHIR to start..."
	@sleep 10
	@$(MAKE) wait-for-fhir
	@echo ""
	@echo "Starting MCP HTTP server on port 3000..."
	@nohup uv run python -m mcp_server.http_server > mcp-server.log 2>&1 & echo $$! > .mcp-server.pid
	@sleep 2
	@if curl -sf http://localhost:3000/health > /dev/null 2>&1; then \
		echo "✓ MCP server is running (PID: $$(cat .mcp-server.pid))"; \
	else \
		echo "⚠ MCP server may still be starting. Check: tail -f mcp-server.log"; \
	fi
	@echo ""
	@echo "✓ Development environment ready!"
	@echo ""
	@echo "FHIR Server: http://localhost:8080/fhir"
	@echo "MCP Server:  http://localhost:3000/mcp"
	@echo ""
	@echo "Logs: tail -f mcp-server.log"

# Stop everything
dev-down: mcp-down fhir-down
	@echo "✓ Development environment stopped"

# Stop MCP server
mcp-down:
	@if [ -f .mcp-server.pid ]; then \
		PID=$$(cat .mcp-server.pid); \
		if kill -0 $$PID 2>/dev/null; then \
			kill $$PID && echo "✓ MCP server stopped (PID: $$PID)"; \
		else \
			echo "MCP server not running"; \
		fi; \
		rm -f .mcp-server.pid; \
	else \
		@# Try to kill by port as fallback
		lsof -ti:3000 | xargs -r kill 2>/dev/null || true; \
	fi

# HAPI FHIR commands
fhir-up:
	docker-compose up -d
	@echo "HAPI FHIR starting at http://localhost:8080/fhir"

fhir-down:
	docker-compose down

fhir-logs:
	docker-compose logs -f

# Wait for FHIR server to be ready
wait-for-fhir:
	@echo "Checking FHIR server health..."
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		if curl -sf http://localhost:8080/fhir/metadata > /dev/null 2>&1; then \
			echo "✓ FHIR server is ready"; \
			exit 0; \
		fi; \
		echo "  Waiting... ($$i/10)"; \
		sleep 3; \
	done; \
	echo "✗ FHIR server failed to start"; \
	exit 1

# Load mock data
load-data:
	uv run python scripts/load_mock_data.py

# Run MCP server (stdio mode - for local testing)
run:
	uv run mcp-server

# Run MCP server with HTTP transport (for public deployment)
http-server:
	uv run python -m mcp_server.http_server

# Start ngrok tunnel (reads token from .env.ngrok, auto-detects domain)
ngrok-up:
	@if [ ! -f .env.ngrok ]; then \
		echo "✗ .env.ngrok not found!"; \
		echo ""; \
		echo "Create it from the example:"; \
		echo "  cp .env.ngrok.example .env.ngrok"; \
		echo ""; \
		echo "Then edit .env.ngrok and add your auth token from:"; \
		echo "  https://dashboard.ngrok.com/get-started/your-authtoken"; \
		exit 1; \
	fi
	@. ./.env.ngrok && \
	if [ -z "$$NGROK_AUTHTOKEN" ] || [ "$$NGROK_AUTHTOKEN" = "your_auth_token_here" ]; then \
		echo "✗ NGROK_AUTHTOKEN not set in .env.ngrok"; \
		exit 1; \
	fi && \
	export NGROK_AUTHTOKEN="$$NGROK_AUTHTOKEN" && \
	echo "Checking for existing ngrok domains..." && \
	DOMAIN=$$(ngrok api reserved-domains list 2>/dev/null | grep -o '"domain":"[^"]*"' | head -1 | cut -d'"' -f4) && \
	if [ -n "$$DOMAIN" ]; then \
		echo "Found domain: $$DOMAIN"; \
		echo "Starting ngrok tunnel on port 3000..."; \
		ngrok http --domain="$$DOMAIN" 3000; \
	else \
		echo "No static domain found. Using random URL."; \
		echo "To get a free static domain, visit: https://dashboard.ngrok.com/cloud-edge/domains"; \
		ngrok http 3000; \
	fi

# Run all tests
test: test-tools

# Test MCP tools directly (bypasses MCP protocol)
test-tools:
	uv run python scripts/test_tools.py

# Test via MCP client (full JSON-RPC protocol)
test-mcp:
	uv run python scripts/test_mcp_client.py

# Test via MCP HTTP client
test-http:
	uv run python scripts/sample_mcp_http_client.py

# Test FHIR endpoints with curl
test-curl:
	chmod +x scripts/test_fhir_curl.sh
	./scripts/test_fhir_curl.sh

# Launch MCP Inspector (browser UI)
inspect:
	npx @modelcontextprotocol/inspector uv run mcp-server

# Clean up
clean:
	docker-compose down -v
	rm -rf .venv
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned up"
