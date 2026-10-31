
import pytest

from services.review_service import review_ticket
from services.ticket_service import get_ticket
from services.ticket_audit_query_service import (
    list_ticket_audit_history,
)


def test_approve_ticket(sample_ticket):
    """Human approval updates the ticket and audit history."""

    review_ticket(
        ticket_id=sample_ticket,
        action="Approve",
        reviewer="Test Reviewer",
        notes="Response verified for testing.",
    )

    ticket = get_ticket(sample_ticket)

    assert ticket["review_status"] == "Approved"

    events = list_ticket_audit_history(sample_ticket)

    assert any(
        event["action"] == "REVIEW_APPROVE"
        for event in events
    )

    print(f"\nPASS: Ticket approved: {sample_ticket}")


def test_request_revision(sample_ticket):
    """Revision requires reviewer notes."""

    review_ticket(
        ticket_id=sample_ticket,
        action="Revise",
        reviewer="Test Reviewer",
        notes="Please make the response more empathetic.",
    )

    ticket = get_ticket(sample_ticket)

    assert ticket["review_status"] == "Revision Requested"

    events = list_ticket_audit_history(sample_ticket)

    assert any(
        event["action"] == "REVIEW_REVISE"
        for event in events
    )

    print(f"\nPASS: Revision requested: {sample_ticket}")


def test_reject_ticket(sample_ticket):
    """Human rejection updates the ticket and audit history."""

    review_ticket(
        ticket_id=sample_ticket,
        action="Reject",
        reviewer="Test Reviewer",
        notes="Response does not meet quality requirements.",
    )

    ticket = get_ticket(sample_ticket)

    assert ticket["review_status"] == "Rejected"

    events = list_ticket_audit_history(sample_ticket)

    assert any(
        event["action"] == "REVIEW_REJECT"
        for event in events
    )

    print(f"\nPASS: Ticket rejected: {sample_ticket}")


@pytest.mark.parametrize("action", ["Revise", "Reject"])
def test_review_notes_required(sample_ticket, action):
    """Revision and rejection must include notes."""

    with pytest.raises(ValueError):
        review_ticket(
            ticket_id=sample_ticket,
            action=action,
            reviewer="Test Reviewer",
            notes="",
        )

    assert get_ticket(sample_ticket)["review_status"] == "Pending"

    print(f"\nPASS: {action} without notes blocked")


def test_duplicate_review_blocked(sample_ticket):
    """An approved ticket cannot be reviewed again."""

    review_ticket(
        ticket_id=sample_ticket,
        action="Approve",
        reviewer="Test Reviewer",
    )

    with pytest.raises(ValueError):
        review_ticket(
            ticket_id=sample_ticket,
            action="Reject",
            reviewer="Test Reviewer",
            notes="Attempting duplicate review.",
        )

    assert get_ticket(sample_ticket)["review_status"] == "Approved"

    print("\nPASS: Duplicate review blocked")
