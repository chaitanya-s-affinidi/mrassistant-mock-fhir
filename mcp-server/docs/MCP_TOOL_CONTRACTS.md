# MCP Tool Contracts

This document defines the JSON schemas for all MCP tools exposed by the Hospital FHIR MCP Server.

---

## Tool 1: `search_patients`

**Purpose**: Find a patient by name and date of birth for identity verification.

### Input Schema

```json
{
  "name": "search_patients",
  "description": "Search for a patient by name and date of birth. Returns patient details if found, or indicates no match.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "description": "Patient's full name (first and last)"
      },
      "birth_date": {
        "type": "string",
        "description": "Date of birth in YYYY-MM-DD format"
      }
    },
    "required": ["name", "birth_date"]
  }
}
```

### Response (Patient Found)

```json
{
  "found": true,
  "patient_id": "patient-123",
  "name": "Camila Lopez",
  "birth_date": "1985-03-15",
  "phone": "+6591234567"
}
```

### Response (Patient Not Found)

```json
{
  "found": false,
  "message": "No patient found matching the provided name and date of birth"
}
```

---

## Tool 2: `create_patient`

**Purpose**: Register a new patient when identity verification finds no existing record.

### Input Schema

```json
{
  "name": "create_patient",
  "description": "Create a new patient record with minimal required information.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "description": "Patient's full name (first and last)"
      },
      "birth_date": {
        "type": "string",
        "description": "Date of birth in YYYY-MM-DD format"
      },
      "phone": {
        "type": "string",
        "description": "Phone number with country code (e.g., +6591234567)"
      }
    },
    "required": ["name", "birth_date", "phone"]
  }
}
```

### Response (Success)

```json
{
  "success": true,
  "patient_id": "patient-456",
  "name": "John Doe",
  "message": "Patient record created successfully"
}
```

### Response (Validation Error)

```json
{
  "success": false,
  "error": "validation_error",
  "message": "Invalid phone number format. Please use format: +65XXXXXXXX"
}
```

---

## Tool 3: `list_practitioners_by_specialty`

**Purpose**: Get available practitioners for a given specialty to route patients based on visit reason.

### Input Schema

```json
{
  "name": "list_practitioners_by_specialty",
  "description": "List practitioners who practice a given medical specialty.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "specialty": {
        "type": "string",
        "enum": ["general-medicine", "cardiology", "dermatology", "obgyn", "orthopedics"],
        "description": "Specialty code. See SPECIALTY_MAPPING.md for mapping from visit reasons."
      }
    },
    "required": ["specialty"]
  }
}
```

### Response (Practitioners Found)

```json
{
  "specialty": "cardiology",
  "practitioners": [
    {
      "practitioner_id": "practitioner-002",
      "name": "Dr. Lim Mei Ling",
      "specialty": "cardiology",
      "specialty_display": "Cardiology"
    }
  ]
}
```

### Response (No Practitioners)

```json
{
  "specialty": "orthopedics",
  "practitioners": [],
  "message": "No practitioners available for this specialty"
}
```

---

## Tool 4: `get_available_slots`

**Purpose**: Fetch bookable appointment slots for a practitioner on a specific date.

### Input Schema

```json
{
  "name": "get_available_slots",
  "description": "Get available 15-minute appointment slots for a practitioner on a specific date.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "practitioner_id": {
        "type": "string",
        "description": "Practitioner ID returned from list_practitioners_by_specialty"
      },
      "date_timestamp": {
        "type": "integer",
        "description": "Unix timestamp representing the desired date (any time on that day)"
      }
    },
    "required": ["practitioner_id", "date_timestamp"]
  }
}
```

### Response (Slots Available)

```json
{
  "date": "2026-05-05",
  "date_display": "Monday, May 5th 2026",
  "practitioner_id": "practitioner-001",
  "practitioner_name": "Dr. Tan Wei Ming",
  "timezone": "Asia/Singapore",
  "slots": [
    {
      "slot_id": "slot-001",
      "start_time": "09:00",
      "end_time": "09:15",
      "start_timestamp": 1746406800
    },
    {
      "slot_id": "slot-002",
      "start_time": "09:15",
      "end_time": "09:30",
      "start_timestamp": 1746407700
    },
    {
      "slot_id": "slot-003",
      "start_time": "10:00",
      "end_time": "10:15",
      "start_timestamp": 1746410400
    },
    {
      "slot_id": "slot-004",
      "start_time": "14:00",
      "end_time": "14:15",
      "start_timestamp": 1746424800
    }
  ]
}
```

