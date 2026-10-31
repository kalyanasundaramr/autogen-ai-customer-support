
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.delivery_query_service import (
    list_delivery_history,
)


def main():
    print("\n========== DELIVERY HISTORY QUERY TEST ==========")

    ticket_id = "TKT-000010"

    # Test 1: Retrieve all delivery records
    all_deliveries = list_delivery_history()

    assert isinstance(all_deliveries, list)
    assert len(all_deliveries) >= 1

    print("PASS: All delivery records retrieved")
    print("Total delivery records:", len(all_deliveries))

    # Test 2: Retrieve delivery history for a ticket
    deliveries = list_delivery_history(ticket_id)

    assert len(deliveries) == 1
    assert deliveries[0]["ticket_id"] == ticket_id

    print("PASS: Ticket-specific delivery history retrieved")

    # Test 3: Verify the stored receipt
    receipt = deliveries[0]

    assert receipt["delivery_id"] == "SIM-1C789598EC6D"
    assert receipt["delivery_mode"] == "simulation"
    assert receipt["delivery_status"] == "Simulated"
    assert receipt["actual_message_sent"] is False

    print("PASS: Saved simulated delivery verified")

    # Test 4: Verify unknown tickets
    unknown = list_delivery_history("TKT-999999")

    assert unknown == []

    print("PASS: Unknown ticket returns empty history")

    # Test 5: Verify empty ticket ID validation
    try:
        list_delivery_history("")
    except ValueError:
        print("PASS: Empty ticket ID blocked")
    else:
        raise AssertionError("Empty ticket ID was accepted")

    print("\n========== DELIVERY HISTORY ==========")

    for delivery in deliveries:
        print("Delivery ID:", delivery["delivery_id"])
        print("Ticket ID:", delivery["ticket_id"])
        print("Mode:", delivery["delivery_mode"])
        print("Status:", delivery["delivery_status"])
        print("Channel:", delivery["channel"])
        print("Timestamp:", delivery["delivered_at"])
        print("Actual Message Sent:", delivery["actual_message_sent"])

    print("\nALL DELIVERY HISTORY QUERY TESTS PASSED")


if __name__ == "__main__":
    main()
