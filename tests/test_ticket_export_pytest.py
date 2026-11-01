
import csv
import io

from services.ticket_export_service import (
    EXPORT_COLUMNS,
    export_tickets_csv,
)


def test_ticket_csv_export(sample_ticket):
    """Verify that a persisted ticket appears in the CSV export."""

    csv_content = export_tickets_csv()

    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)

    # Validate required CSV columns.
    assert reader.fieldnames == EXPORT_COLUMNS

    # Find the ticket created by the test fixture.
    matching_rows = [
        row for row in rows
        if row["ticket_id"] == sample_ticket
    ]

    assert len(matching_rows) == 1

    ticket = matching_rows[0]

    assert ticket["complaint"] == (
        "My test order has not arrived yet."
    )
    assert ticket["category"] == "Shipping"
    assert ticket["urgency"] == "Medium"
    assert ticket["sentiment"] == "Neutral"
    assert ticket["status"] == "Pending"

    assert "shipping_policy.md" in ticket["kb_sources"]

    assert ticket["response"]
    assert ticket["timestamp"]
