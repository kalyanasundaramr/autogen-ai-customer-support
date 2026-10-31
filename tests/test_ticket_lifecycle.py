
import sys
from pathlib import Path
from unittest.mock import patch

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.ticket_lifecycle_service import (
    validate_ticket_transition,
    TicketLifecycleError,
)


def mock_ticket(status, review_status="Approved"):
    return {
        "ticket_id": "TKT-TEST",
        "ticket_status": status,
        "review_status": review_status,
    }


def expect_valid(current, target, review="Approved"):
    with patch(
        "services.ticket_lifecycle_service.get_ticket",
        return_value=mock_ticket(current, review),
    ):
        result = validate_ticket_transition(
            "TKT-TEST", target
        )

        assert result["transition_valid"] is True
        assert result["previous_status"] == current
        assert result["new_status"] == target

        print(f"PASS: {current} -> {target}")


def expect_blocked(current, target, review="Approved"):
    with patch(
        "services.ticket_lifecycle_service.get_ticket",
        return_value=mock_ticket(current, review),
    ):
        try:
            validate_ticket_transition(
                "TKT-TEST", target
            )
        except TicketLifecycleError:
            print(f"PASS: Blocked {current} -> {target}")
        else:
            raise AssertionError(
                f"Invalid transition accepted: {current} -> {target}"
            )


def main():
    print("\n========== TICKET LIFECYCLE TESTS ==========")

    # Valid transitions
    expect_valid("Pending", "Escalated")
    expect_valid("Pending", "Resolved")
    expect_valid("Escalated", "Resolved")
    expect_valid("Resolved", "Closed")
    expect_valid("Resolved", "Escalated")

    # Invalid transitions
    expect_blocked("Pending", "Closed")
    expect_blocked("Closed", "Pending")
    expect_blocked("Closed", "Resolved")
    expect_blocked("Escalated", "Closed")
    expect_blocked("Pending", "Pending")

    # Human approval checks
    expect_blocked("Pending", "Resolved", "Pending")
    expect_blocked("Escalated", "Resolved", "Rejected")
    expect_blocked("Resolved", "Closed", "Revision Requested")

    # Missing ticket
    with patch(
        "services.ticket_lifecycle_service.get_ticket",
        return_value=None,
    ):
        try:
            validate_ticket_transition(
                "TKT-999999", "Resolved"
            )
        except TicketLifecycleError:
            print("PASS: Missing ticket blocked")
        else:
            raise AssertionError("Missing ticket accepted")

    # Real database ticket: validation only
    result = validate_ticket_transition(
        "TKT-000010", "Resolved"
    )

    assert result["transition_valid"] is True
    print("PASS: Approved real ticket eligible for resolution")

    print("\nALL TICKET LIFECYCLE TESTS PASSED")


if __name__ == "__main__":
    main()
