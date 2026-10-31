
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.db import initialize_database, get_connection
from services.ticket_service import create_ticket, get_ticket


def main():
    print("\n========== SQLITE TICKET TEST ==========")

    # Ensure database tables exist
    initialize_database()

    complaint = (
        "My order is delayed beyond the estimated "
        "delivery date. What should I do?"
    )

    record = {
        "category": "Shipping",
        "urgency": "Medium",
        "sentiment": "Negative",
        "language": "English",
        "summary": "Customer reports delayed delivery.",
        "escalation_signals": [],
        "evidence_found": True,
        "policy_sources": [
            "shipping_policy.md | Delayed Deliveries",
            "shipping_policy.md | Escalation"
        ],
        "proposed_response": (
            "I'm sorry your order is delayed. "
            "Please provide your order ID so our "
            "support team can investigate."
        ),
        "escalation_decision": "Pending",
        "escalation_reason": None,
        "ticket_status": "Pending",
        "review_status": "Pending"
    }

    # Test 1: Create a ticket
    ticket_id = create_ticket(complaint, record)

    print("\n[1] TICKET CREATED")
    print("Ticket ID:", ticket_id)

    assert ticket_id.startswith("TKT-")

    # Test 2: Retrieve the ticket
    saved_ticket = get_ticket(ticket_id)

    assert saved_ticket is not None
    assert saved_ticket["ticket_id"] == ticket_id
    assert saved_ticket["original_complaint"] == complaint
    assert saved_ticket["category"] == "Shipping"
    assert saved_ticket["urgency"] == "Medium"
    assert saved_ticket["evidence_found"] is True
    assert saved_ticket["ticket_status"] == "Pending"
    assert saved_ticket["review_status"] == "Pending"

    print("\n[2] TICKET RETRIEVED")
    print(json.dumps(saved_ticket, indent=2, ensure_ascii=False))

    # Test 3: Verify the audit log
    with get_connection() as connection:
        audit_logs = connection.execute(
            """
            SELECT action, performed_by
            FROM ticket_audit_logs
            WHERE ticket_id = ?
            """,
            (ticket_id,)
        ).fetchall()

    assert len(audit_logs) == 1
    assert audit_logs[0]["action"] == "TICKET_CREATED"
    assert audit_logs[0]["performed_by"] == "system"

    print("\n[3] AUDIT LOG VERIFIED")
    print("Action:", audit_logs[0]["action"])
    print("Performed by:", audit_logs[0]["performed_by"])

    # Test 4: Verify missing-ticket handling
    missing_ticket = get_ticket("TKT-999999999")

    assert missing_ticket is None

    print("\n[4] MISSING TICKET HANDLING: PASS")

    print("\n===================================")
    print("ALL SQLITE TICKET TESTS PASSED")
    print("===================================")


if __name__ == "__main__":
    main()
