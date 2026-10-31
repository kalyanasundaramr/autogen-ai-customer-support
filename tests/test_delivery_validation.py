
import sys
from pathlib import Path
from unittest.mock import patch

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.delivery_validation_service import (
    validate_approved_response,
    DeliveryValidationError,
)


def test_approved_ticket():
    result = validate_approved_response("TKT-000010")

    assert result["delivery_eligible"] is True
    assert result["review_status"] == "Approved"
    assert result["delivery_mode"] == "simulation"
    assert result["response"].strip()

    print("PASS: Approved ticket is eligible for delivery")


def test_missing_ticket():
    try:
        validate_approved_response("TKT-999999")
        raise AssertionError("Missing ticket was accepted")
    except DeliveryValidationError:
        print("PASS: Missing ticket blocked")


def test_unapproved_ticket():
    ticket = {
        "ticket_id": "TKT-TEST",
        "review_status": "Pending",
        "ticket_status": "Pending",
        "proposed_response": "Thank you for contacting support.",
    }

    with patch(
        "services.delivery_validation_service.get_ticket",
        return_value=ticket,
    ):
        try:
            validate_approved_response("TKT-TEST")
            raise AssertionError("Unapproved ticket was accepted")
        except DeliveryValidationError:
            print("PASS: Unapproved ticket blocked")


def test_empty_response():
    ticket = {
        "ticket_id": "TKT-TEST",
        "review_status": "Approved",
        "ticket_status": "Pending",
        "proposed_response": "   ",
    }

    with patch(
        "services.delivery_validation_service.get_ticket",
        return_value=ticket,
    ):
        try:
            validate_approved_response("TKT-TEST")
            raise AssertionError("Empty response was accepted")
        except DeliveryValidationError:
            print("PASS: Empty response blocked")


def test_unresolved_placeholders():
    ticket = {
        "ticket_id": "TKT-TEST",
        "review_status": "Approved",
        "ticket_status": "Pending",
        "proposed_response": (
            "Dear Customer, thank you. "
            "Regards, [Your Name]"
        ),
    }

    with patch(
        "services.delivery_validation_service.get_ticket",
        return_value=ticket,
    ):
        try:
            validate_approved_response("TKT-TEST")
            raise AssertionError("Placeholder was accepted")
        except DeliveryValidationError:
            print("PASS: Unresolved placeholder blocked")


def test_unsupported_status():
    ticket = {
        "ticket_id": "TKT-TEST",
        "review_status": "Approved",
        "ticket_status": "Closed",
        "proposed_response": "Thank you for contacting support.",
    }

    with patch(
        "services.delivery_validation_service.get_ticket",
        return_value=ticket,
    ):
        try:
            validate_approved_response("TKT-TEST")
            raise AssertionError("Closed ticket was accepted")
        except DeliveryValidationError:
            print("PASS: Unsupported ticket status blocked")


if __name__ == "__main__":
    print("\n========== DELIVERY VALIDATION TESTS ==========")

    test_approved_ticket()
    test_missing_ticket()
    test_unapproved_ticket()
    test_empty_response()
    test_unresolved_placeholders()
    test_unsupported_status()

    print("\nALL DELIVERY VALIDATION TESTS PASSED")
