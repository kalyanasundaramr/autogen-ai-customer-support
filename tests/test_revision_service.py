
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.revision_service import generate_revised_response
from services.ticket_service import get_ticket


async def main():
    load_dotenv(BASE_DIR / ".env")

    ticket_id = "TKT-000001"

    reviewer_notes = (
        "Please make the response more empathetic "
        "and clearly explain the shipping delay policy "
        "and next steps."
    )

    print("\n========== AI RESPONSE REVISION TEST ==========")

    ticket = get_ticket(ticket_id)

    assert ticket is not None, "Test ticket not found."
    assert ticket["review_status"] == "Revision Requested"

    original_response = ticket["proposed_response"]

    model_client = OpenAIChatCompletionClient(
        model="gpt-4o-mini",
        api_key=os.environ["OPENAI_API_KEY"],
    )

    try:
        result = await generate_revised_response(
            ticket_id=ticket_id,
            reviewer_notes=reviewer_notes,
            model_client=model_client,
        )

        assert result["ticket_id"] == ticket_id
        assert result["status"] == "Draft Generated"
        assert result["revised_output"].strip()
        assert result["original_response"] == original_response

        # Validate the extracted customer-facing response.
        customer_response = result["customer_response"]

        assert isinstance(customer_response, str)
        assert customer_response.strip()

        # Ensure internal agent sections are excluded.
        assert "Supporting Policies:" not in customer_response
        assert "Recommended Action:" not in customer_response
        assert "Human Review Recommended:" not in customer_response

        # Confirm the extracted response belongs to the full output.
        assert customer_response in result["revised_output"]

        print("PASS: Customer-facing response extracted")
        print("PASS: Internal workflow sections excluded")

        print("\n========== REVISED AI RESPONSE ==========")
        print(result["revised_output"])

        print("\n========== CLEAN CUSTOMER RESPONSE ==========")
        print(customer_response)

        # Confirm the revision service did not modify SQLite.
        saved_ticket = get_ticket(ticket_id)

        assert saved_ticket["proposed_response"] == original_response
        assert saved_ticket["review_status"] == "Revision Requested"

        print("\n========== TEST SUMMARY ==========")
        print("Ticket retrieval: PASS")
        print("Revision status validation: PASS")
        print("AutoGen draft generation: PASS")
        print("Original response preserved: PASS")
        print("Database unchanged: PASS")

        print("\nAI RESPONSE REVISION TEST PASSED")

    finally:
        await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
