
import pytest

from services.review_service import review_ticket
from services.ticket_service import get_ticket
from services.ticket_lifecycle_service import (
    update_ticket_status,
    TicketLifecycleError,
)
from services.ticket_audit_query_service import (
    list_ticket_audit_history,
)


def approve_ticket(ticket_id):
    review_ticket(
        ticket_id=ticket_id,
        action="Approve",
        reviewer="Pytest Reviewer",
        notes="Approved for lifecycle testing.",
    )


def change_status(ticket_id, new_status):
    return update_ticket_status(
        ticket_id=ticket_id,
        new_status=new_status,
        performed_by="Pytest Operator",
        reason="Automated lifecycle regression test",
    )


def test_pending_to_escalated(sample_ticket):
    result = change_status(sample_ticket, "Escalated")

    assert result["previous_status"] == "Pending"
    assert result["new_status"] == "Escalated"
    assert get_ticket(sample_ticket)["ticket_status"] == "Escalated"


def test_approved_ticket_can_be_resolved(sample_ticket):
    approve_ticket(sample_ticket)

    change_status(sample_ticket, "Resolved")

    assert get_ticket(sample_ticket)["ticket_status"] == "Resolved"


def test_unapproved_ticket_cannot_be_resolved(sample_ticket):
    with pytest.raises(TicketLifecycleError):
        change_status(sample_ticket, "Resolved")

    assert get_ticket(sample_ticket)["ticket_status"] == "Pending"


def test_complete_lifecycle(sample_ticket):
    approve_ticket(sample_ticket)

    for status in ("Escalated", "Resolved", "Closed"):
        change_status(sample_ticket, status)

    assert get_ticket(sample_ticket)["ticket_status"] == "Closed"

    events = list_ticket_audit_history(sample_ticket)

    lifecycle_events = [
        event for event in events
        if event["action"] == "TICKET_STATUS_CHANGED"
    ]

    assert len(lifecycle_events) == 3


def test_closed_ticket_cannot_reopen(sample_ticket):
    approve_ticket(sample_ticket)

    for status in ("Resolved", "Closed"):
        change_status(sample_ticket, status)

    with pytest.raises(TicketLifecycleError):
        change_status(sample_ticket, "Pending")

    assert get_ticket(sample_ticket)["ticket_status"] == "Closed"


def test_pending_to_closed_blocked(sample_ticket):
    approve_ticket(sample_ticket)

    with pytest.raises(TicketLifecycleError):
        change_status(sample_ticket, "Closed")

    assert get_ticket(sample_ticket)["ticket_status"] == "Pending"


def test_operator_and_reason_required(sample_ticket):
    with pytest.raises(TicketLifecycleError):
        update_ticket_status(
            ticket_id=sample_ticket,
            new_status="Escalated",
            performed_by="",
            reason="Testing",
        )

    with pytest.raises(TicketLifecycleError):
        update_ticket_status(
            ticket_id=sample_ticket,
            new_status="Escalated",
            performed_by="Pytest Operator",
            reason="",
        )

    assert get_ticket(sample_ticket)["ticket_status"] == "Pending"


def test_lifecycle_audit_details(sample_ticket):
    change_status(sample_ticket, "Escalated")

    events = list_ticket_audit_history(sample_ticket)

    lifecycle_event = next(
        event for event in events
        if event["action"] == "TICKET_STATUS_CHANGED"
    )

    assert lifecycle_event["previous_value"] == "Pending"
    assert lifecycle_event["new_value"].startswith("Escalated")
    assert lifecycle_event["performed_by"] == "Pytest Operator"
    assert lifecycle_event["created_at"]
