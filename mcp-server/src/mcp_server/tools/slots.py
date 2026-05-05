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
    def get_available_slots(practitioner_id: str, date_option: str) -> dict:
        """
        Get available 15-minute appointment slots for a practitioner on a specific date.
        
        Args:
            practitioner_id: Practitioner ID returned from list_practitioners_by_specialty
            date_option: One of: "today", "tomorrow", or a specific date in YYYY-MM-DD format (e.g., "2026-05-07")
        
        Returns:
            Available slots with slot_id and time for the user to choose from.
            Each slot includes: slot_id, start_time, end_time, and a friendly display string.
        """
        client = get_fhir_client()
        
        try:
            # Parse date_option to get the target date
            now = datetime.now(tz=TIMEZONE)
            date_option_lower = date_option.lower().strip()
            
            if date_option_lower == "today":
                dt = now
            elif date_option_lower == "tomorrow":
                dt = now + timedelta(days=1)
            else:
                # Try to parse as YYYY-MM-DD
                try:
                    dt = datetime.strptime(date_option, "%Y-%m-%d").replace(tzinfo=TIMEZONE)
                except ValueError:
                    return {
                        "error": "invalid_date",
                        "message": f"Invalid date format: '{date_option}'. Use 'today', 'tomorrow', or YYYY-MM-DD format (e.g., '2026-05-07').",
                        "valid_options": ["today", "tomorrow", "YYYY-MM-DD (e.g., 2026-05-07)"]
                    }
            
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
                    "display": f"{slot_start_local.strftime('%I:%M %p')} - {slot_end_local.strftime('%I:%M %p')}"
                })
            
            # Sort by start time
            slots.sort(key=lambda x: x["start_time"])
            
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
                "date_option_used": date_option,
                "practitioner_id": practitioner_id,
                "practitioner_name": practitioner_name,
                "timezone": str(TIMEZONE),
                "available_slots": slots,
                "slot_count": len(slots)
            }
            
            if not slots:
                # Suggest alternative dates
                tomorrow = now + timedelta(days=1)
                day_after = now + timedelta(days=2)
                result["message"] = "No available slots on this date."
                result["suggested_dates"] = [
                    {"option": "tomorrow", "date": tomorrow.strftime("%Y-%m-%d"), "display": tomorrow.strftime("%A, %B %d")},
                    {"option": day_after.strftime("%Y-%m-%d"), "date": day_after.strftime("%Y-%m-%d"), "display": day_after.strftime("%A, %B %d")}
                ]
            else:
                result["message"] = f"Found {len(slots)} available slot(s). Please choose one."
            
            return result
            
        except Exception as e:
            return {
                "date_option": date_option,
                "practitioner_id": practitioner_id,
                "available_slots": [],
                "slot_count": 0,
                "error": "fhir_error",
                "message": f"Error fetching slots: {str(e)}"
            }
