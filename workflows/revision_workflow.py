
from services.revision_service import generate_revised_response
from services.revision_persistence_service import save_revised_response


async def run_revision_workflow(
    ticket_id: str,
    reviewer_notes: str,
    model_client,
) -> dict:
    """
    Generate and save an AI-revised customer response.

    The ticket returns to Pending human review.
    The response is not sent to the customer.
    """

    # Step 1: Generate and parse the revised response.
    revision = await generate_revised_response(
        ticket_id=ticket_id,
        reviewer_notes=reviewer_notes,
        model_client=model_client,
    )

    customer_response = revision["customer_response"]

    # Step 2: Persist only the customer-facing draft.
    saved = save_revised_response(
        ticket_id=ticket_id,
        revised_response=customer_response,
        reviewer_notes=reviewer_notes,
        performed_by="AI Resolution Agent",
    )

    # Step 3: Return the saved revision details.
    return {
        "ticket_id": ticket_id,
        "previous_response": saved["previous_response"],
        "revised_response": saved["revised_response"],
        "review_status": saved["review_status"],
        "ticket_status": saved["ticket_status"],
        "saved_at": saved["saved_at"],
        "status": "Revision Saved - Awaiting Human Review",
    }
