#!/usr/bin/env python3
"""Test MCP tools directly (without MCP protocol).

This bypasses MCP and calls the tool functions directly to verify
FHIR integration is working.

Usage:
    uv run python scripts/test_tools.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Set environment
os.environ.setdefault("FHIR_BASE_URL", "http://localhost:8080/fhir")
os.environ.setdefault("TIMEZONE", "Asia/Singapore")

import json

# Import tool functions (they're registered but we can call directly)
from mcp_server.fhir import get_fhir_client


def pp(title: str, data: dict):
    """Pretty print with title."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)
    print(json.dumps(data, indent=2))


def test_search_patients():
    """Test patient search."""
    from mcp_server.tools.patients import register_patient_tools
    from mcp.server.fastmcp import FastMCP
    
    mcp = FastMCP("test")
    register_patient_tools(mcp)
    
    # Get the tool function
    search_fn = None
    for tool in mcp._tool_manager._tools.values():
        if tool.name == "search_patients":
            search_fn = tool.fn
            break
    
    # Test 1: Find existing patient
    result = search_fn(name="Camila Lopez", birth_date="1985-03-15")
    pp("TEST 1: Search existing patient (Camila Lopez)", result)
    assert result.get("found") == True, "Should find Camila Lopez"
    
    # Test 2: Non-existent patient
    result = search_fn(name="John Nobody", birth_date="2000-01-01")
    pp("TEST 2: Search non-existent patient", result)
    assert result.get("found") == False, "Should not find John Nobody"
    
    return True


def test_create_patient():
    """Test patient creation."""
    from mcp_server.tools.patients import register_patient_tools
    from mcp.server.fastmcp import FastMCP
    
    mcp = FastMCP("test")
    register_patient_tools(mcp)
    
    create_fn = None
    for tool in mcp._tool_manager._tools.values():
        if tool.name == "create_patient":
            create_fn = tool.fn
            break
    
    result = create_fn(
        name="Test Patient",
        birth_date="1995-06-15",
        phone="+6598765432"
    )
    pp("TEST 3: Create new patient", result)
    assert result.get("success") == True, "Should create patient"
    
    return True


def test_list_practitioners():
    """Test practitioner listing by specialty."""
    from mcp_server.tools.practitioners import register_practitioner_tools
    from mcp.server.fastmcp import FastMCP
    
    mcp = FastMCP("test")
    register_practitioner_tools(mcp)
    
    list_fn = None
    for tool in mcp._tool_manager._tools.values():
        if tool.name == "list_practitioners_by_specialty":
            list_fn = tool.fn
            break
    
    # Test general medicine
    result = list_fn(specialty="general-medicine")
    pp("TEST 4: List practitioners (general-medicine)", result)
    
    # Test cardiology
    result = list_fn(specialty="cardiology")
    pp("TEST 5: List practitioners (cardiology)", result)
    
    # Test invalid specialty
    result = list_fn(specialty="invalid-specialty")
    pp("TEST 6: List practitioners (invalid)", result)
    assert "error" in result, "Should return error for invalid specialty"
    
    return True


def test_get_slots():
    """Test slot retrieval."""
    from mcp_server.tools.slots import register_slot_tools
    from mcp.server.fastmcp import FastMCP
    
    mcp = FastMCP("test")
    register_slot_tools(mcp)
    
    get_fn = None
    for tool in mcp._tool_manager._tools.values():
        if tool.name == "get_available_slots":
            get_fn = tool.fn
            break
    
    # May 5, 2026 09:00:00 SGT = Unix timestamp
    # Using a timestamp that falls on May 5, 2026 in SGT
    may_5_timestamp = 1746374400  # Approximate
    
    result = get_fn(practitioner_id="practitioner-001", date_timestamp=may_5_timestamp)
    pp("TEST 7: Get available slots (Dr. Tan, May 5)", result)
    
    return True


def test_create_appointment():
    """Test appointment creation."""
    from mcp_server.tools.appointments import register_appointment_tools
    from mcp.server.fastmcp import FastMCP
    
    mcp = FastMCP("test")
    register_appointment_tools(mcp)
    
    create_fn = None
    for tool in mcp._tool_manager._tools.values():
        if tool.name == "create_appointment":
            create_fn = tool.fn
            break
    
    result = create_fn(
        patient_id="patient-001",
        slot_id="slot-003",
        reason="Annual checkup"
    )
    pp("TEST 8: Create appointment", result)
    
    # Try to book same slot again (should fail)
    result = create_fn(
        patient_id="patient-002",
        slot_id="slot-003",
        reason="Follow-up"
    )
    pp("TEST 9: Book same slot again (should fail)", result)
    assert result.get("success") == False, "Should fail - slot already booked"
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  Hospital FHIR MCP - Tool Tests")
    print("=" * 60)
    
    # Check FHIR server is running
    client = get_fhir_client()
    try:
        import httpx
        response = httpx.get(f"{client.base_url}/metadata", timeout=5.0)
        if response.status_code != 200:
            print("\n✗ FHIR server is not running!")
            print("  Start it with: make fhir-up && make load-data")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Cannot connect to FHIR server: {e}")
        print("  Start it with: make fhir-up && make load-data")
        sys.exit(1)
    
    print("\n✓ FHIR server is running")
    
    tests = [
        ("Patient Search", test_search_patients),
        ("Patient Create", test_create_patient),
        ("Practitioner List", test_list_practitioners),
        ("Slot Retrieval", test_get_slots),
        ("Appointment Create", test_create_appointment),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"\n✗ {name} FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        sys.exit(1)
    
    print("\n✓ All tests passed!")


if __name__ == "__main__":
    main()
