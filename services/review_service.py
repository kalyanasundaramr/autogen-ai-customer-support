
from datetime import datetime, timezone
from database.db import get_connection


ALLOWED_ACTIONS = {
    "Approve": "Approved",
    "Revise": "Revision Requested",
    "Reject": "Rejected",
}


def review_ticket(
    ticket_id: str,
    action: str,
    reviewer: str,
    notes: str = "",
) -> dict:
    """
    Record a human review decision.

    Approval applies to the response draft only,
    not to resolution of the customer complaint.
    """

    if action not in ALLOWED_ACTIONS:
        raise ValueError("Invalid review action.")

    if not reviewer or not reviewer.strip():
        raise ValueError("Reviewer is required.")

    if action in ("Revise", "Reject") and not notes.strip():
        raise ValueError(
            "Reviewer notes are required for revision or rejection."
        )

    new_review_status = ALLOWED_ACTIONS[action]
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        ticket = connection.execute(
            """
            SELECT ticket_id, ticket_status, review_status
            FROM tickets
            WHERE ticket_id = ?
            """,
            (ticket_id,),
        ).fetchone()

        if ticket is None:
            raise ValueError("Ticket not found.")

        if ticket["review_status"] != "Pending":
            raise ValueError(
                "Only tickets pending review can be reviewed."
            )

        connection.execute(
            """
            UPDATE tickets
            SET review_status = ?,
                updated_at = ?
            WHERE ticket_id = ?
            """,
            (
                new_review_status,
                now,
                ticket_id,
            ),
        )

        connection.execute(
            """
            INSERT INTO ticket_audit_logs (
                ticket_id,
                action,
                previous_value,
                new_value,
                performed_by
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                f"REVIEW_{action.upper()}",
                ticket["review_status"],
                new_review_status + (
                    f" | Notes: {notes.strip()}"
                    if notes.strip() else ""
                ),
                reviewer.strip(),
            ),
        )

    return {
        "ticket_id": ticket_id,
        "review_status": new_review_status,
        "ticket_status": ticket["ticket_status"],
        "reviewer": reviewer.strip(),
        "notes": notes.strip(),
        "reviewed_at": now,
    }
