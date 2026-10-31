
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.delivery_service import (
    simulate_customer_response_delivery,
)
from services.ticket_service import get_ticket
from services.delivery_validation_service import (
    DeliveryValidationError,
)


def main():
    ticket_id = "TKT-000010"

    print("\n========== SIMULATED DELIVERY TEST ==========")

    # Capture ticket state before simulation
    before = get_ticket(ticket_id)

    assert before is not None
    assert before["review_status"] == "Approved"

    # Execute simulated delivery
    receipt = simulate_customer_response_delivery(ticket_id)

    assert receipt["ticket_id"] == ticket_id
    print("PASS: Correct ticket selected")

    assert receipt["delivery_id"].startswith("SIM-")
    print("PASS: Simulated delivery ID generated")

    assert receipt["delivery_mode"] == "simulation"
    assert receipt["delivery_status"] == "Simulated"
    print("PASS: Simulation status recorded in receipt")

    assert receipt["actual_message_sent"] is False
    print("PASS: No actual message sent")

    assert receipt["response"] == before["proposed_response"].strip()
    print("PASS: Approved response used")

    datetime.fromisoformat(receipt["delivered_at"])
    print("PASS: Delivery timestamp generated")

    # Verify database ticket remains unchanged
    after = get_ticket(ticket_id)

    assert after == before
    print("PASS: Ticket database unchanged")

    # Verify missing tickets are blocked
    try:
        simulate_customer_response_delivery("TKT-999999")
    except DeliveryValidationError:
        print("PASS: Invalid ticket blocked")
    else:
        raise AssertionError("Invalid ticket was accepted")

    print("\n========== DELIVERY RECEIPT ==========")

    print("Delivery ID:", receipt["delivery_id"])
    print("Ticket ID:", receipt["ticket_id"])
    print("Mode:", receipt["delivery_mode"])
    print("Status:", receipt["delivery_status"])
    print("Channel:", receipt["channel"])
    print("Timestamp:", receipt["delivered_at"])
    print("Actual Message Sent:", receipt["actual_message_sent"])

    print("\n========== CUSTOMER RESPONSE ==========")
    print(receipt["response"])

    print("\n======================================")
    print("ALL SIMULATED DELIVERY TESTS PASSED")
    print("======================================")


if __name__ == "__main__":
    main()
