"""Practitioner-related MCP tools."""

from mcp.server.fastmcp import FastMCP
from mcp_server.fhir import get_fhir_client


# Custom specialty codes to display names
SPECIALTY_DISPLAY = {
    "general-medicine": "General Medicine",
    "cardiology": "Cardiology",
    "dermatology": "Dermatology",
    "obgyn": "OB/GYN",
    "orthopedics": "Orthopedics",
}


def register_practitioner_tools(mcp: FastMCP):
    """Register practitioner tools with the MCP server."""

    @mcp.tool()
    def list_practitioners_by_specialty(specialty: str) -> dict:
        """
        List practitioners who practice a given medical specialty.
        
        Args:
            specialty: Specialty code (general-medicine, cardiology, dermatology, obgyn, orthopedics)
        
        Returns:
            List of practitioners with their IDs and names.
        """
        if specialty not in SPECIALTY_DISPLAY:
            return {
                "specialty": specialty,
                "practitioners": [],
                "error": "invalid_specialty",
                "message": f"Invalid specialty code. Valid codes: {', '.join(SPECIALTY_DISPLAY.keys())}"
            }
        
        client = get_fhir_client()
        
        try:
            # Search PractitionerRole by specialty code
            # Using custom code system for demo
            bundle = client.search(
                "PractitionerRole",
                specialty=f"http://hospital.example.com/specialty|{specialty}"
            )
            
            entries = bundle.get("entry", [])
            practitioners = []
            
            for entry in entries:
                role = entry["resource"]
                practitioner_ref = role.get("practitioner", {}).get("reference", "")
                practitioner_id = practitioner_ref.split("/")[-1] if "/" in practitioner_ref else practitioner_ref
                
                # Get practitioner name from the display or fetch it
                practitioner_name = role.get("practitioner", {}).get("display", f"Practitioner {practitioner_id}")
                
                practitioners.append({
                    "practitioner_id": practitioner_id,
                    "name": practitioner_name,
                    "specialty": specialty,
                    "specialty_display": SPECIALTY_DISPLAY[specialty]
                })
            
            if not practitioners:
                return {
                    "specialty": specialty,
                    "practitioners": [],
                    "message": "No practitioners available for this specialty"
                }
            
            return {
                "specialty": specialty,
                "practitioners": practitioners
            }
            
        except Exception as e:
            return {
                "specialty": specialty,
                "practitioners": [],
                "error": "fhir_error",
                "message": f"Error searching for practitioners: {str(e)}"
            }
