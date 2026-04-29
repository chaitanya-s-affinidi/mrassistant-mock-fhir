"""Slot-related MCP tools."""

import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from mcp.server.fastmcp import FastMCP
from mcp_server.fhir import get_fhir_client


TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "Asia/Singapore"))


def register_slot_tools(mcp: FastMCP):
    """Register slot tools with the MCP server."""

    @mcp.tool()
    def get_available_slots(practitioner_id: str, date_timestamp: int) -> dict:
        """
        Get available 15-minute appointment slots for a practitioner on a specific date.
        
        Args:
            practitioner_id: Practitioner ID returned from list_practitioners_by_specialty
            date_timestamp: Unix timestamp representing the desired date (any time on that day)
        
        Returns:
            List of available slots with their IDs and times.
        """
        client = get_fhir_client()
        
        try:
            # Convert timestamp to date in local timezone
            dt = datetime.fromtimestamp(date_timestamp, tz=TIMEZONE)
            date_str = dt.strftime("%Y-%m-%d")
            
            # Calculate start and end of day
            start_of_day = dt.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1) - timedelta(seconds=1)
            
            # Search for Schedule by practitioner
            schedule_bundle = client.search(
                "Schedule",
                actor=f"Practitioner/{practitioner_id}"
            )
            
            schedule_entries = schedule_bundle.get("entry", [])
            if not schedule_entries:
                return {
                    "date": date_str,
                    "date_display": dt.strftime("%A, %B %d %Y"),
                    "practitioner_id": practitioner_id,
                    "practitioner_name": f"Practitioner {practitioner_id}",
                    "timezone": str(TIMEZONE),
                    "slots": [],
                    "message": "No schedule found for this practitioner"
                }
            
            schedule_id = schedule_entries[0]["resource"]["id"]
            
            # Search for free slots in this schedule for the given date
            slot_bundle = client.search(
                "Slot",
                schedule=f"Schedule/{schedule_id}",
                status="free",
                start=f"ge{start_of_day.isoformat()}",
            )
            
            slot_entries = slot_bundle.get("entry", [])
            slots = []
            
            for entry in slot_entries:
                slot = entry["resource"]
                slot_start = datetime.fromisoformat(slot["start"].replace("Z", "+00:00"))
                slot_end = datetime.fromisoformat(slot["end"].replace("Z", "+00:00"))
                
                # Convert to local timezone
                slot_start_local = slot_start.astimezone(TIMEZONE)
                slot_end_local = slot_end.astimezone(TIMEZONE)
                
                # Only include slots on the requested date
                if slot_start_local.date() != dt.date():
                    continue
                
                slots.append({
                    "slot_id": slot["id"],
                    "start_time": slot_start_local.strftime("%H:%M"),
                    "end_time": slot_end_local.strftime("%H:%M"),
                    "start_timestamp": int(slot_start.timestamp())
                })
            
            # Sort by start time
            slots.sort(key=lambda x: x["start_timestamp"])
            
            # Get practitioner name
            try:
                practitioner = client.read("Practitioner", practitioner_id)
                name_parts = practitioner.get("name", [{}])[0]
                prefix = " ".join(name_parts.get("prefix", []))
                given = " ".join(name_parts.get("given", []))
                family = name_parts.get("family", "")
                practitioner_name = f"{prefix} {given} {family}".strip()
            except Exception:
                practitioner_name = f"Practitioner {practitioner_id}"
            
            result = {
                "date": date_str,
                "date_display": dt.strftime("%A, %B %d %Y"),
                "practitioner_id": practitioner_id,
                "practitioner_name": practitioner_name,
                "timezone": str(TIMEZONE),
                "slots": slots
            }
            
            if not slots:
                result["message"] = "No available slots on this date. Please try a different date."
            
            return result
            
        except Exception as e:
            return {
                "date": datetime.fromtimestamp(date_timestamp, tz=TIMEZONE).strftime("%Y-%m-%d"),
                "practitioner_id": practitioner_id,
                "practitioner_name": "",
                "timezone": str(TIMEZONE),
                "slots": [],
                "error": "fhir_error",
                "message": f"Error fetching slots: {str(e)}"
            }
