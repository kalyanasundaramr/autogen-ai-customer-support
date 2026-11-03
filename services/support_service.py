
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

     
       
    # Reject workflows that did not terminate successfully.
    stop_reason = result.stop_reason or ""

    if "maximum" in stop_reason.lower() and "message" in stop_reason.lower():
        raise RuntimeError(
            "Workflow terminated due to maximum message limit. "
            "Ticket creation aborted."
        )


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

    
    # Validate dependencies without requiring exactly four messages.
    required_agents = [
        "customer_query_agent",
        "knowledge_base_agent",
        "resolution_agent",
        "log_agent",
    ]

    first_positions = {}

    for index, agent_name in enumerate(execution_order):
        if agent_name not in first_positions:
            first_positions[agent_name] = index

    missing_agents = [
        name for name in required_agents
        if name not in first_positions
    ]

    if missing_agents:
        raise RuntimeError(
            f"Workflow incomplete. Missing agents: {missing_agents}"
        )

    positions = [
        first_positions[name] for name in required_agents
    ]

    if positions != sorted(positions):
        raise RuntimeError(
            f"Agent dependencies violated: {execution_order}"
        )
        # Reject backward transitions between workflow stages.
    stage_index = {
        name: index
        for index, name in enumerate(required_agents)
    }

    for previous, current in zip(
        execution_order,
        execution_order[1:],
    ):
        if stage_index[current] < stage_index[previous]:
            raise RuntimeError(
                "Agent dependencies violated: "
                f"{execution_order}"
            )

    if execution_order[-1] != "log_agent":
        raise RuntimeError(
            "Log Agent must complete the workflow."
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
