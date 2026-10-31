
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.db import initialize_database, get_connection
from services.ticket_service import create_ticket, get_ticket


def build_record(category, urgency, sentiment, evidence_found=True):
    return {
        "category": category,
        "urgency": urgency,
        "sentiment": sentiment,
        "language": "English",
        "summary": "Customer support test complaint.",
        "escalation_signals": [],
        "evidence_found": evidence_found,
        "policy_sources": ["billing_policy.md | Duplicate Charges"]
            if category == "Billing" else [],
        "proposed_response": "Please contact our support team.",
        # Deliberately incorrect AI decision
        "escalation_decision": "Pending",
        "escalation_reason": None,
        "ticket_status": "Pending",
        "review_status": "Pending",
    }


def main():
    initialize_database()

    print("\n========== ESCALATION INTEGRATION TEST ==========")

    # Test 1: High-risk billing complaint
    complaint = (
        "I was charged three times for one order! "
        "If you don't fix it, I will take legal action."
    )

    record = build_record(
        category="Billing",
        urgency="High",
        sentiment="Very Angry",
    )

    ticket_id = create_ticket(complaint, record)
    saved = get_ticket(ticket_id)

    assert saved is not None
    assert saved["escalation_decision"] == "Escalated"
    assert saved["ticket_status"] == "Escalated"
    assert saved["review_status"] == "Pending"
    assert "Legal threat detected" in saved["escalation_reason"]
    assert "Payment or billing dispute" in saved["escalation_reason"]

    print("\n[1] HIGH-RISK COMPLAINT: PASS")
    print("Ticket ID:", ticket_id)
    print("AI suggested:", record["escalation_decision"])
    print("Database decision:", saved["escalation_decision"])
    print("Reason:", saved["escalation_reason"])
    print("Review status:", saved["review_status"])

    # Test 2: Normal password reset
    normal_complaint = (
        "I forgot my password. How can I reset it?"
    )

    normal_record = build_record(
        category="Account",
        urgency="Low",
        sentiment="Neutral",
    )

    normal_id = create_ticket(normal_complaint, normal_record)
    normal_saved = get_ticket(normal_id)

    assert normal_saved is not None
    assert normal_saved["escalation_decision"] == "Pending"
    assert normal_saved["ticket_status"] == "Pending"
    assert normal_saved["review_status"] == "Pending"
    assert normal_saved["escalation_reason"] is None

    print("\n[2] NORMAL COMPLAINT: PASS")
    print("Ticket ID:", normal_id)
    print("Database decision:", normal_saved["escalation_decision"])

    # Test 3: Verify escalation is recorded in audit log
    with get_connection() as connection:
        audit = connection.execute(
            """
            SELECT action, new_value
            FROM ticket_audit_logs
            WHERE ticket_id = ?
            """,
            (ticket_id,),
        ).fetchone()

    assert audit is not None
    assert audit["action"] == "TICKET_CREATED"

    audit_data = json.loads(audit["new_value"])

    assert audit_data["escalation_decision"] == "Escalated"
    assert audit_data["ticket_status"] == "Escalated"

    print("\n[3] ESCALATION AUDIT LOG: PASS")

    print("\n==========================================")
    print("ALL ESCALATION INTEGRATION TESTS PASSED")
    print("==========================================")


if __name__ == "__main__":
    main()
