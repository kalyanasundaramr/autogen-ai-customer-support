
import pytest

from database.db import get_connection
from services.review_service import review_ticket
from services.ticket_service import get_ticket
from services.delivery_validation_service import (
    validate_approved_response,
    DeliveryValidationError,
)
from services.delivery_persistence_service import (
    save_simulated_delivery,
    DuplicateDeliveryError,
)
from services.delivery_query_service import list_delivery_history
from services.ticket_audit_query_service import (
    list_ticket_audit_history,
)


def approve_test_ticket(ticket_id):
    review_ticket(
        ticket_id=ticket_id,
        action="Approve",
        reviewer="Pytest Reviewer",
        notes="Approved for simulation testing.",
    )


def test_unapproved_delivery_blocked(sample_ticket):
    with pytest.raises(DeliveryValidationError):
        validate_approved_response(sample_ticket)

    assert list_delivery_history(sample_ticket) == []


def test_approved_delivery_validation(sample_ticket):
    approve_test_ticket(sample_ticket)

    result = validate_approved_response(sample_ticket)

    assert result["delivery_eligible"] is True
    assert result["delivery_mode"] == "simulation"


def test_simulated_delivery_persisted(sample_ticket):
    approve_test_ticket(sample_ticket)

    receipt = save_simulated_delivery(sample_ticket)
    history = list_delivery_history(sample_ticket)

    assert len(history) == 1
    assert history[0]["delivery_id"] == receipt["delivery_id"]
    assert history[0]["delivery_status"] == "Simulated"
    assert history[0]["actual_message_sent"] is False

    # Simulated delivery must not resolve the ticket.
    assert get_ticket(sample_ticket)["ticket_status"] == "Pending"


def test_duplicate_delivery_blocked(sample_ticket):
    approve_test_ticket(sample_ticket)

    save_simulated_delivery(sample_ticket)

    with pytest.raises(DuplicateDeliveryError):
        save_simulated_delivery(sample_ticket)

    assert len(list_delivery_history(sample_ticket)) == 1


def test_delivery_audit_created(sample_ticket):
    approve_test_ticket(sample_ticket)

    save_simulated_delivery(sample_ticket)

    events = list_ticket_audit_history(sample_ticket)

    delivery_events = [
        event for event in events
        if event["action"] == "DELIVERY_SIMULATED"
    ]

    assert len(delivery_events) == 1


def test_rejected_ticket_cannot_be_delivered(sample_ticket):
    review_ticket(
        ticket_id=sample_ticket,
        action="Reject",
        reviewer="Pytest Reviewer",
        notes="Response rejected for testing.",
    )

    with pytest.raises(DeliveryValidationError):
        save_simulated_delivery(sample_ticket)

    assert list_delivery_history(sample_ticket) == []
