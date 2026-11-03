
import pytest

from autogen_agentchat.agents import UserProxyAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from agents.human_reviewer_agent import (
    create_human_reviewer_agent,
)


def test_human_reviewer_agent_creation():
    agent = create_human_reviewer_agent()

    assert isinstance(agent, UserProxyAgent)
    assert agent.name == "human_reviewer"


@pytest.mark.asyncio
async def test_human_reviewer_agent_custom_input():

    async def mock_input(prompt, cancellation_token=None):
        return "Approve"

    agent = create_human_reviewer_agent(
        input_func=mock_input
    )

    response = await agent.on_messages(
        [
            TextMessage(
                source="support_workflow",
                content="Please review ticket TKT-000026. Approve or Reject?",
            )
        ],
        cancellation_token=CancellationToken(),
    )

    assert response.chat_message.content == "Approve"
    assert response.chat_message.source == "human_reviewer"
