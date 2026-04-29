#!/bin/bash
# Test FHIR endpoints directly with curl
# Usage: ./scripts/test_fhir_curl.sh

set -e

FHIR_URL="${FHIR_BASE_URL:-http://localhost:8080/fhir}"

echo "========================================"
echo "  FHIR Endpoint Tests"
echo "  Server: $FHIR_URL"
echo "========================================"

# Check server is running
echo -e "\nChecking FHIR server..."
if ! curl -sf "$FHIR_URL/metadata" > /dev/null; then
    echo "✗ FHIR server is not running!"
    echo "  Start it with: make fhir-up && make load-data"
    exit 1
fi
echo "✓ FHIR server is running"

echo -e "\n----------------------------------------"
echo "TEST 1: List all patients"
echo "----------------------------------------"
curl -s "$FHIR_URL/Patient" | jq '{total: .total, patients: [.entry[].resource | {id: .id, name: .name[0].given[0] + " " + .name[0].family}]}'

echo -e "\n----------------------------------------"
echo "TEST 2: Search patient by name and DOB"
echo "----------------------------------------"
curl -s "$FHIR_URL/Patient?name=Camila&birthdate=1985-03-15" | jq '.entry[0].resource | {id: .id, name: .name[0].given[0] + " " + .name[0].family, birthDate: .birthDate}'

echo -e "\n----------------------------------------"
echo "TEST 3: List practitioners"
echo "----------------------------------------"
curl -s "$FHIR_URL/Practitioner" | jq '{total: .total, practitioners: [.entry[].resource | {id: .id, name: (.name[0].prefix[0] // "") + " " + .name[0].given[0] + " " + .name[0].family}]}'

echo -e "\n----------------------------------------"
echo "TEST 4: List practitioner roles (specialties)"
echo "----------------------------------------"
curl -s "$FHIR_URL/PractitionerRole" | jq '{roles: [.entry[].resource | {id: .id, practitioner: .practitioner.display, specialty: .specialty[0].coding[0].code}]}'

echo -e "\n----------------------------------------"
echo "TEST 5: Search by specialty (general-medicine)"
echo "----------------------------------------"
curl -s "$FHIR_URL/PractitionerRole?specialty=http://hospital.example.com/specialty|general-medicine" | jq '.entry[0].resource | {practitioner: .practitioner.display, specialty: .specialty[0].coding[0].display}'

echo -e "\n----------------------------------------"
echo "TEST 6: List schedules"
echo "----------------------------------------"
curl -s "$FHIR_URL/Schedule" | jq '{schedules: [.entry[].resource | {id: .id, actor: .actor[0].display}]}'

echo -e "\n----------------------------------------"
echo "TEST 7: List free slots"
echo "----------------------------------------"
curl -s "$FHIR_URL/Slot?status=free" | jq '{total: .total, slots: [.entry[].resource | {id: .id, schedule: .schedule.reference, start: .start, status: .status}] | .[0:5]}'

echo -e "\n----------------------------------------"
echo "TEST 8: Create a new patient"
echo "----------------------------------------"
NEW_PATIENT=$(curl -s -X POST "$FHIR_URL/Patient" \
  -H "Content-Type: application/fhir+json" \
  -d '{
    "resourceType": "Patient",
    "name": [{"family": "CurlTest", "given": ["Demo"]}],
    "birthDate": "1990-01-01",
    "telecom": [{"system": "phone", "value": "+6599999999"}]
  }')
echo "$NEW_PATIENT" | jq '{id: .id, name: .name[0].given[0] + " " + .name[0].family}'
NEW_PATIENT_ID=$(echo "$NEW_PATIENT" | jq -r '.id')

echo -e "\n----------------------------------------"
echo "TEST 9: Create an appointment"
echo "----------------------------------------"
APPOINTMENT=$(curl -s -X POST "$FHIR_URL/Appointment" \
  -H "Content-Type: application/fhir+json" \
  -d '{
    "resourceType": "Appointment",
    "status": "booked",
    "slot": [{"reference": "Slot/slot-005"}],
    "start": "2026-05-05T14:15:00+08:00",
    "end": "2026-05-05T14:30:00+08:00",
    "participant": [
      {
        "actor": {"reference": "Patient/patient-001", "display": "Camila Lopez"},
        "status": "accepted"
      }
    ],
    "reasonCode": [{"text": "Follow-up visit"}]
  }')
echo "$APPOINTMENT" | jq '{id: .id, status: .status, start: .start}'

echo -e "\n========================================"
echo "✓ All curl tests completed!"
echo "========================================"
