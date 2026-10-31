
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from autogen_agentchat.messages import (
    ToolCallRequestEvent,
    ToolCallExecutionEvent,
)
from autogen_ext.models.openai import OpenAIChatCompletionClient

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agents.knowledge_base_agent import create_knowledge_base_agent

load_dotenv(BASE_DIR / ".env")


async def main():
    model_client = OpenAIChatCompletionClient(
        model="gpt-4o-mini"
    )

    try:
        agent = create_knowledge_base_agent(model_client)

        complaint = (
            "My order is delayed beyond the estimated "
            "delivery date. What does your shipping policy say?"
        )

        print("\nCustomer Complaint:")
        print(complaint)

        result = await agent.run(task=complaint)

        tool_called = False

        for message in result.messages:
            if isinstance(message, ToolCallRequestEvent):
                for call in message.content:
                    if call.name == "search_kb":
                        tool_called = True
                        print("\nTool called:", call.name)
            if isinstance(message, ToolCallExecutionEvent):
                print("\n========== RAW TOOL RESULTS ==========")

                for execution in message.content:
                    print("Tool:", execution.name)
                    print("Result:", execution.content)
                    
        print("\nKnowledge Base Agent Response:")
        print(result.messages[-1].content)

        assert tool_called, (
            "Knowledge Base Agent did not call search_kb."
        )

        print("\nTEST PASSED: search_kb tool invoked")

    finally:
        await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
