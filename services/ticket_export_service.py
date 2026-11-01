
import csv
import io
import json

from services.ticket_query_service import list_all_tickets


EXPORT_COLUMNS = [
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


def _format_sources(value):
    """Convert stored knowledge-base sources to readable text."""
    if value is None:
        return ""

    if isinstance(value, list):
        return "; ".join(str(item) for item in value)

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return "; ".join(str(item) for item in parsed)
        except json.JSONDecodeError:
            pass

    return str(value)


def export_tickets_csv() -> str:
    """Export all persisted tickets to CSV text."""

    tickets = list_all_tickets()

    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=EXPORT_COLUMNS,
        extrasaction="ignore",
    )

    writer.writeheader()

    for ticket in tickets:
        writer.writerow({
            "ticket_id": ticket.get("ticket_id", ""),
            "timestamp": ticket.get("created_at", ""),
            "customer_name_order_id": (
                ticket.get("customer_name")
                or ticket.get("order_id")
                or ""
            ),
            "complaint": ticket.get("original_complaint", ""),
            "category": ticket.get("category", ""),
            "urgency": ticket.get("urgency", ""),
            "sentiment": ticket.get("sentiment", ""),
            "kb_sources": _format_sources(
                ticket.get("policy_sources")
            ),
            "response": ticket.get("proposed_response", ""),
            "status": ticket.get("ticket_status", ""),
            "escalation_reason": (
                ticket.get("escalation_reason") or ""
            ),
        })

    return output.getvalue()
