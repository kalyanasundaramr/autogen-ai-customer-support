from datetime import datetime, timezone
from database.db import get_connection
from services.ticket_service import get_ticket


class TicketLifecycleError(ValueError):
    """Raised when a ticket lifecycle transition is invalid."""


ALLOWED_TRANSITIONS = {
    "Pending": {"Escalated", "Resolved"},
    "Escalated": {"Resolved"},
    "Resolved": {"Closed", "Escalated"},
    "Closed": set(),
}


def validate_ticket_transition(
    ticket_id: str,
    new_status: str,
) -> dict:
    """
    Validate a ticket status transition.

    This function does not modify the database.
    """

    if not ticket_id or not ticket_id.strip():
        raise TicketLifecycleError(
            "Ticket ID is required."
        )

    ticket = get_ticket(ticket_id.strip())

    if ticket is None:
        raise TicketLifecycleError(
            f"Ticket {ticket_id} was not found."
        )

    current_status = ticket["ticket_status"]

    if new_status not in ALLOWED_TRANSITIONS.get(
        current_status, set()
    ):
        raise TicketLifecycleError(
            f"Invalid transition: "
            f"{current_status} -> {new_status}"
        )

    if new_status in {"Resolved", "Closed"}:
        if ticket["review_status"] != "Approved":
            raise TicketLifecycleError(
                "Human approval is required before "
                "resolving or closing a ticket."
            )

    return {
        "ticket_id": ticket["ticket_id"],
        "previous_status": current_status,
        "new_status": new_status,
        "transition_valid": True,
    }

def update_ticket_status(
    ticket_id: str,
    new_status: str,
    performed_by: str,
    reason: str,
) -> dict:
    """
    Update a ticket lifecycle status and create an audit entry.

    The transition is revalidated inside the SQLite transaction.
    """

    if not performed_by or not performed_by.strip():
        raise TicketLifecycleError(
            "Performed by is required."
        )

    if not reason or not reason.strip():
        raise TicketLifecycleError(
            "A reason is required for status changes."
        )

    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")

        row = connection.execute(
            """
            SELECT ticket_id, ticket_status, review_status
            FROM tickets
            WHERE ticket_id = ?
            """,
            (ticket_id,),
        ).fetchone()

        if row is None:
            raise TicketLifecycleError(
                f"Ticket {ticket_id} was not found."
            )

        previous_status = row["ticket_status"]

        allowed = ALLOWED_TRANSITIONS.get(
            previous_status, set()
        )

        if new_status not in allowed:
            raise TicketLifecycleError(
                f"Invalid transition: "
                f"{previous_status} -> {new_status}"
            )

        if new_status in {"Resolved", "Closed"}:
            if row["review_status"] != "Approved":
                raise TicketLifecycleError(
                    "Human approval is required."
                )

        now = datetime.now(timezone.utc).isoformat()

        connection.execute(
            """
            UPDATE tickets
            SET ticket_status = ?,
                updated_at = ?
            WHERE ticket_id = ?
            """,
            (new_status, now, ticket_id),
        )

        connection.execute(
            """
            INSERT INTO ticket_audit_logs (
                ticket_id,
                action,
                previous_value,
                new_value,
                performed_by,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                "TICKET_STATUS_CHANGED",
                previous_status,
                f"{new_status} | Reason: {reason.strip()}",
                performed_by.strip(),
                now,
            ),
        )

    connection.commit()

    # Synchronize the CSV after the SQLite transaction
    # has completed successfully.
    from services.ticket_csv_service import sync_tickets_csv
    sync_tickets_csv()

    return {
        "ticket_id": ticket_id,
        "previous_status": previous_status,
        "new_status": new_status,
        "performed_by": performed_by.strip(),
        "reason": reason.strip(),
        "updated_at": now,
    }
