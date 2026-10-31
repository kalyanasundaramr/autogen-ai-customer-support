
import sys
from pathlib import Path
from unittest.mock import patch

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.db import get_connection
from services.ticket_lifecycle_service import (
    update_ticket_status,
    TicketLifecycleError,
)


def main():
    print("\n========== LIFECYCLE PERSISTENCE TEST ==========")

    # Create a dedicated test ticket directly in SQLite.
    # The test uses a transaction so existing tickets are untouched.
    test_ticket_id = "TKT-LIFECYCLE-TEST"

    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")

        # Remove only records belonging to this test ticket.
        connection.execute(
            "DELETE FROM ticket_audit_logs WHERE ticket_id = ?",
            (test_ticket_id,),
        )
        connection.execute(
            "DELETE FROM delivery_history WHERE ticket_id = ?",
            (test_ticket_id,),
        )
        connection.execute(
            "DELETE FROM tickets WHERE ticket_id = ?",
            (test_ticket_id,),
        )

        connection.execute(
            """
            INSERT INTO tickets (
                ticket_id,
                original_complaint,
                category,
                urgency,
                sentiment,
                language,
                summary,
                escalation_signals,
                evidence_found,
                policy_sources,
                proposed_response,
                escalation_decision,
                escalation_reason,
                ticket_status,
                review_status,
                created_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            """,
            (
                test_ticket_id,
                "Test lifecycle status changes.",
                "Shipping",
                "Medium",
                "Neutral",
                "English",
                "Lifecycle test",
                "[]",
                1,
                "[]",
                "Test response.",
                "No",
                None,
                "Pending",
                "Approved",
            ),
        )

        connection.commit()

    print("PASS: Dedicated test ticket created")

    # Pending -> Escalated
    result = update_ticket_status(
        ticket_id=test_ticket_id,
        new_status="Escalated",
        performed_by="Test Operator",
        reason="Testing escalation workflow",
    )

    assert result["previous_status"] == "Pending"
    assert result["new_status"] == "Escalated"

    print("PASS: Pending -> Escalated persisted")

    # Escalated -> Resolved
    result = update_ticket_status(
        ticket_id=test_ticket_id,
        new_status="Resolved",
        performed_by="Test Operator",
        reason="Test issue marked resolved",
    )

    assert result["new_status"] == "Resolved"

    print("PASS: Escalated -> Resolved persisted")

    # Resolved -> Closed
    result = update_ticket_status(
        ticket_id=test_ticket_id,
        new_status="Closed",
        performed_by="Test Operator",
        reason="Test ticket closure",
    )

    assert result["new_status"] == "Closed"

    print("PASS: Resolved -> Closed persisted")

    # Verify invalid transition is rejected.
    try:
        update_ticket_status(
            ticket_id=test_ticket_id,
            new_status="Pending",
            performed_by="Test Operator",
            reason="Invalid reopening attempt",
        )
    except TicketLifecycleError:
        print("PASS: Invalid transition blocked")
    else:
        raise AssertionError("Invalid transition was accepted")

    # Verify final database status and audit events.
    with get_connection() as connection:
        ticket = connection.execute(
            """
            SELECT ticket_status
            FROM tickets
            WHERE ticket_id = ?
            """,
            (test_ticket_id,),
        ).fetchone()

        audit_rows = connection.execute(
            """
            SELECT action, previous_value, new_value
            FROM ticket_audit_logs
            WHERE ticket_id = ?
              AND action = 'TICKET_STATUS_CHANGED'
            ORDER BY id
            """,
            (test_ticket_id,),
        ).fetchall()

    assert ticket["ticket_status"] == "Closed"
    assert len(audit_rows) == 3

    assert [row["previous_value"] for row in audit_rows] == [
        "Pending",
        "Escalated",
        "Resolved",
    ]

    print("PASS: Final status verified in SQLite")
    print("PASS: Three lifecycle audit events recorded")

    print("\n========== AUDIT HISTORY ==========")

    for row in audit_rows:
        print(dict(row))

    print("\nALL LIFECYCLE PERSISTENCE TESTS PASSED")


if __name__ == "__main__":
    main()
