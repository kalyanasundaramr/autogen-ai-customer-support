
import json
import sqlite3
from services.escalation_service import evaluate_escalation

from database.db import get_connection


REQUIRED_FIELDS = [
    "category",
    "urgency",
    "sentiment",
    "language",
    "summary",
    "escalation_signals",
    "evidence_found",
    "policy_sources",
    "proposed_response",
    "escalation_decision",
    "escalation_reason",
    "ticket_status",
    "review_status",
]


def create_ticket(original_complaint: str, record: dict) -> str:
    """
    Validate and persist a support ticket.

    Returns the generated ticket ID.
    """

    if not isinstance(original_complaint, str) or not original_complaint.strip():
        raise ValueError("Original complaint cannot be empty.")

    if not isinstance(record, dict):
        raise ValueError("Ticket record must be a dictionary.")

    missing = [
        field for field in REQUIRED_FIELDS
        if field not in record
    ]

    if missing:
        raise ValueError(f"Missing ticket fields: {missing}")

    if not isinstance(record["escalation_signals"], list):
        raise ValueError("escalation_signals must be a list.")

    if not isinstance(record["policy_sources"], list):
        raise ValueError("policy_sources must be a list.")

    if not isinstance(record["evidence_found"], bool):
        raise ValueError("evidence_found must be a boolean.")

    # The application, not the LLM, controls initial statuses.
        # Python business rules override the LLM's escalation decision.
    escalation = evaluate_escalation(
        original_complaint,
        record,
    )

    escalation_decision = escalation["escalation_decision"]
    escalation_reason = escalation["escalation_reason"]

    # Human review remains pending until a reviewer acts.
    ticket_status = (
        "Escalated"
        if escalation_decision == "Escalated"
        else "Pending"
    )
    review_status = "Pending"

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO tickets (
                original_complaint,
                category,
                urgency,
                sentiment,
                language,
                summary,
                escalation_signals,
                evidence_found,
                policy_sources,
                proposed_response,
                escalation_decision,
                escalation_reason,
                ticket_status,
                review_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                original_complaint.strip(),
                record["category"],
                record["urgency"],
                record["sentiment"],
                record["language"],
                record["summary"],
                json.dumps(record["escalation_signals"]),
                int(record["evidence_found"]),
                json.dumps(record["policy_sources"]),
                record["proposed_response"],
                escalation_decision,
                escalation_reason,
                ticket_status,
                review_status,
            ),
        )

        ticket_id = f"TKT-{cursor.lastrowid:06d}"

        connection.execute(
            "UPDATE tickets SET ticket_id = ? WHERE id = ?",
            (ticket_id, cursor.lastrowid),
        )

        connection.execute(
            """
            INSERT INTO ticket_audit_logs (
                ticket_id,
                action,
                previous_value,
                new_value,
                performed_by
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                "TICKET_CREATED",
                None,
                json.dumps({
                    "ticket_status": ticket_status,
                    "review_status": review_status,
                    "escalation_decision": escalation_decision,
                    "escalation_reason": escalation_reason,
                }),
                "system",
            ),
        )

    return ticket_id


def get_ticket(ticket_id: str) -> dict | None:
    """
    Retrieve a saved ticket by its ID.
    """

    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM tickets WHERE ticket_id = ?",
            (ticket_id,),
        ).fetchone()

    if row is None:
        return None

    ticket = dict(row)

    ticket["escalation_signals"] = json.loads(
        ticket["escalation_signals"]
    )
    ticket["policy_sources"] = json.loads(
        ticket["policy_sources"]
    )
    ticket["evidence_found"] = bool(ticket["evidence_found"])

    return ticket
