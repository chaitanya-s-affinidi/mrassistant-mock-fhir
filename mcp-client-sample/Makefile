# MCP Client Sample - Makefile
# ============================

.PHONY: setup sync init list-tools demo search-patient create-patient list-practitioners get-slots book reschedule help

# Default MCP server URL (can be overridden)
MCP_SERVER_URL ?= http://localhost:3000/mcp

# Setup
setup: sync  ## Install dependencies

sync:  ## Sync dependencies with uv
	uv sync

# Tool Commands (via CLI)
init:  ## Initialize MCP session and list tools
	MCP_SERVER_URL=$(MCP_SERVER_URL) uv run mcp-client init

demo:  ## Run demo workflow
	MCP_SERVER_URL=$(MCP_SERVER_URL) uv run mcp-client demo

# Individual tool calls
search-patient:  ## Search patient: make search-patient NAME="John Smith" DOB="1985-03-15"
	MCP_SERVER_URL=$(MCP_SERVER_URL) uv run mcp-client search-patients "$(NAME)" "$(DOB)"

create-patient:  ## Create patient: make create-patient NAME="Jane Doe" DOB="1990-01-01" PHONE="+1234567890"
	MCP_SERVER_URL=$(MCP_SERVER_URL) uv run mcp-client create-patient "$(NAME)" "$(DOB)" "$(PHONE)"

list-practitioners:  ## List practitioners: make list-practitioners SPECIALTY="cardiology"
	MCP_SERVER_URL=$(MCP_SERVER_URL) uv run mcp-client list-practitioners "$(SPECIALTY)"

get-slots:  ## Get slots: make get-slots PRACTITIONER_ID="..." DATE="2026-05-01"
	MCP_SERVER_URL=$(MCP_SERVER_URL) uv run mcp-client get-slots "$(PRACTITIONER_ID)" "$(DATE)"

book:  ## Book appointment: make book PATIENT_ID="..." SLOT_ID="..." REASON="checkup"
	MCP_SERVER_URL=$(MCP_SERVER_URL) uv run mcp-client book "$(PATIENT_ID)" "$(SLOT_ID)" --reason "$(REASON)"

reschedule:  ## Reschedule: make reschedule APPOINTMENT_ID="..." NEW_SLOT_ID="..."
	MCP_SERVER_URL=$(MCP_SERVER_URL) uv run mcp-client reschedule "$(APPOINTMENT_ID)" "$(NEW_SLOT_ID)"

# Help
help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
