
import json

from autogen_agentchat.messages import TextMessage

from workflows.support_workflow import (
    create_support_workflow,
    AGENT_ORDER,
)
from services.ticket_service import (
    create_ticket,
    get_ticket,
)

from services.ticket_validator import validate_ticket_record


async def process_customer_complaint(
    complaint: str,
    model_client,
) -> dict:
    """
    Run the AutoGen workflow and persist the ticket.

    Returns the saved ticket record.
    """

    if not isinstance(complaint, str) or not complaint.strip():
        raise ValueError("Customer complaint cannot be empty.")

    team = create_support_workflow(model_client)

    result = await team.run(task=complaint.strip())

    # Collect final text responses from each agent.
    agent_messages = [
        message
        for message in result.messages
        if isinstance(message, TextMessage)
        and message.source in AGENT_ORDER
    ]

    execution_order = [
        message.source for message in agent_messages
    ]

    if execution_order != AGENT_ORDER:
        raise RuntimeError(
            f"Unexpected agent execution order: {execution_order}"
        )

    if len(agent_messages) != 4:
        raise RuntimeError(
            "Expected exactly four agent responses."
        )

    # Extract the Log Agent's structured record.
    log_response = agent_messages[-1].content

    try:
        record = json.loads(log_response)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError(
            "Log Agent did not return valid JSON."
        ) from exc

    if not isinstance(record, dict):
        raise ValueError(
            "Log Agent output must be a JSON object."
        )

    # The LLM does not control the final escalation decision.
    # Reset provisional fields to safe application defaults.
    # create_ticket() will independently calculate escalation
    # using deterministic Python business rules.
    record["escalation_decision"] = "Pending"
    record["escalation_reason"] = None

    # Initial workflow statuses are application-controlled.
    record["ticket_status"] = "Pending"
    record["review_status"] = "Pending"

    # Validate the normalized ticket record.
    record = validate_ticket_record(record)

    # create_ticket() applies authoritative
    # Python escalation rules before saving.
    ticket_id = create_ticket(
        original_complaint=complaint,
        record=record,
    )

    saved_ticket = get_ticket(ticket_id)

    if saved_ticket is None:
        raise RuntimeError(
            "Ticket was created but could not be retrieved."
        )

    return {
        "ticket_id": ticket_id,
        "ticket": saved_ticket,
        "execution_order": execution_order,
        "stop_reason": result.stop_reason,
    }
