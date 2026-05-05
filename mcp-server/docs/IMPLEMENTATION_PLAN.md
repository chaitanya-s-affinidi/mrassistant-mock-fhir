# Implementation Plan: Hospital FHIR MCP Server

**Created**: 2026-04-29  
**Target**: May 13 Demo  
**Status**: Planning Complete

---

## Decision Log

| # | Decision | Answer |
|---|----------|--------|
| 1 | MCP Server ownership | Hospital IT deploys (Python code + docs) |
| 2 | Call flow | Hospital IVR → Mr Assistant Voice Agent |
| 3 | Language | Python |
| 4 | Identity Verification | Name + DOB → search_patients |
| 5 | Which Doctor | Reason → PractitionerRole specialty lookup |
| 6 | Slot Selection | Patient specifies date → show slots |
| 7 | Output Format | JSON |
| 8 | Condition mapping | FHIR PractitionerRole with custom codes |
| 9 | Identity fail | Create new patient |
| 10 | Slot conflict | Error → re-fetch |
| 11 | FHIR Server | HAPI FHIR (Docker) |
| 12 | ATG | Separate phase |
| 13 | Create Patient data | Name + DOB + phone (minimal) |
| 14 | Specialty codes | Custom (general-medicine, cardiology, dermatology, obgyn, orthopedics) |
| 15 | Date format | Unix timestamp |
| 16 | Slot duration | Fixed 15-minute slots |
| 17 | Mock data scale | Minimal (5 patients, 3 practitioners, 10 slots) |
| 18 | Specialties | 5 specialties |
| 19 | Timezone | Singapore (UTC+8) |
| 20 | Session state | Voice Agent holds state in `{{variables}}` |
| 21 | Reason mapping | Mr Assistant prompt engineering (see SPECIALTY_MAPPING.md) |

---

## Architecture

```
Patient → Hospital IVR → Mr Assistant Voice Agent
                              │
                         MCP Client
                              │
                    ┌─────────────────────────────────────┐
                    │     Hospital Trust Boundary         │
                    │  ┌─────────────────────────────┐    │
                    │  │   MCP Server (Python)       │    │
                    │  │   - search_patients         │    │
                    │  │   - create_patient          │    │
                    │  │   - list_practitioners      │    │
                    │  │   - get_available_slots     │    │
                    │  │   - create_appointment      │    │
                    │  │   - update_appointment      │    │
                    │  └─────────────┬───────────────┘    │
                    │                │                    │
                    │  ┌─────────────▼───────────────┐    │
                    │  │   HAPI FHIR (Docker)        │    │
                    │  │   Patient, Practitioner,    │    │
                    │  │   Schedule, Slot, Appt      │    │
                    │  └─────────────────────────────┘    │
                    └─────────────────────────────────────┘
```

---

## Project Structure

```
hospital-fhir-mcp/
├── src/mcp_server/
│   ├── __init__.py
│   ├── server.py              # MCP server entry point (stdio)
│   ├── http_server.py         # HTTP wrapper for public deployment
│   ├── fhir/__init__.py       # FHIR client utilities
│   └── tools/
│       ├── patients.py        # search_patients, create_patient
│       ├── practitioners.py   # list_practitioners_by_specialty
│       ├── slots.py           # get_available_slots
│       └── appointments.py    # create_appointment, update_appointment
├── data/
│   └── mock_bundle.json       # FHIR Bundle with test data
├── docs/
│   ├── IMPLEMENTATION_PLAN.md
│   ├── MCP_TOOL_CONTRACTS.md
│   ├── MCP_CLIENT_INTEGRATION.md
│   └── SPECIALTY_MAPPING.md
├── scripts/
│   ├── load_mock_data.py
│   ├── test_tools.py
│   ├── test_mcp_client.py
│   ├── test_fhir_curl.sh
│   ├── sample_mcp_http_client.py
│   └── start_ngrok.sh
├── docker-compose.yml
├── pyproject.toml
├── Makefile
└── README.md
```

---

## MCP Tools Summary

| Tool | Input | Output | FHIR Operation |
|------|-------|--------|----------------|
| `search_patients` | name, birth_date | patient_id or not found | `GET /Patient?name=&birthdate=` |
| `create_patient` | name, birth_date, phone | patient_id | `POST /Patient` |
| `list_practitioners_by_specialty` | specialty | practitioners[] | `GET /PractitionerRole?specialty=` |
| `get_available_slots` | practitioner_id, date_option | available_slots[] | `GET /Slot?schedule.actor=&status=free` |
| `create_appointment` | patient_id, slot_id, reason? | appointment_id | `POST /Appointment` |
| `update_appointment` | appointment_id, new_slot_id | success | `PUT /Appointment/{id}` |

See [MCP_TOOL_CONTRACTS.md](MCP_TOOL_CONTRACTS.md) for full JSON schemas.

---

## Voice Agent Workflow Integration

