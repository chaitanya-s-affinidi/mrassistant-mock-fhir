#!/bin/bash
# Start ngrok tunnel for MCP HTTP server
# Usage: ./scripts/start_ngrok.sh
#
# Configuration: Create .env.ngrok from .env.ngrok.example
#   NGROK_AUTHTOKEN=your_token_here
#
# The script auto-detects your static domain from ngrok API.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env.ngrok"

PORT="${MCP_HTTP_PORT:-3000}"

echo "========================================"
echo "  ngrok Tunnel for MCP Server"
echo "========================================"

# Check for .env.ngrok
if [ ! -f "$ENV_FILE" ]; then
    echo ""
    echo "✗ .env.ngrok not found!"
    echo ""
    echo "Create it from the example:"
    echo "  cp .env.ngrok.example .env.ngrok"
    echo ""
    echo "Then add your auth token from:"
    echo "  https://dashboard.ngrok.com/get-started/your-authtoken"
    exit 1
fi

# Load config
source "$ENV_FILE"

if [ -z "$NGROK_AUTHTOKEN" ] || [ "$NGROK_AUTHTOKEN" = "your_auth_token_here" ]; then
    echo ""
    echo "✗ NGROK_AUTHTOKEN not set in .env.ngrok"
    exit 1
fi

export NGROK_AUTHTOKEN

echo ""
echo "Port: $PORT"
echo ""
echo "Checking for existing ngrok domains..."

# Try to get domain from ngrok API
DOMAIN=$(ngrok api reserved-domains list 2>/dev/null | grep -o '"domain":"[^"]*"' | head -1 | cut -d'"' -f4 || true)

if [ -n "$DOMAIN" ]; then
    echo "Found domain: $DOMAIN"
    echo ""
    echo "Starting ngrok with static domain..."
    ngrok http --domain="$DOMAIN" "$PORT"
else
    echo "No static domain found."
    echo ""
    echo "To get a free static domain:"
    echo "  1. Go to https://dashboard.ngrok.com/cloud-edge/domains"
    echo "  2. Create a free static domain"
    echo "  3. Run this script again"
    echo ""
    echo "Starting ngrok with random URL..."
    ngrok http "$PORT"
fi
