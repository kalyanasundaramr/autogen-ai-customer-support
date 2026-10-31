
import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agents.log_agent import create_log_agent

load_dotenv(BASE_DIR / ".env")


async def main():
    model_client = OpenAIChatCompletionClient(
        model="gpt-4o-mini"
    )

    try:
        agent = create_log_agent(model_client)

        ticket_data = {
            "original_complaint": (
                "My order is delayed beyond the estimated "
                "delivery date. What should I do?"
            ),
            "classification": {
                "category": "Shipping",
                "urgency": "Medium",
                "sentiment": "Negative",
                "language": "English",
                "summary": "Customer reports delayed delivery.",
                "escalation_signals": []
            },
            "knowledge_base": {
                "evidence_found": True,
                "policy_sources": [
                    "shipping_policy.md | Delayed Deliveries",
                    "shipping_policy.md | Escalation"
                ]
            },
            "resolution": {
                "proposed_response": (
                    "I'm sorry your order is delayed. "
                    "Please share your order ID so our "
                    "support team can investigate. "
                    "Delays exceeding seven days beyond "
                    "the estimated date require human review."
                )
            },
            "authoritative_escalation_decision": "Pending",
            "escalation_reason": None
        }

        task = (
            "Prepare a structured ticket record from "
            "the following workflow data. Return JSON only.\n\n"
            + json.dumps(ticket_data, indent=2)
        )

        result = await agent.run(task=task)
        response = result.messages[-1].content

        record = json.loads(response)

        print("\n========== LOG AGENT OUTPUT ==========")
        print(json.dumps(record, indent=2, ensure_ascii=False))

        required_fields = [
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
            "review_status"
        ]

        for field in required_fields:
            assert field in record, (
                f"Missing required field: {field}"
            )

        assert record["category"] == "Shipping"
        assert record["urgency"] == "Medium"
        assert record["evidence_found"] is True
        assert record["escalation_decision"] == "Pending"
        assert record["ticket_status"] == "Pending"
        assert record["review_status"] == "Pending"

        print("\nTEST PASSED: Structured ticket record generated")

    finally:
        await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
