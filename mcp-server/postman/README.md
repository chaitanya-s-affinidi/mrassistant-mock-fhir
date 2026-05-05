# Postman Collection for Hospital MCP Tools

This folder contains Postman collections for testing the Hospital MCP server.

## Files

- `Hospital_MCP_Tools.postman_collection.json` - All MCP tool calls
- `Hospital_MCP_Local.postman_environment.json` - Environment variables for local testing

## Setup

1. Import both files into Postman
2. Select "Hospital MCP Local" environment
3. Start the MCP HTTP server: `make http-server` (port 3000)
4. Ensure HAPI FHIR is running: `make dev-up` (port 8080)

## Available Tools

| Tool | Description |
|------|-------------|
| `search_patients` | Search patient by name and DOB |
| `create_patient` | Create new patient record |
| `list_practitioners_by_specialty` | Find doctors by specialty |
| `get_available_slots` | Get available appointment slots |
| `create_appointment` | Book an appointment |
| `update_appointment` | Reschedule an appointment |

## Collection Structure

- **Patient Tools** - Search and create patients
- **Practitioner Tools** - List doctors by specialty
- **Slot Tools** - Get available time slots
- **Appointment Tools** - Book and reschedule appointments
- **MCP Protocol** - List tools, health check
- **Complete Booking Flow** - End-to-end booking workflow

## Valid Specialty Codes

- `general-medicine`
- `cardiology`
- `dermatology`
- `obgyn`
- `orthopedics`

## Date Options for get_available_slots

- `"today"` - Today's slots
- `"tomorrow"` - Tomorrow's slots
- `"YYYY-MM-DD"` - Specific date (e.g., "2026-05-07")

## Example Flow

1. Search for patient: `search_patients("Camila Lopez", "1985-03-15")`
2. Find dermatologist: `list_practitioners_by_specialty("dermatology")`
3. Get slots: `get_available_slots("practitioner-003", "tomorrow")`
4. Book: `create_appointment("patient-001", "slot-013", "Skin rash")`
