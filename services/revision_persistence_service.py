
from datetime import datetime, timezone

from database.db import get_connection


def save_revised_response(
    ticket_id: str,
    revised_response: str,
    reviewer_notes: str,
    performed_by: str = "AI Resolution Agent",
) -> dict:
    """
    Save a revised AI response and return the ticket
    to Pending human review.

    Preserve the previous draft in the audit log.
    """

    if not isinstance(revised_response, str) or not revised_response.strip():
        raise ValueError("Revised response cannot be empty.")

    if not isinstance(reviewer_notes, str) or not reviewer_notes.strip():
        raise ValueError("Reviewer notes are required.")

    if not isinstance(performed_by, str) or not performed_by.strip():
        raise ValueError("Performed by is required.")

    revised_response = revised_response.strip()
    reviewer_notes = reviewer_notes.strip()
    performed_by = performed_by.strip()

    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        ticket = connection.execute(
            """
            SELECT proposed_response, review_status, ticket_status
            FROM tickets
            WHERE ticket_id = ?
            """,
            (ticket_id,),
        ).fetchone()

        if ticket is None:
            raise ValueError("Ticket not found.")

        if ticket["review_status"] != "Revision Requested":
            raise ValueError(
                "Ticket must have Revision Requested status."
            )

        previous_response = ticket["proposed_response"]

        connection.execute(
            """
            UPDATE tickets
            SET proposed_response = ?,
                review_status = 'Pending',
                updated_at = ?
            WHERE ticket_id = ?
            """,
            (revised_response, now, ticket_id),
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
                "AI_RESPONSE_REVISED",
                previous_response,
                (
                    f"Revised response:\n{revised_response}\n\n"
                    f"Reviewer feedback:\n{reviewer_notes}"
                ),
                performed_by,
            ),
        )

    return {
        "ticket_id": ticket_id,
        "review_status": "Pending",
        "ticket_status": ticket["ticket_status"],
        "previous_response": previous_response,
        "revised_response": revised_response,
        "saved_at": now,
    }
