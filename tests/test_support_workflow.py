
import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from workflows.support_workflow import (
    create_support_workflow,
    AGENT_ORDER,
)

load_dotenv(BASE_DIR / ".env")


async def main():
    model_client = OpenAIChatCompletionClient(
        model="gpt-4o-mini"
    )

    try:
        team = create_support_workflow(model_client)

        complaint = (
            "My order is delayed beyond the estimated "
            "delivery date. What should I do?"
        )

        print("\n========== CUSTOMER COMPLAINT ==========")
        print(complaint)

        print("\n========== AGENT EXECUTION ==========")

        result = await team.run(task=complaint)

        executed_agents = []

        for message in result.messages:
            if (
                isinstance(message, TextMessage)
                and message.source in AGENT_ORDER
            ):
                executed_agents.append(message.source)

                print("\nAgent:", message.source)
                print("Response:", message.content[:500])

        print("\n========== WORKFLOW SUMMARY ==========")
        print("Execution order:", executed_agents)
        print("Stop reason:", result.stop_reason)

        assert executed_agents[:4] == AGENT_ORDER, (
            "Agents did not execute in the expected order."
        )

        print("\n========== LOG RECORD VALIDATION ==========")

        log_messages = [
            message
            for message in result.messages
            if isinstance(message, TextMessage)
            and message.source == "log_agent"
        ]

        assert len(log_messages) == 1, (
            "Expected exactly one Log Agent response."
        )

        log_record = json.loads(log_messages[0].content)

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
            "review_status",
        ]

        missing_fields = [
            field for field in required_fields
            if field not in log_record
        ]

        assert not missing_fields, (
            f"Missing fields: {missing_fields}"
        )

        assert log_record["category"] == "Shipping"
        assert log_record["ticket_status"] == "Pending"
        assert log_record["review_status"] == "Pending"
        assert log_record["escalation_decision"] == "Pending"
        assert isinstance(log_record["policy_sources"], list)
        assert isinstance(log_record["proposed_response"], str)
        assert log_record["proposed_response"].strip()

        print("JSON parsing: PASS")
        print("Required fields: PASS")
        print("Ticket status: Pending")
        print("Review status: Pending")
        print("Escalation decision: Pending")
        print("Proposed response: Present")
        print("LOG RECORD VALIDATION PASSED")

        print("\nTEST PASSED: Four-agent sequence verified")

    finally:
        await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
