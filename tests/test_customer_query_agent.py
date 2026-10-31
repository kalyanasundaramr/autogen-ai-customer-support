
import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agents.customer_query_agent import create_customer_query_agent

load_dotenv(BASE_DIR / ".env")


async def main():
    model_client = OpenAIChatCompletionClient(
        model="gpt-4o-mini"
    )

    try:
        agent = create_customer_query_agent(model_client)

        complaint = (
            "I was charged three times for one order! "
            "This is unacceptable. If you don't fix it, "
            "I will take legal action."
        )

        print("\nCustomer Complaint:")
        print(complaint)

        result = await agent.run(task=complaint)

        response = result.messages[-1].content

        print("\nCustomer Query Agent Response:")

        parsed = json.loads(response)
        print(json.dumps(parsed, indent=2, ensure_ascii=False))

        assert parsed["category"] == "Billing"
        assert parsed["urgency"] == "High"
        assert parsed["escalation_signals"], (
            "Expected at least one escalation signal."
        )

        print("\nTEST PASSED")

    finally:
        await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