### Response (No Slots)

```json
{
  "date": "2026-05-05",
  "date_display": "Monday, May 5th 2026",
  "practitioner_id": "practitioner-001",
  "practitioner_name": "Dr. Tan Wei Ming",
  "timezone": "Asia/Singapore",
  "slots": [],
  "message": "No available slots on this date. Please try a different date."
}
```

---

## Tool 5: `create_appointment`

**Purpose**: Book an appointment for a patient at a specific slot.

### Input Schema

```json
{
  "name": "create_appointment",
  "description": "Create an appointment for a patient at a specific time slot.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "patient_id": {
        "type": "string",
        "description": "Patient ID from search_patients or create_patient"
      },
      "slot_id": {
        "type": "string",
        "description": "Slot ID from get_available_slots"
      },
      "reason": {
        "type": "string",
        "description": "Reason for the appointment (optional)"
      }
    },
    "required": ["patient_id", "slot_id"]
  }
}
```

### Response (Success)

```json
{
  "success": true,
  "appointment_id": "appointment-789",
  "patient_name": "Camila Lopez",
  "practitioner_name": "Dr. Tan Wei Ming",
  "date": "2026-05-05",
  "date_display": "Monday, May 5th 2026",
  "time": "10:00",
  "end_time": "10:15",
  "reason": "Annual checkup",
  "message": "Appointment booked successfully"
}
```

### Response (Slot No Longer Available)

```json
{
  "success": false,
  "error": "slot_unavailable",
  "message": "This slot is no longer available. Please select another slot."
}
```

### Response (Patient Not Found)

```json
{
  "success": false,
  "error": "patient_not_found",
  "message": "Patient ID not found. Please verify the patient first."
}
```

---

## Tool 6: `update_appointment`

**Purpose**: Reschedule an existing appointment to a different slot.

### Input Schema

```json
{
  "name": "update_appointment",
  "description": "Reschedule an existing appointment to a new time slot.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "appointment_id": {
        "type": "string",
        "description": "Existing appointment ID to reschedule"
      },
      "new_slot_id": {
        "type": "string",
        "description": "New slot ID from get_available_slots"
      }
    },
    "required": ["appointment_id", "new_slot_id"]
  }
}
```

### Response (Success)

```json
{
  "success": true,
  "appointment_id": "appointment-789",
  "previous_date": "2026-05-05",
  "previous_time": "10:00",
  "new_date": "2026-05-06",
  "new_date_display": "Tuesday, May 6th 2026",
  "new_time": "14:00",
  "practitioner_name": "Dr. Tan Wei Ming",
  "message": "Appointment rescheduled successfully"
}
```

### Response (New Slot Unavailable)

```json
{
  "success": false,
  "error": "slot_unavailable",
  "message": "The requested slot is no longer available. Please select another slot."
}
```

### Response (Appointment Not Found)

```json
{
  "success": false,
  "error": "appointment_not_found",
  "message": "Appointment ID not found."
}
```

---

## Error Response Format

All tools follow a consistent error format:

```json
{
  "success": false,
  "error": "<error_code>",
  "message": "<human_readable_message>"
}
```

### Error Codes

| Code | Meaning |
|------|---------|
| `validation_error` | Input data failed validation |
| `patient_not_found` | Patient ID doesn't exist |
| `practitioner_not_found` | Practitioner ID doesn't exist |
| `slot_unavailable` | Slot was booked by someone else |
| `appointment_not_found` | Appointment ID doesn't exist |
| `fhir_error` | Unexpected error from FHIR server |

---

## Timezone Handling

- All `date_timestamp` inputs are **Unix timestamps (UTC)**
- All `start_timestamp` outputs are **Unix timestamps (UTC)**
- All human-readable times (`start_time`, `time`, etc.) are in **Asia/Singapore (UTC+8)**
- The `timezone` field indicates the timezone used for display times
