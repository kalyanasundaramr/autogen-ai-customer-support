
from services.ticket_service import get_ticket


class DeliveryValidationError(ValueError):
    """Raised when a ticket is not eligible for delivery."""


def validate_approved_response(ticket_id: str) -> dict:
    """
    Validate that a customer support response is
    eligible for delivery.

    This function does not send messages or
    modify the database.
    """

    if not ticket_id or not ticket_id.strip():
        raise DeliveryValidationError(
            "A valid ticket ID is required."
        )

    ticket = get_ticket(ticket_id.strip())

    if ticket is None:
        raise DeliveryValidationError(
            f"Ticket {ticket_id} was not found."
        )

    if ticket["review_status"] != "Approved":
        raise DeliveryValidationError(
            "Delivery blocked: human approval is required."
        )

    response = ticket.get("proposed_response")

    if not isinstance(response, str) or not response.strip():
        raise DeliveryValidationError(
            "Delivery blocked: customer response is empty."
        )

    # Prevent common unresolved AI-generated placeholders.
    placeholders = (
        "[Your Name]",
        "[Your Position]",
        "[Customer Name]",
        "[Insert",
    )

    if any(
        placeholder.lower() in response.lower()
        for placeholder in placeholders
    ):
        raise DeliveryValidationError(
            "Delivery blocked: unresolved response placeholders."
        )

    if ticket["ticket_status"] not in (
        "Pending",
        "Escalated",
    ):
        raise DeliveryValidationError(
            "Delivery blocked: unsupported ticket status."
        )

    return {
        "ticket_id": ticket["ticket_id"],
        "response": response.strip(),
        "review_status": ticket["review_status"],
        "ticket_status": ticket["ticket_status"],
        "delivery_eligible": True,
        "delivery_mode": "simulation",
    }
