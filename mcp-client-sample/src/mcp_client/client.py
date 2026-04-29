"""MCP HTTP Client implementation.

This client communicates with the MCP server over HTTP POST,
sending JSON-RPC 2.0 requests.
"""

import json
from typing import Any

import httpx


class MCPClient:
    """HTTP client for MCP server."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        """Initialize the MCP HTTP client.

        Args:
            base_url: The MCP server URL (e.g., http://localhost:3000/mcp)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._request_id = 0
        self._client = httpx.Client(timeout=timeout)
        self._initialized = False

    def _next_id(self) -> int:
        """Get next request ID."""
        self._request_id += 1
        return self._request_id

    def _send_request(self, method: str, params: dict | None = None) -> dict:
        """Send a JSON-RPC request to the MCP server.

        Args:
            method: The JSON-RPC method name
            params: Optional parameters

        Returns:
            The result from the server

        Raises:
            MCPError: If the request fails or returns an error
        """
        request_body = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params or {},
        }

        response = self._client.post(
            self.base_url,
            json=request_body,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()

        result = response.json()

        if "error" in result:
            error = result["error"]
            raise MCPError(error.get("code", -1), error.get("message", "Unknown error"))

        return result.get("result", {})

    def initialize(self) -> dict:
        """Initialize the MCP session.

        Returns:
            Server info including capabilities
        """
        result = self._send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mrassistant-mcp-client", "version": "1.0.0"},
            },
        )
        self._initialized = True
        return result

    def list_tools(self) -> list[dict]:
        """List available MCP tools.

        Returns:
            List of tool definitions with schemas
        """
        result = self._send_request("tools/list")
        return result.get("tools", [])

    def call_tool(self, name: str, arguments: dict | None = None) -> Any:
        """Call an MCP tool.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result (parsed JSON if text content)
        """
        result = self._send_request("tools/call", {"name": name, "arguments": arguments or {}})

        # Parse the result content
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            try:
                return json.loads(content[0]["text"])
            except json.JSONDecodeError:
                return {"text": content[0]["text"]}
        return result

    # ==========================================
    # Tool-specific methods
    # ==========================================

    def search_patients(self, name: str, birth_date: str) -> dict:
        """Search for a patient by name and date of birth.

        Args:
            name: Patient's full name
            birth_date: Date of birth (YYYY-MM-DD)

        Returns:
            Patient info if found, or not found message
        """
        return self.call_tool("search_patients", {"name": name, "birth_date": birth_date})

    def create_patient(self, name: str, birth_date: str, phone: str) -> dict:
        """Create a new patient record.

        Args:
            name: Patient's full name
            birth_date: Date of birth (YYYY-MM-DD)
            phone: Phone number with country code

        Returns:
            Created patient info
        """
        return self.call_tool(
            "create_patient", {"name": name, "birth_date": birth_date, "phone": phone}
        )

    def list_practitioners(self, specialty: str) -> dict:
        """Get practitioners by specialty.

        Args:
            specialty: Specialty code (general-medicine, cardiology, etc.)

        Returns:
            List of practitioners
        """
        return self.call_tool("list_practitioners_by_specialty", {"specialty": specialty})

    def get_slots(self, practitioner_id: str, date_timestamp: int) -> dict:
        """Get available appointment slots.

        Args:
            practitioner_id: Practitioner ID
            date_timestamp: Unix timestamp for the date

        Returns:
            Available slots
        """
        return self.call_tool(
            "get_available_slots",
            {"practitioner_id": practitioner_id, "date_timestamp": date_timestamp},
        )

    def create_appointment(self, patient_id: str, slot_id: str, reason: str = "") -> dict:
        """Book an appointment.

        Args:
            patient_id: Patient ID
            slot_id: Slot ID to book
            reason: Reason for visit (optional)

        Returns:
            Appointment confirmation or error
        """
        return self.call_tool(
            "create_appointment", {"patient_id": patient_id, "slot_id": slot_id, "reason": reason}
        )

    def update_appointment(self, appointment_id: str, new_slot_id: str) -> dict:
        """Reschedule an existing appointment.

        Args:
            appointment_id: Existing appointment ID
            new_slot_id: New slot ID

        Returns:
            Updated appointment info or error
        """
        return self.call_tool(
            "update_appointment", {"appointment_id": appointment_id, "new_slot_id": new_slot_id}
        )

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class MCPError(Exception):
    """MCP protocol error."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"MCP Error {code}: {message}")
