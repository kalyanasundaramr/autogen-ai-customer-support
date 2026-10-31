
import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agents.resolution_agent import create_resolution_agent
from rag.search_kb import search_kb

load_dotenv(BASE_DIR / ".env")


async def main():
    model_client = OpenAIChatCompletionClient(
        model="gpt-4o-mini"
    )

    try:
        complaint = (
            "My order is delayed beyond the estimated "
            "delivery date. What should I do?"
        )

        classification = {
            "category": "Shipping",
            "urgency": "Medium",
            "sentiment": "Negative",
            "language": "English",
            "summary": "Customer reports delayed delivery.",
            "escalation_signals": []
        }

        evidence = search_kb(complaint, top_k=5)

        print("\nCustomer Complaint:")
        print(complaint)

        print("\nRAG Evidence Found:", evidence["evidence_found"])
        print("Retrieved Passages:", len(evidence["matches"]))

        assert evidence["evidence_found"], (
            "Expected relevant shipping policy evidence."
        )

        task = (
            "Draft a customer support response using "
            "the following information.\n\n"
            f"Original Complaint:\n{complaint}\n\n"
            f"Customer Classification:\n"
            f"{json.dumps(classification, indent=2)}\n\n"
            f"Knowledge Base Evidence:\n"
            f"{json.dumps(evidence, indent=2)}\n\n"
            "Follow your required output format. "
            "Do not invent policies or claim actions "
            "have already been completed."
        )

        agent = create_resolution_agent(model_client)
        result = await agent.run(task=task)

        response = result.messages[-1].content

        print("\n========== RESOLUTION AGENT ==========")
        print(response)

        assert isinstance(response, str) and response.strip(), (
            "Resolution Agent returned an empty response."
        )

        print("\nTEST PASSED: Resolution draft generated")

    finally:
        await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
