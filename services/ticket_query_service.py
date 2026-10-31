
from database.db import get_connection
from services.ticket_service import get_ticket


def list_pending_review_tickets() -> list[dict]:
    """
    Retrieve tickets waiting for human review.
    Most recently created tickets appear first.
    """

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT ticket_id
            FROM tickets
            WHERE review_status = 'Pending'
            ORDER BY id DESC
            """
        ).fetchall()

    tickets = []

    for row in rows:
        ticket = get_ticket(row["ticket_id"])

        if ticket is not None:
            tickets.append(ticket)

    return tickets

def list_revision_requested_tickets() -> list[dict]:
    """
    Retrieve tickets awaiting AI-assisted revision.
    Newest tickets appear first.
    """

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT ticket_id
            FROM tickets
            WHERE review_status = 'Revision Requested'
            ORDER BY id DESC
            """
        ).fetchall()

    tickets = []

    for row in rows:
        ticket = get_ticket(row["ticket_id"])

        if ticket is not None:
            tickets.append(ticket)

    return tickets

def list_all_tickets() -> list[dict]:
    """
    Retrieve all customer support tickets,
    including Pending, Escalated, Resolved,
    and Closed tickets.

    Newest tickets appear first.
    """

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT ticket_id
            FROM tickets
            ORDER BY id DESC
            """
        ).fetchall()

    tickets = []

    for row in rows:
        ticket = get_ticket(row["ticket_id"])

        if ticket is not None:
            tickets.append(ticket)

    return tickets
