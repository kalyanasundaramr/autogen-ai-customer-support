
import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.db import initialize_database, get_connection
from services.support_service import process_customer_complaint

load_dotenv(BASE_DIR / ".env")


async def main():
    initialize_database()

    model_client = OpenAIChatCompletionClient(
        model="gpt-4o-mini"
    )

    try:
        complaint = (
            "I was charged three times for one order! "
            "If you don't fix it, I will take legal action."
        )

        print("\n========== CUSTOMER COMPLAINT ==========")
        print(complaint)

        print("\n========== RUNNING AUTOGEN WORKFLOW ==========")

        result = await process_customer_complaint(
            complaint=complaint,
            model_client=model_client,
        )

        ticket_id = result["ticket_id"]
        ticket = result["ticket"]

        print("\n========== AGENT EXECUTION ==========")
        for agent in result["execution_order"]:
            print(agent)

        print("\n========== SAVED TICKET ==========")
        print("Ticket ID:", ticket_id)
        print("Category:", ticket["category"])
        print("Urgency:", ticket["urgency"])
        print("Sentiment:", ticket["sentiment"])
        print("Escalation:", ticket["escalation_decision"])
        print("Reason:", ticket["escalation_reason"])
        print("Ticket status:", ticket["ticket_status"])
        print("Review status:", ticket["review_status"])
        print("Evidence found:", ticket["evidence_found"])
        print("Policy sources:", ticket["policy_sources"])

        print("\n========== PROPOSED RESPONSE ==========")
        print(ticket["proposed_response"])

        expected_order = [
            "customer_query_agent",
            "knowledge_base_agent",
            "resolution_agent",
            "log_agent",
        ]

        assert result["execution_order"] == expected_order
        assert ticket["original_complaint"] == complaint
        assert ticket["category"] == "Billing"
        assert ticket["escalation_decision"] == "Escalated"
        assert ticket["ticket_status"] == "Escalated"
        assert ticket["review_status"] == "Pending"

        assert ticket["escalation_reason"]
        assert "Legal threat detected" in ticket["escalation_reason"]
        assert "Payment or billing dispute" in ticket["escalation_reason"]

        assert isinstance(ticket["proposed_response"], str)
        assert ticket["proposed_response"].strip()

        with get_connection() as connection:
            audit = connection.execute(
                """
                SELECT action, new_value
                FROM ticket_audit_logs
                WHERE ticket_id = ?
                """,
                (ticket_id,),
            ).fetchone()

        assert audit is not None
        assert audit["action"] == "TICKET_CREATED"

        audit_data = json.loads(audit["new_value"])
        assert audit_data["escalation_decision"] == "Escalated"

        print("\n========== TEST SUMMARY ==========")
        print("Four-agent execution: PASS")
        print("Ticket persistence: PASS")
        print("Python escalation override: PASS")
        print("Human review remains pending: PASS")
        print("Audit logging: PASS")
        print("END-TO-END TEST PASSED")

    finally:
        await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
