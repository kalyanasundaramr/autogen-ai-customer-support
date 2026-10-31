
from database.db import get_connection


def list_ticket_audit_history(ticket_id: str) -> list[dict]:
    """
    Retrieve the complete audit history for a ticket.

    Newest events appear first.
    This operation is read-only.
    """
    if not ticket_id or not ticket_id.strip():
        raise ValueError("Ticket ID is required.")

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                ticket_id,
                action,
                previous_value,
                new_value,
                performed_by,
                created_at
            FROM ticket_audit_logs
            WHERE ticket_id = ?
            ORDER BY id DESC
            """,
            (ticket_id.strip(),),
        ).fetchall()

        return [dict(row) for row in rows]
