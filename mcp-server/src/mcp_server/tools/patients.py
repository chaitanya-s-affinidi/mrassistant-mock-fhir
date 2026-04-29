"""Patient-related MCP tools."""

from mcp.server.fastmcp import FastMCP
from mcp_server.fhir import get_fhir_client


def register_patient_tools(mcp: FastMCP):
    """Register patient tools with the MCP server."""

    @mcp.tool()
    def search_patients(name: str, birth_date: str) -> dict:
        """
        Search for a patient by name and date of birth.
        
        Args:
            name: Patient's full name (first and last)
            birth_date: Date of birth in YYYY-MM-DD format
        
        Returns:
            Patient details if found, or indication that no match was found.
        """
        client = get_fhir_client()
        
        try:
            # Search by name and birthdate
            bundle = client.search("Patient", name=name, birthdate=birth_date)
            
            entries = bundle.get("entry", [])
            if not entries:
                return {
                    "found": False,
                    "message": "No patient found matching the provided name and date of birth"
                }
            
            # Take the first match
            patient = entries[0]["resource"]
            patient_id = patient["id"]
            
            # Extract name
            name_parts = patient.get("name", [{}])[0]
            given = " ".join(name_parts.get("given", []))
            family = name_parts.get("family", "")
            full_name = f"{given} {family}".strip()
            
            # Extract phone
            phone = None
            for telecom in patient.get("telecom", []):
                if telecom.get("system") == "phone":
                    phone = telecom.get("value")
                    break
            
            return {
                "found": True,
                "patient_id": patient_id,
                "name": full_name,
                "birth_date": patient.get("birthDate"),
                "phone": phone
            }
            
        except Exception as e:
            return {
                "found": False,
                "error": "fhir_error",
                "message": f"Error searching for patient: {str(e)}"
            }

    @mcp.tool()
    def create_patient(name: str, birth_date: str, phone: str) -> dict:
        """
        Create a new patient record with minimal required information.
        
        Args:
            name: Patient's full name (first and last)
            birth_date: Date of birth in YYYY-MM-DD format
            phone: Phone number with country code (e.g., +6591234567)
        
        Returns:
            Created patient ID and confirmation.
        """
        client = get_fhir_client()
        
        # Parse name into given/family
        name_parts = name.strip().split()
        if len(name_parts) >= 2:
            given = name_parts[:-1]
            family = name_parts[-1]
        else:
            given = name_parts
            family = ""
        
        # Build FHIR Patient resource
        patient_resource = {
            "resourceType": "Patient",
            "name": [
                {
                    "use": "official",
                    "family": family,
                    "given": given
                }
            ],
            "birthDate": birth_date,
            "telecom": [
                {
                    "system": "phone",
                    "value": phone,
                    "use": "mobile"
                }
            ]
        }
        
        try:
            result = client.create("Patient", patient_resource)
            patient_id = result.get("id")
            
            return {
                "success": True,
                "patient_id": patient_id,
                "name": name,
                "message": "Patient record created successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "fhir_error",
                "message": f"Error creating patient: {str(e)}"
            }
