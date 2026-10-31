
from datetime import datetime, timezone

from database.db import get_connection
from services.delivery_validation_service import (
    validate_approved_response,
)


class DuplicateDeliveryError(ValueError):
    """Raised when a ticket already has a simulated delivery."""


def save_simulated_delivery(ticket_id: str) -> dict:
    """
    Validate and persist one simulated delivery per ticket.

    No real customer message is sent.
    """

    validated = validate_approved_response(ticket_id)

    # Import here to keep the existing simulation service reusable.
    from services.delivery_service import (
        simulate_customer_response_delivery,
    )

    with get_connection() as connection:
        # Acquire a write lock before checking for duplicates.
        # This protects against concurrent duplicate simulations.
        connection.execute("BEGIN IMMEDIATE")

        existing = connection.execute(
            """
            SELECT delivery_id
            FROM delivery_history
            WHERE ticket_id = ?
              AND delivery_mode = 'simulation'
            LIMIT 1
            """,
            (validated["ticket_id"],),
        ).fetchone()

        if existing:
            raise DuplicateDeliveryError(
                f"Ticket {ticket_id} already has a simulated "
                f"delivery: {existing['delivery_id']}"
            )

        receipt = simulate_customer_response_delivery(ticket_id)

        connection.execute(
            """
            INSERT INTO delivery_history (
                delivery_id,
                ticket_id,
                delivery_mode,
                delivery_status,
                channel,
                response,
                delivered_at,
                actual_message_sent
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                receipt["delivery_id"],
                receipt["ticket_id"],
                receipt["delivery_mode"],
                receipt["delivery_status"],
                receipt["channel"],
                receipt["response"],
                receipt["delivered_at"],
                0,
            ),
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
                "DELIVERY_SIMULATED",
                None,
                receipt["delivery_id"],
                "Delivery Simulation Service",
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        connection.commit()

    return receipt
