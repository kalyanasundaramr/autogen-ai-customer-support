
from database.db import get_connection


def list_delivery_history(
    ticket_id: str | None = None,
) -> list[dict]:
    """
    Retrieve saved delivery records.

    If ticket_id is provided, return records
    for that ticket only.

    This function is read-only.
    """

    query = """
        SELECT
            delivery_id,
            ticket_id,
            delivery_mode,
            delivery_status,
            channel,
            response,
            delivered_at,
            actual_message_sent,
            created_at
        FROM delivery_history
    """

    parameters = ()

    if ticket_id is not None:
        if not ticket_id.strip():
            raise ValueError("Ticket ID cannot be empty.")

        query += " WHERE ticket_id = ?"
        parameters = (ticket_id.strip(),)

    query += " ORDER BY id DESC"

    with get_connection() as connection:
        rows = connection.execute(
            query,
            parameters,
        ).fetchall()

    return [
        {
            **dict(row),
            "actual_message_sent": bool(
                row["actual_message_sent"]
            ),
        }
        for row in rows
    ]
