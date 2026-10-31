
from autogen_agentchat.messages import TextMessage

from workflows.support_workflow import (
    AGENT_ORDER,
    select_next_agent,
    log_agent_completed,
)


def test_complete_agent_handoff():
    """Verify the complete four-agent message sequence."""

    messages = [
        TextMessage(
            source="user",
            content="My order has not arrived.",
        )
    ]

    expected_outputs = {
        "customer_query_agent": (
            "Category: Shipping; Urgency: Medium"
        ),
        "knowledge_base_agent": (
            "Shipping policy: investigate delayed deliveries."
        ),
        "resolution_agent": (
            "Please provide your order ID."
        ),
        "log_agent": (
            '{"category": "Shipping", "status": "Pending"}'
        ),
    }

    executed_agents = []

    for expected_agent in AGENT_ORDER:
        selected_agent = select_next_agent(messages)

        assert selected_agent == expected_agent

        messages.append(
            TextMessage(
                source=selected_agent,
                content=expected_outputs[selected_agent],
            )
        )

        executed_agents.append(selected_agent)

        if selected_agent != "log_agent":
            assert log_agent_completed(messages) is False

    assert executed_agents == AGENT_ORDER
    assert log_agent_completed(messages) is True


def test_user_message_does_not_skip_agent():
    messages = [
        TextMessage(
            source="user",
            content="I need a refund.",
        ),
        TextMessage(
            source="customer_query_agent",
            content="Category: Refund",
        ),
        TextMessage(
            source="user",
            content="Please help quickly.",
        ),
    ]

    assert select_next_agent(messages) == "knowledge_base_agent"


def test_log_agent_termination_requires_text():
    messages = [
        TextMessage(
            source="resolution_agent",
            content="Customer response generated.",
        )
    ]

    assert log_agent_completed(messages) is False

    messages.append(
        TextMessage(
            source="log_agent",
            content='{"status": "Pending"}',
        )
    )

    assert log_agent_completed(messages) is True
