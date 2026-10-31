
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.db import get_connection
from services.ticket_service import get_ticket
from services.delivery_persistence_service import (
    save_simulated_delivery,
    DuplicateDeliveryError,
)


def main():
    ticket_id = "TKT-000010"

    print("\n========== DELIVERY PERSISTENCE TEST ==========")

    before = get_ticket(ticket_id)

    assert before is not None
    assert before["review_status"] == "Approved"

    # Check whether this test was already run.
    with get_connection() as connection:
        existing = connection.execute(
            """
            SELECT delivery_id
            FROM delivery_history
            WHERE ticket_id = ?
              AND delivery_mode = 'simulation'
            LIMIT 1
            """,
            (ticket_id,),
        ).fetchone()

    if existing:
        print(
            "Existing simulated delivery:",
            existing["delivery_id"],
        )
        print("Skipping first delivery creation.")
    else:
        receipt = save_simulated_delivery(ticket_id)

        assert receipt["ticket_id"] == ticket_id
        assert receipt["delivery_status"] == "Simulated"
        assert receipt["actual_message_sent"] is False

        print("PASS: Simulated delivery created")
        print("Delivery ID:", receipt["delivery_id"])

    # Verify the persisted receipt.
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM delivery_history
            WHERE ticket_id = ?
              AND delivery_mode = 'simulation'
            """,
            (ticket_id,),
        ).fetchall()

        audit = connection.execute(
            """
            SELECT action, new_value, performed_by
            FROM ticket_audit_logs
            WHERE ticket_id = ?
              AND action = 'DELIVERY_SIMULATED'
            ORDER BY id DESC
            LIMIT 1
            """,
            (ticket_id,),
        ).fetchone()

    assert len(rows) == 1
    print("PASS: Exactly one simulated delivery stored")

    stored = dict(rows[0])

    assert stored["delivery_status"] == "Simulated"
    assert stored["actual_message_sent"] == 0
    assert stored["response"] == before["proposed_response"].strip()

    print("PASS: Stored delivery details verified")

    assert audit is not None
    assert audit["new_value"] == stored["delivery_id"]
    assert audit["performed_by"] == "Delivery Simulation Service"

    print("PASS: Delivery audit event recorded")

    # Attempt a duplicate delivery.
    try:
        save_simulated_delivery(ticket_id)
    except DuplicateDeliveryError:
        print("PASS: Duplicate simulated delivery blocked")
    else:
        raise AssertionError("Duplicate delivery was accepted")

    # Confirm the duplicate attempt did not insert another row.
    with get_connection() as connection:
        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM delivery_history
            WHERE ticket_id = ?
              AND delivery_mode = 'simulation'
            """,
            (ticket_id,),
        ).fetchone()[0]

    assert count == 1
    print("PASS: No duplicate delivery record created")

    after = get_ticket(ticket_id)

    assert after == before
    print("PASS: Ticket record remains unchanged")

    print("\n========== SAVED DELIVERY RECEIPT ==========")
    print("Delivery ID:", stored["delivery_id"])
    print("Ticket ID:", stored["ticket_id"])
    print("Status:", stored["delivery_status"])
    print("Channel:", stored["channel"])
    print("Actual Message Sent:", bool(stored["actual_message_sent"]))

    print("\nALL DELIVERY PERSISTENCE TESTS PASSED")


if __name__ == "__main__":
    main()
