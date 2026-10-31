
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.db import get_connection
from services.ticket_service import get_ticket
from workflows.revision_workflow import run_revision_workflow


async def main():
    load_dotenv(BASE_DIR / ".env")

    ticket_id = "TKT-000010"

    reviewer_notes = (
        "Make the response more empathetic, "
        "explain the next steps clearly, and "
        "avoid promising a delivery date."
    )

    print("\n========== COMPLETE AI REVISION WORKFLOW TEST ==========")

    original = get_ticket(ticket_id)

    assert original is not None, "Test ticket not found."
    assert original["review_status"] == "Revision Requested"

    previous_response = original["proposed_response"]
    previous_ticket_status = original["ticket_status"]

    model_client = OpenAIChatCompletionClient(
        model="gpt-4o-mini",
        api_key=os.environ["OPENAI_API_KEY"],
    )

    try:
        result = await run_revision_workflow(
            ticket_id=ticket_id,
            reviewer_notes=reviewer_notes,
            model_client=model_client,
        )

        saved = get_ticket(ticket_id)

        assert result["ticket_id"] == ticket_id
        assert result["status"] == (
            "Revision Saved - Awaiting Human Review"
        )

        assert saved["proposed_response"] == result["revised_response"]
        print("PASS: AI-generated revision saved")

        assert saved["proposed_response"] != previous_response
        print("PASS: Original response replaced with revised draft")

        assert saved["review_status"] == "Pending"
        print("PASS: Ticket returned to human review")

        assert saved["ticket_status"] == previous_ticket_status
        print("PASS: Customer ticket status preserved")

        for internal_heading in (
            "Supporting Policies:",
            "Recommended Action:",
            "Human Review Recommended:",
        ):
            assert internal_heading not in saved["proposed_response"]

        print("PASS: Internal agent sections excluded")

        with get_connection() as connection:
            audit = connection.execute(
                """
                SELECT action, previous_value, new_value,
                       performed_by, created_at
                FROM ticket_audit_logs
                WHERE ticket_id = ?
                  AND action = 'AI_RESPONSE_REVISED'
                ORDER BY id DESC
                LIMIT 1
                """,
                (ticket_id,),
            ).fetchone()

        assert audit is not None
        assert audit["previous_value"] == previous_response
        assert saved["proposed_response"] in audit["new_value"]
        assert audit["performed_by"] == "AI Resolution Agent"

        print("PASS: Original draft preserved in audit history")
        print("PASS: AI revision audit event recorded")

        print("\n========== SAVED CUSTOMER RESPONSE ==========")
        print(saved["proposed_response"])

        print("\n========== FINAL TICKET STATUS ==========")
        print("Ticket ID:", saved["ticket_id"])
        print("Review Status:", saved["review_status"])
        print("Ticket Status:", saved["ticket_status"])

        print("\n======================================")
        print("ALL AI REVISION WORKFLOW TESTS PASSED")
        print("======================================")

    finally:
        await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
