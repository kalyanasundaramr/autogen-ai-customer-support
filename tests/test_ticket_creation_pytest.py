
from services.ticket_service import get_ticket
from database.db import get_connection


def test_create_ticket(sample_ticket):
    """Verify a ticket is created in the test database."""

    ticket = get_ticket(sample_ticket)

    assert ticket is not None
    assert ticket["ticket_id"] == sample_ticket
    assert ticket["category"] == "Shipping"
    assert ticket["ticket_status"] == "Pending"
    assert ticket["review_status"] == "Pending"

    print(f"\nPASS: Ticket created: {sample_ticket}")


def test_ticket_persisted_in_sqlite(sample_ticket):
    """Verify the ticket is stored in SQLite."""

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT ticket_id, category, ticket_status
            FROM tickets
            WHERE ticket_id = ?
            """,
            (sample_ticket,),
        ).fetchone()

    assert row is not None
    assert row["ticket_id"] == sample_ticket
    assert row["category"] == "Shipping"
    assert row["ticket_status"] == "Pending"

    print(f"\nPASS: Ticket persisted in SQLite: {sample_ticket}")


def test_ticket_creation_audit(sample_ticket):
    """Verify ticket creation generates an audit event."""

    with get_connection() as connection:
        audit = connection.execute(
            """
            SELECT action, ticket_id
            FROM ticket_audit_logs
            WHERE ticket_id = ?
              AND action = 'TICKET_CREATED'
            """,
            (sample_ticket,),
        ).fetchone()

    assert audit is not None
    assert audit["action"] == "TICKET_CREATED"

    print(f"\nPASS: Ticket creation audit verified: {sample_ticket}")

def test_confidence_fields_persisted(sample_ticket):
    """Verify confidence fields are available on saved tickets."""
    from services.ticket_service import get_ticket

    ticket = get_ticket(sample_ticket)

    assert ticket is not None
    assert "confidence_score" in ticket
    assert "confidence_explanation" in ticket

def test_confidence_values_saved_to_sqlite(sample_ticket):
    """Verify confidence values can be saved and retrieved."""
    from database.db import get_connection
    from services.ticket_service import get_ticket

    confidence_score = 0.85
    confidence_explanation = (
        "Shipping policy directly supports the response."
    )

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE tickets
            SET confidence_score = ?,
                confidence_explanation = ?
            WHERE ticket_id = ?
            """,
            (
                confidence_score,
                confidence_explanation,
                sample_ticket,
            ),
        )

    saved_ticket = get_ticket(sample_ticket)

    assert saved_ticket is not None
    assert saved_ticket["confidence_score"] == confidence_score
    assert (
        saved_ticket["confidence_explanation"]
        == confidence_explanation
    )

def test_confidence_persisted_during_ticket_creation(
    sample_ticket,
    sample_ticket_data,
):
    """Verify confidence values survive the initial ticket INSERT."""

    ticket = get_ticket(sample_ticket)

    assert ticket is not None

    assert (
        ticket["confidence_score"]
        == sample_ticket_data["record"]["confidence_score"]
    )

    assert (
        ticket["confidence_explanation"]
        == sample_ticket_data["record"]["confidence_explanation"]
    )

    assert ticket["ticket_status"] == "Pending"
