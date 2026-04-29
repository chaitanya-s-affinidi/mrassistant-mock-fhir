"""Appointment-related MCP tools."""

import os
from datetime import datetime
from zoneinfo import ZoneInfo

from mcp.server.fastmcp import FastMCP
from mcp_server.fhir import get_fhir_client


TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "Asia/Singapore"))


def register_appointment_tools(mcp: FastMCP):
    """Register appointment tools with the MCP server."""

    @mcp.tool()
    def create_appointment(patient_id: str, slot_id: str, reason: str = "") -> dict:
        """
        Create an appointment for a patient at a specific time slot.
        
        Args:
            patient_id: Patient ID from search_patients or create_patient
            slot_id: Slot ID from get_available_slots
            reason: Reason for the appointment (optional)
        
        Returns:
            Appointment confirmation with ID, date, and time.
        """
        client = get_fhir_client()
        
        try:
            # First, verify the slot is still free
            slot = client.read("Slot", slot_id)
            
            if slot.get("status") != "free":
                return {
                    "success": False,
                    "error": "slot_unavailable",
                    "message": "This slot is no longer available. Please select another slot."
                }
            
            # Get slot times
            slot_start = datetime.fromisoformat(slot["start"].replace("Z", "+00:00"))
            slot_end = datetime.fromisoformat(slot["end"].replace("Z", "+00:00"))
            slot_start_local = slot_start.astimezone(TIMEZONE)
            
            # Get schedule to find practitioner
            schedule_ref = slot.get("schedule", {}).get("reference", "")
            schedule_id = schedule_ref.split("/")[-1] if "/" in schedule_ref else ""
            
            practitioner_id = ""
            practitioner_name = ""
            if schedule_id:
                schedule = client.read("Schedule", schedule_id)
                for actor in schedule.get("actor", []):
                    if actor.get("reference", "").startswith("Practitioner/"):
                        practitioner_id = actor["reference"].split("/")[-1]
                        practitioner_name = actor.get("display", "")
                        break
            
            # Verify patient exists
            try:
                patient = client.read("Patient", patient_id)
                name_parts = patient.get("name", [{}])[0]
                given = " ".join(name_parts.get("given", []))
                family = name_parts.get("family", "")
                patient_name = f"{given} {family}".strip()
            except Exception:
                return {
                    "success": False,
                    "error": "patient_not_found",
                    "message": "Patient ID not found. Please verify the patient first."
                }
            
            # Create appointment
            appointment_resource = {
                "resourceType": "Appointment",
                "status": "booked",
                "slot": [{"reference": f"Slot/{slot_id}"}],
                "start": slot["start"],
                "end": slot["end"],
                "participant": [
                    {
                        "actor": {"reference": f"Patient/{patient_id}", "display": patient_name},
                        "status": "accepted"
                    }
                ]
            }
            
            if practitioner_id:
                appointment_resource["participant"].append({
                    "actor": {"reference": f"Practitioner/{practitioner_id}", "display": practitioner_name},
                    "status": "accepted"
                })
            
            if reason:
                appointment_resource["reasonCode"] = [{"text": reason}]
            
            # Create the appointment
            result = client.create("Appointment", appointment_resource)
            appointment_id = result.get("id")
            
            # Update slot status to busy
            slot["status"] = "busy"
            client.update("Slot", slot_id, slot)
            
            return {
                "success": True,
                "appointment_id": appointment_id,
                "patient_name": patient_name,
                "practitioner_name": practitioner_name,
                "date": slot_start_local.strftime("%Y-%m-%d"),
                "date_display": slot_start_local.strftime("%A, %B %d %Y"),
                "time": slot_start_local.strftime("%H:%M"),
                "end_time": slot_end.astimezone(TIMEZONE).strftime("%H:%M"),
                "reason": reason,
                "message": "Appointment booked successfully"
            }
            
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                return {
                    "success": False,
                    "error": "slot_unavailable",
                    "message": "This slot is no longer available. Please select another slot."
                }
            return {
                "success": False,
                "error": "fhir_error",
                "message": f"Error creating appointment: {error_msg}"
            }

    @mcp.tool()
    def update_appointment(appointment_id: str, new_slot_id: str) -> dict:
        """
        Reschedule an existing appointment to a new time slot.
        
        Args:
            appointment_id: Existing appointment ID to reschedule
            new_slot_id: New slot ID from get_available_slots
        
        Returns:
            Confirmation with old and new appointment times.
        """
        client = get_fhir_client()
        
        try:
            # Get existing appointment
            try:
                appointment = client.read("Appointment", appointment_id)
            except Exception:
                return {
                    "success": False,
                    "error": "appointment_not_found",
                    "message": "Appointment ID not found."
                }
            
            # Get old slot info
            old_slot_ref = appointment.get("slot", [{}])[0].get("reference", "")
            old_slot_id = old_slot_ref.split("/")[-1] if "/" in old_slot_ref else ""
            old_start = datetime.fromisoformat(appointment["start"].replace("Z", "+00:00"))
            old_start_local = old_start.astimezone(TIMEZONE)
            
            # Verify new slot is free
            try:
                new_slot = client.read("Slot", new_slot_id)
            except Exception:
                return {
                    "success": False,
                    "error": "slot_unavailable",
                    "message": "The requested slot is no longer available. Please select another slot."
                }
            
            if new_slot.get("status") != "free":
                return {
                    "success": False,
                    "error": "slot_unavailable",
                    "message": "The requested slot is no longer available. Please select another slot."
                }
            
            new_start = datetime.fromisoformat(new_slot["start"].replace("Z", "+00:00"))
            new_end = datetime.fromisoformat(new_slot["end"].replace("Z", "+00:00"))
            new_start_local = new_start.astimezone(TIMEZONE)
            
            # Get practitioner name from appointment
            practitioner_name = ""
            for participant in appointment.get("participant", []):
                ref = participant.get("actor", {}).get("reference", "")
                if ref.startswith("Practitioner/"):
                    practitioner_name = participant.get("actor", {}).get("display", "")
                    break
            
            # Update appointment with new slot
            appointment["slot"] = [{"reference": f"Slot/{new_slot_id}"}]
            appointment["start"] = new_slot["start"]
            appointment["end"] = new_slot["end"]
            
            client.update("Appointment", appointment_id, appointment)
            
            # Free up old slot
            if old_slot_id:
                try:
                    old_slot = client.read("Slot", old_slot_id)
                    old_slot["status"] = "free"
                    client.update("Slot", old_slot_id, old_slot)
                except Exception:
                    pass  # Best effort
            
            # Mark new slot as busy
            new_slot["status"] = "busy"
            client.update("Slot", new_slot_id, new_slot)
            
            return {
                "success": True,
                "appointment_id": appointment_id,
                "previous_date": old_start_local.strftime("%Y-%m-%d"),
                "previous_time": old_start_local.strftime("%H:%M"),
                "new_date": new_start_local.strftime("%Y-%m-%d"),
                "new_date_display": new_start_local.strftime("%A, %B %d %Y"),
                "new_time": new_start_local.strftime("%H:%M"),
                "practitioner_name": practitioner_name,
                "message": "Appointment rescheduled successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "fhir_error",
                "message": f"Error rescheduling appointment: {str(e)}"
            }
