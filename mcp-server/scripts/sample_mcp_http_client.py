"""Sample MCP HTTP Client for Mr Assistant Integration.

This is a reference implementation showing how Mr Assistant can
call the MCP server over HTTP when deployed behind a public URL.

Usage:
    # Set the MCP server URL
    export MCP_SERVER_URL=https://your-domain.ngrok-free.app/mcp
    
    # Run the client
    uv run python scripts/sample_mcp_http_client.py

For production:
    - Replace with your actual MCP server public URL
    - Add proper error handling and retries
    - Add authentication headers if required by ATG
"""

import json
import os
import sys
from typing import Any

import httpx


class MCPHttpClient:
    """HTTP client for MCP server.
    
    This client communicates with the MCP server over HTTP POST,
    sending JSON-RPC 2.0 requests.
    """
    
    def __init__(self, base_url: str, timeout: float = 30.0):
        """Initialize the MCP HTTP client.
        
        Args:
            base_url: The MCP server URL (e.g., https://your-domain.ngrok-free.app/mcp)
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
    
    def _send_request(self, method: str, params: dict = None) -> dict:
        """Send a JSON-RPC request to the MCP server.
        
        Args:
            method: The JSON-RPC method name
            params: Optional parameters
            
        Returns:
            The result from the server
            
        Raises:
            Exception: If the request fails or returns an error
        """
        request_body = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params or {}
        }
        
        response = self._client.post(
            self.base_url,
            json=request_body,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        result = response.json()
        
        if "error" in result:
            error = result["error"]
            raise Exception(f"MCP Error {error.get('code')}: {error.get('message')}")
        
        return result.get("result", {})
    
    def initialize(self) -> dict:
        """Initialize the MCP session.
        
        Returns:
            Server info including capabilities
        """
        result = self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "mr-assistant-client",
                "version": "1.0.0"
            }
        })
        self._initialized = True
        return result
    
    def list_tools(self) -> list[dict]:
        """List available MCP tools.
        
        Returns:
            List of tool definitions with schemas
        """
        result = self._send_request("tools/list")
        return result.get("tools", [])
    
    def call_tool(self, name: str, arguments: dict = None) -> dict:
        """Call an MCP tool.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool result as a dictionary
        """
        result = self._send_request("tools/call", {
            "name": name,
            "arguments": arguments or {}
        })
        
        # Parse the result content
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            try:
                return json.loads(content[0]["text"])
            except json.JSONDecodeError:
                return {"text": content[0]["text"]}
        return result
    
    # ==========================================
    # Convenience methods for Voice Agent
    # ==========================================
    
    def search_patient(self, name: str, birth_date: str) -> dict:
        """Search for a patient by name and date of birth.
        
        Args:
            name: Patient's full name
            birth_date: Date of birth (YYYY-MM-DD)
            
        Returns:
            Patient info if found, or not found message
        """
        return self.call_tool("search_patients", {
            "name": name,
            "birth_date": birth_date
        })
    
    def create_patient(self, name: str, birth_date: str, phone: str) -> dict:
        """Create a new patient record.
        
        Args:
            name: Patient's full name
            birth_date: Date of birth (YYYY-MM-DD)
            phone: Phone number with country code
            
        Returns:
            Created patient info
        """
        return self.call_tool("create_patient", {
            "name": name,
            "birth_date": birth_date,
            "phone": phone
        })
    
    def get_practitioners(self, specialty: str) -> dict:
        """Get practitioners by specialty.
        
        Args:
            specialty: Specialty code (general-medicine, cardiology, etc.)
            
        Returns:
            List of practitioners
        """
        return self.call_tool("list_practitioners_by_specialty", {
            "specialty": specialty
        })
    
    def get_slots(self, practitioner_id: str, date_timestamp: int) -> dict:
        """Get available appointment slots.
        
        Args:
            practitioner_id: Practitioner ID
            date_timestamp: Unix timestamp for the date
            
        Returns:
            Available slots
        """
        return self.call_tool("get_available_slots", {
            "practitioner_id": practitioner_id,
            "date_timestamp": date_timestamp
        })
    
    def book_appointment(self, patient_id: str, slot_id: str, reason: str = "") -> dict:
        """Book an appointment.
        
        Args:
            patient_id: Patient ID
            slot_id: Slot ID to book
            reason: Reason for visit (optional)
            
        Returns:
            Appointment confirmation or error
        """
        return self.call_tool("create_appointment", {
            "patient_id": patient_id,
            "slot_id": slot_id,
            "reason": reason
        })
    
    def reschedule_appointment(self, appointment_id: str, new_slot_id: str) -> dict:
        """Reschedule an existing appointment.
        
        Args:
            appointment_id: Existing appointment ID
            new_slot_id: New slot ID
            
        Returns:
            Updated appointment info or error
        """
        return self.call_tool("update_appointment", {
            "appointment_id": appointment_id,
            "new_slot_id": new_slot_id
        })
    
    def close(self):
        """Close the HTTP client."""
        self._client.close()


def demo():
    """Demonstrate the MCP HTTP client."""
    
    # Get server URL from environment or use default
    server_url = os.getenv("MCP_SERVER_URL", "http://localhost:3000/mcp")
    
    print("=" * 60)
    print("  MCP HTTP Client Demo")
    print("=" * 60)
    print(f"\nServer URL: {server_url}")
    
    client = MCPHttpClient(server_url)
    
    try:
        # Initialize
        print("\n1. Initializing...")
        info = client.initialize()
        print(f"   Server: {info.get('serverInfo', {}).get('name')}")
        
        # List tools
        print("\n2. Available tools:")
        tools = client.list_tools()
        for tool in tools:
            print(f"   - {tool['name']}")
        
        # Search patient
        print("\n3. Searching for patient 'Camila Lopez'...")
        patient = client.search_patient("Camila Lopez", "1985-03-15")
        print(f"   Result: {json.dumps(patient, indent=2)}")
        
        if patient.get("found"):
            patient_id = patient["patient_id"]
            
            # Get practitioners
            print("\n4. Getting general medicine practitioners...")
            practitioners = client.get_practitioners("general-medicine")
            print(f"   Result: {json.dumps(practitioners, indent=2)}")
            
            if practitioners.get("practitioners"):
                practitioner_id = practitioners["practitioners"][0]["practitioner_id"]
                
                # Get slots
                print(f"\n5. Getting slots for {practitioner_id}...")
                # May 5, 2026
                slots = client.get_slots(practitioner_id, 1746374400)
                print(f"   Date: {slots.get('date_display')}")
                print(f"   Slots: {len(slots.get('slots', []))} available")
                
                if slots.get("slots"):
                    slot_id = slots["slots"][0]["slot_id"]
                    
                    # Book appointment
                    print(f"\n6. Booking appointment...")
                    appointment = client.book_appointment(
                        patient_id=patient_id,
                        slot_id=slot_id,
                        reason="Annual checkup"
                    )
                    print(f"   Result: {json.dumps(appointment, indent=2)}")
        
        print("\n" + "=" * 60)
        print("✓ Demo completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure:")
        print("  1. MCP HTTP server is running: make http-server")
        print("  2. FHIR server is running: make fhir-up")
        print("  3. Mock data is loaded: make load-data")
        sys.exit(1)
    
    finally:
        client.close()


if __name__ == "__main__":
    demo()
