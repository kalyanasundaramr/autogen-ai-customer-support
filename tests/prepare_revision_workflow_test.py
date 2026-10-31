
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.db import initialize_database
from services.ticket_service import create_ticket, get_ticket
from services.review_service import review_ticket


def main():
    initialize_database()

    complaint = (
        "My order has not arrived, and the estimated "
        "delivery date has already passed."
    )

    record = {
        "category": "Shipping",
        "urgency": "Medium",
        "sentiment": "Negative",
        "language": "English",
        "summary": "Customer reports a delayed order.",
        "escalation_signals": [],
        "evidence_found": True,
        "policy_sources": [
            "shipping_policy.md | Delayed Deliveries"
        ],
        "proposed_response": (
            "Dear Customer, please provide your order ID "
            "so we can check the delivery status."
        ),
        "escalation_decision": "Pending",
        "escalation_reason": None,
        "ticket_status": "Pending",
        "review_status": "Pending",
    }

    ticket_id = create_ticket(complaint, record)

    review_ticket(
        ticket_id=ticket_id,
        action="Revise",
        reviewer="Test Reviewer",
        notes=(
            "Make the response more empathetic, "
            "explain the next steps clearly, and "
            "avoid promising a delivery date."
        ),
    )

    ticket = get_ticket(ticket_id)

    assert ticket["review_status"] == "Revision Requested"

    print("\n========== REVISION WORKFLOW TEST SETUP ==========")
    print("Ticket ID:", ticket_id)
    print("Category:", ticket["category"])
    print("Review Status:", ticket["review_status"])
    print("Ticket Status:", ticket["ticket_status"])
    print("\nTEST TICKET READY")


if __name__ == "__main__":
    main()
