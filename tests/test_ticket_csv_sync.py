import csv
import io

from services import ticket_csv_service


def test_csv_sync_creates_file_with_required_columns(
    sample_ticket,
    tmp_path,
    monkeypatch,
):
    """Verify a persisted test ticket is exported to CSV."""

    csv_path = tmp_path / "tickets.csv"

    monkeypatch.setattr(
        ticket_csv_service,
        "CSV_PATH",
        csv_path,
    )

    result = ticket_csv_service.sync_tickets_csv()

    assert result == csv_path
    assert csv_path.exists()

    with csv_path.open(
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)
        rows = list(reader)

        assert reader.fieldnames == [
            "ticket_id",
            "timestamp",
            "customer_name_order_id",
            "complaint",
            "category",
            "urgency",
            "sentiment",
            "kb_sources",
            "response",
            "status",
            "escalation_reason",
        ]

    assert any(
        row["ticket_id"] == sample_ticket
        for row in rows
    )

def test_create_ticket_triggers_csv_sync(
    sample_ticket_data,
    monkeypatch,
):
    """Verify ticket creation automatically triggers CSV sync."""
    from services import ticket_csv_service
    from services.ticket_service import create_ticket

    sync_calls = []

    def mock_sync():
        sync_calls.append(True)

    monkeypatch.setattr(
        ticket_csv_service,
        "sync_tickets_csv",
        mock_sync,
    )

    ticket_id = create_ticket(
        sample_ticket_data["complaint"],
        sample_ticket_data["record"],
    )

    assert ticket_id.startswith("TKT-")
    assert len(sync_calls) == 1