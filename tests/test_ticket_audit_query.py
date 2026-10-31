
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.ticket_audit_query_service import (
    list_ticket_audit_history,
)


def main():
    print("\n========== TICKET AUDIT QUERY TEST ==========")

    ticket_id = "TKT-LIFECYCLE-TEST"

    # Test 1: Retrieve audit history
    history = list_ticket_audit_history(ticket_id)

    assert isinstance(history, list)
    assert len(history) >= 3

    print("PASS: Audit history retrieved")
    print("Total audit events:", len(history))

    # Test 2: Verify required fields
    required_fields = {
        "id",
        "ticket_id",
        "action",
        "previous_value",
        "new_value",
        "performed_by",
        "created_at",
    }

    for event in history:
        assert required_fields.issubset(event.keys())
        assert event["ticket_id"] == ticket_id

    print("PASS: Audit event structure validated")

    # Test 3: Verify lifecycle events
    lifecycle_events = [
        event for event in history
        if event["action"] == "TICKET_STATUS_CHANGED"
    ]

    assert len(lifecycle_events) >= 3

    print("PASS: Lifecycle audit events found")

    # Test 4: Verify newest-first ordering
    ids = [event["id"] for event in history]

    assert ids == sorted(ids, reverse=True)

    print("PASS: Audit history ordered newest first")

    # Test 5: Verify unknown ticket
    unknown = list_ticket_audit_history("TKT-999999")

    assert unknown == []

    print("PASS: Unknown ticket returns empty history")

    # Test 6: Verify empty ticket ID validation
    try:
        list_ticket_audit_history("")
    except ValueError:
        print("PASS: Empty ticket ID rejected")
    else:
        raise AssertionError("Empty ticket ID was accepted")

    print("\n========== AUDIT EVENTS ==========")

    for event in history:
        print(
            f"{event['created_at']} | "
            f"{event['action']} | "
            f"{event['previous_value']} -> "
            f"{event['new_value']} | "
            f"By: {event['performed_by']}"
        )

    print("\nALL TICKET AUDIT QUERY TESTS PASSED")


if __name__ == "__main__":
    main()
