
from autogen_agentchat.messages import TextMessage

from agents.resolution_agent import create_resolution_agent
from services.ticket_service import get_ticket
from services.response_parser import extract_customer_response

async def generate_revised_response(
    ticket_id: str,
    reviewer_notes: str,
    model_client,
) -> dict:
    """
    Generate a revised customer response using
    the existing AutoGen Resolution Agent.

    This function does not update SQLite.
    """

    if not reviewer_notes or not reviewer_notes.strip():
        raise ValueError("Reviewer feedback is required.")

    ticket = get_ticket(ticket_id)

    if ticket is None:
        raise ValueError("Ticket not found.")

    if ticket["review_status"] != "Revision Requested":
        raise ValueError(
            "Ticket must have Revision Requested status."
        )

    agent = create_resolution_agent(model_client)

    sources = ticket.get("policy_sources") or []

    task = f"""
You are revising an existing customer support draft.

ORIGINAL CUSTOMER COMPLAINT:
{ticket["original_complaint"]}

CUSTOMER LANGUAGE:
{ticket["language"]}

ORIGINAL RESPONSE:
{ticket["proposed_response"]}

RECORDED POLICY SOURCES:
{sources}

HUMAN REVIEWER FEEDBACK:
{reviewer_notes}

INSTRUCTIONS:
1. Improve the original response based on the feedback.
2. Maintain a professional, empathetic tone.
3. Respond in the customer's language.
4. Do not invent company policies.
5. Policy source names alone are not policy evidence.
6. If the available information is insufficient,
   recommend human investigation instead of
   inventing policy details.
7. Do not claim any refund, replacement, or
   investigation has already been completed.
8. Return a revised draft for human approval.
9. Do not send anything to the customer.

Use your normal Resolution Agent output format.
"""

    result = await agent.run(
        task=task
    )

    messages = [
        message
        for message in result.messages
        if isinstance(message, TextMessage)
        and message.source == "resolution_agent"
    ]

    if not messages:
        raise RuntimeError(
            "Resolution Agent returned no response."
        )

    revised_output = messages[-1].content

    if not isinstance(revised_output, str) or not revised_output.strip():
        raise ValueError(
            "Resolution Agent returned an empty revision."
        )

        # Extract only the customer-facing response.
    customer_response = extract_customer_response(
        revised_output
    )

    return {
        "ticket_id": ticket_id,
        "original_response": ticket["proposed_response"],
        "revised_output": revised_output.strip(),
        "customer_response": customer_response,
        "reviewer_notes": reviewer_notes.strip(),
        "status": "Draft Generated",
    }