### Updated Node Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Node 1: "start" (Identity Verification)                         │
│ First Message: "Hello! To get started, may I have your full    │
│                 name and date of birth?"                        │
│ Extract: {{patient_name}}, {{birth_date}}                       │
│ Action: Call search_patients(name, birth_date)                  │
│         → If found: store {{patient_id}}, proceed               │
│         → If not found: go to "new_patient" node                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Node 1b: "new_patient" (Registration)                           │
│ First Message: "I don't have a record for you yet. Can I have  │
│                 your phone number to create one?"               │
│ Extract: {{phone}}                                              │
│ Action: Call create_patient(name, birth_date, phone)            │
│         → Store {{patient_id}}, proceed                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Node 2: "reason" (Visit Reason)                                 │
│ First Message: "What's the reason for your visit today?"        │
│ Extract: {{reason}}, {{specialty}} (mapped via prompt)          │
│ Action: Call list_practitioners_by_specialty(specialty)         │
│         → Store {{practitioner_id}}, {{practitioner_name}}      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Node 3: "pick_date" (Date Selection)                            │
│ First Message: "When would you like to come in?"                │
│ Extract: {{preferred_date}} (unix timestamp)                    │
│ Action: Call get_available_slots(practitioner_id, date)         │
│         → Present slots to patient                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Node 4: "pick_slot" (Slot Selection)                            │
│ First Message: "Dr. {{practitioner_name}} has openings at       │
│                 [times]. Which works for you?"                  │
│ Extract: {{slot_id}}                                            │
│ Action: Call create_appointment(patient_id, slot_id, reason)    │
│         → If success: proceed to confirmation                   │
│         → If slot_unavailable: re-fetch slots, retry            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Node 5: "confirmation" (Booking Complete)                       │
│ First Message: "You're all set! Your appointment with           │
│                 Dr. {{practitioner_name}} is on {{date}} at     │
│                 {{time}}. Anything else I can help with?"       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Infrastructure (Day 1-2)

| Task | Est. Time | Deliverable |
|------|-----------|-------------|
| Set up Python project with `uv` | 30 min | pyproject.toml, src structure |
| Docker Compose for HAPI FHIR | 30 min | docker-compose.yml |
| FHIR client utility | 1 hr | src/mcp_server/fhir/client.py |
| Create mock FHIR Bundle | 2 hr | data/mock_bundle.json |
| Load script | 30 min | scripts/load_mock_data.py |
| Verify FHIR queries work | 1 hr | Manual testing |

**Checkpoint**: Can query Patient, Practitioner, Slot from HAPI FHIR

### Phase 2: MCP Tools (Day 3-5)

| Task | Est. Time | Deliverable |
|------|-----------|-------------|
| MCP server scaffold (FastMCP) | 1 hr | src/mcp_server/server.py |
| `search_patients` tool | 1 hr | tools/patients.py |
| `create_patient` tool | 1 hr | tools/patients.py |
| `list_practitioners_by_specialty` tool | 1 hr | tools/practitioners.py |
| `get_available_slots` tool | 1.5 hr | tools/slots.py |
| `create_appointment` tool | 1.5 hr | tools/appointments.py |
| `update_appointment` tool | 1 hr | tools/appointments.py |
| Error handling (slot conflicts, not found) | 1 hr | All tools |

**Checkpoint**: All 6 MCP tools working via `mcp dev`

### Phase 3: Integration Testing (Day 6-7)

| Task | Est. Time | Deliverable |
|------|-----------|-------------|
| End-to-end test script | 1 hr | tests/test_e2e.py |
| Test identity verification flow | 1 hr | — |
| Test new patient registration | 30 min | — |
| Test appointment booking | 1 hr | — |
| Test slot conflict handling | 30 min | — |
| Test rescheduling | 30 min | — |

**Checkpoint**: All flows work end-to-end

### Phase 4: Mr Assistant Integration (Day 8-10)

| Task | Est. Time | Deliverable |
|------|-----------|-------------|
| Configure MCP Server public URL | 1 hr | ngrok or cloud deploy |
| Update Mr Assistant workflow nodes | 2 hr | — |
| Add MCP tool calls to workflow | 2 hr | — |
| Test voice agent → MCP flow | 2 hr | — |
| Fix issues | 2 hr | — |

**Checkpoint**: Voice call triggers MCP tools successfully

### Phase 5: Polish (Day 11-13)

| Task | Est. Time | Deliverable |
|------|-----------|-------------|
| Dry run full demo | 1 hr | — |
| Fix edge cases | 2 hr | — |
| Rehearse demo script | 1 hr | — |
| Prepare fallback (curl demo) | 1 hr | — |
| Network/audio testing | 1 hr | — |

**Checkpoint**: Ready for May 13 demo

---

## Mock Data Specification

### Patients (5)

| Name | DOB | Phone | Notes |
|------|-----|-------|-------|
| Camila Lopez | 1985-03-15 | +6591234567 | Demo patient 1 |
| James Chen | 1972-08-22 | +6592345678 | Demo patient 2 |
| Maria Santos | 1990-11-30 | +6593456789 | Demo patient 3 |
| Robert Williams | 1968-04-05 | +6594567890 | Demo patient 4 |
| Sarah Johnson | 2001-07-19 | +6595678901 | Demo patient 5 |

### Practitioners (3)

| Name | Specialty | Notes |
|------|-----------|-------|
| Dr. Tan Wei Ming | general-medicine | Primary demo doctor |
| Dr. Lim Mei Ling | cardiology | Heart specialist |
| Dr. Lee Kai Wen | dermatology | Skin specialist |

### Slots (15+ per practitioner)

- Date range: May 5-9, 2026
- Times: 09:00, 09:15, 09:30, 10:00, 10:15, 14:00, 14:15, 14:30, 15:00
- Duration: 15 minutes each
- Status: `free`

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Mr Assistant API integration fails | High | Prepare curl/Postman demo showing MCP tools directly |
| HAPI FHIR Docker issues | Medium | Test on multiple machines, have backup instance |
| Slot search performance | Low | Mock data is small, not a concern |
| Network at demo venue | Medium | Test on 4G, prepare local-only fallback |

---

## Success Criteria

- [ ] Voice Agent can verify patient identity via name + DOB
- [ ] New patients can be registered during call
- [ ] Available slots are fetched from FHIR in real-time
- [ ] Appointments are created in FHIR
- [ ] Slot conflicts are handled gracefully
- [ ] Demo runs end-to-end without manual intervention
