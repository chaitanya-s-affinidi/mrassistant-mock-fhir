#!/bin/bash
# Docker entrypoint script to wait for HAPI FHIR and load mock data

set -e

FHIR_BASE_URL="${FHIR_BASE_URL:-http://localhost:8080/fhir}"
MAX_RETRIES=${MAX_RETRIES:-60}
RETRY_INTERVAL=${RETRY_INTERVAL:-5}

echo "==================================================="
echo "Hospital FHIR MCP - Mock Data Loader"
echo "==================================================="
echo ""
echo "Waiting for HAPI FHIR server at ${FHIR_BASE_URL}..."

# Wait for FHIR server to be ready
retry_count=0
until curl -sf "${FHIR_BASE_URL}/metadata" > /dev/null 2>&1; do
    retry_count=$((retry_count + 1))
    if [ $retry_count -ge $MAX_RETRIES ]; then
        echo "✗ FHIR server failed to start after ${MAX_RETRIES} attempts"
        exit 1
    fi
    echo "  Waiting... (${retry_count}/${MAX_RETRIES})"
    sleep $RETRY_INTERVAL
done

echo "✓ FHIR server is ready"
echo ""

# Load mock data
BUNDLE_FILE="/data/mock_bundle.json"

if [ ! -f "$BUNDLE_FILE" ]; then
    echo "✗ Bundle file not found: $BUNDLE_FILE"
    exit 1
fi

echo "Loading mock data from ${BUNDLE_FILE}..."

RESPONSE=$(curl -sf -X POST "${FHIR_BASE_URL}" \
    -H "Content-Type: application/fhir+json" \
    -d @"$BUNDLE_FILE" \
    --max-time 60)

if [ $? -eq 0 ]; then
    ENTRY_COUNT=$(echo "$RESPONSE" | grep -o '"location"' | wc -l)
    echo "✓ Successfully loaded ${ENTRY_COUNT} resources"
    echo ""
    echo "==================================================="
    echo "Mock data loaded successfully!"
    echo ""
    echo "FHIR Server: ${FHIR_BASE_URL}"
    echo "==================================================="
else
    echo "✗ Failed to load mock data"
    exit 1
fi

# Keep container running if needed (for sidecar pattern)
if [ "$KEEP_RUNNING" = "true" ]; then
    echo ""
    echo "Container staying alive (KEEP_RUNNING=true)..."
    tail -f /dev/null
fi
