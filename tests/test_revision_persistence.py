
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.db import get_connection
from services.ticket_service import get_ticket
from services.revision_persistence_service import save_revised_response


def main():
    ticket_id = "TKT-000001"

    print("\n========== REVISION PERSISTENCE TEST ==========")

    original = get_ticket(ticket_id)

    assert original is not None, "Ticket not found."
    assert original["review_status"] == "Revision Requested", (
        "Ticket must be awaiting revision."
    )

    previous_response = original["proposed_response"]
    previous_status = original["ticket_status"]

    revised_response = (
        "Dear Customer,\n\n"
        "We sincerely apologize for the delay in delivering "
        "your order. We understand the inconvenience this has "
        "caused. Please share your order ID so our support "
        "team can review the shipment status and advise you "
        "on the next steps.\n\n"
        "Thank you for your patience.\n\n"
        "Customer Support Team"
    )

    result = save_revised_response(
        ticket_id=ticket_id,
        revised_response=revised_response,
        reviewer_notes=(
            "Make the response more empathetic and "
            "explain the next steps clearly."
        ),
    )

    saved = get_ticket(ticket_id)

    assert saved["proposed_response"] == revised_response
    print("PASS: Revised response saved")

    assert saved["review_status"] == "Pending"
    print("PASS: Ticket returned to human review")

    assert saved["ticket_status"] == previous_status
    print("PASS: Original ticket status preserved")

    assert result["previous_response"] == previous_response
    print("PASS: Previous response returned")

    with get_connection() as connection:
        audit = connection.execute(
            """
            SELECT action, previous_value, new_value,
                   performed_by, created_at
            FROM ticket_audit_logs
            WHERE ticket_id = ?
              AND action = 'AI_RESPONSE_REVISED'
            ORDER BY id DESC
            LIMIT 1
            """,
            (ticket_id,),
        ).fetchone()

    assert audit is not None
    assert audit["previous_value"] == previous_response
    assert revised_response in audit["new_value"]
    assert audit["performed_by"] == "AI Resolution Agent"

    print("PASS: Previous draft preserved in audit log")
    print("PASS: Revision audit event recorded")

    print("\nTicket:", ticket_id)
    print("Review status:", saved["review_status"])
    print("Ticket status:", saved["ticket_status"])

    print("\n======================================")
    print("ALL REVISION PERSISTENCE TESTS PASSED")
    print("======================================")


if __name__ == "__main__":
    main()
