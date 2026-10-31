
from datetime import datetime, timezone
from uuid import uuid4

from services.delivery_validation_service import (
    validate_approved_response,
)


def simulate_customer_response_delivery(ticket_id: str) -> dict:
    """
    Simulate delivery of a human-approved customer response.

    This function:
    - Validates the approved response
    - Generates a simulated delivery ID
    - Returns a delivery receipt

    It does NOT:
    - Send an actual message
    - Modify ticket status
    - Write to the database
    """

    validated = validate_approved_response(ticket_id)

    delivery_id = f"SIM-{uuid4().hex[:12].upper()}"

    delivered_at = datetime.now(timezone.utc).isoformat()

    response = validated["response"]

    receipt = {
        "delivery_id": delivery_id,
        "ticket_id": validated["ticket_id"],
        "delivery_mode": "simulation",
        "delivery_status": "Simulated",
        "channel": "Customer Support",
        "response": response,
        "delivered_at": delivered_at,
        "actual_message_sent": False,
    }

    return receipt
