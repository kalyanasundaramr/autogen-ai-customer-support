
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.db import initialize_database, get_connection
from services.ticket_service import create_ticket, get_ticket
from services.review_service import review_ticket


def create_test_ticket():
    """Create a fresh ticket for each review scenario."""

    complaint = "My order arrived damaged."

    record = {
        "category": "Product",
        "urgency": "Medium",
        "sentiment": "Negative",
        "language": "English",
        "summary": "Customer received a damaged product.",
        "escalation_signals": [],
        "evidence_found": True,
        "policy_sources": [
            "product_faq.md | Damaged Products"
        ],
        "proposed_response": (
            "Please provide your order ID and "
            "photos of the damaged product."
        ),
        "escalation_decision": "Pending",
        "escalation_reason": None,
        "ticket_status": "Pending",
        "review_status": "Pending",
    }

    return create_ticket(complaint, record)


def main():
    initialize_database()

    print("\n========== HUMAN REVIEW TESTS ==========")

    # Test 1: Approve a response draft
    ticket_id = create_test_ticket()

    result = review_ticket(
        ticket_id=ticket_id,
        action="Approve",
        reviewer="Test Reviewer",
        notes="Response is accurate and policy-grounded.",
    )

    saved = get_ticket(ticket_id)

    assert result["review_status"] == "Approved"
    assert saved["review_status"] == "Approved"
    assert saved["ticket_status"] == "Pending"

    print("\n[1] APPROVAL: PASS")
    print("Ticket:", ticket_id)
    print("Review status:", saved["review_status"])
    print("Ticket status:", saved["ticket_status"])

    # Test 2: Request a revision
    revision_id = create_test_ticket()

    review_ticket(
        ticket_id=revision_id,
        action="Revise",
        reviewer="Test Reviewer",
        notes="Add more details about the return policy.",
    )

    revised = get_ticket(revision_id)

    assert revised["review_status"] == "Revision Requested"
    assert revised["ticket_status"] == "Pending"

    print("\n[2] REVISION REQUEST: PASS")
    print("Ticket:", revision_id)
    print("Review status:", revised["review_status"])

    # Test 3: Reject a response draft
    rejection_id = create_test_ticket()

    review_ticket(
        ticket_id=rejection_id,
        action="Reject",
        reviewer="Test Reviewer",
        notes="Response does not adequately address the complaint.",
    )

    rejected = get_ticket(rejection_id)

    assert rejected["review_status"] == "Rejected"
    assert rejected["ticket_status"] == "Pending"

    print("\n[3] REJECTION: PASS")
    print("Ticket:", rejection_id)
    print("Review status:", rejected["review_status"])

    # Test 4: Prevent duplicate review
    try:
        review_ticket(
            ticket_id=ticket_id,
            action="Approve",
            reviewer="Test Reviewer",
        )
    except ValueError:
        print("\n[4] DUPLICATE REVIEW PREVENTION: PASS")
    else:
        raise AssertionError(
            "An already reviewed ticket was reviewed again."
        )

    # Test 5: Verify audit logging
    with get_connection() as connection:
        logs = connection.execute(
            """
            SELECT action, performed_by
            FROM ticket_audit_logs
            WHERE ticket_id = ?
            ORDER BY id
            """,
            (ticket_id,),
        ).fetchall()

    actions = [row["action"] for row in logs]

    assert "TICKET_CREATED" in actions
    assert "REVIEW_APPROVE" in actions
    assert any(
        row["performed_by"] == "Test Reviewer"
        for row in logs
    )

    print("\n[5] REVIEW AUDIT LOGGING: PASS")

    # Test 6: Revision requires notes
    no_notes_id = create_test_ticket()

    try:
        review_ticket(
            ticket_id=no_notes_id,
            action="Revise",
            reviewer="Test Reviewer",
            notes="",
        )
    except ValueError:
        print("\n[6] REVISION NOTES VALIDATION: PASS")
    else:
        raise AssertionError(
            "Revision without notes was accepted."
        )

    print("\n=======================================")
    print("ALL HUMAN REVIEW TESTS PASSED")
    print("=======================================")


if __name__ == "__main__":
    main()
