
import pytest

from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from workflows.support_workflow import (
    AGENT_ORDER,
    select_next_agent,
    log_agent_completed,
)


def make_message(source, content="Test response"):
    return TextMessage(
        source=source,
        content=content,
    )


def test_agent_order():
    assert AGENT_ORDER == [
        "customer_query_agent",
        "knowledge_base_agent",
        "resolution_agent",
        "log_agent",
    ]


def test_first_agent_selected():
    messages = [
        make_message("user", "My order is delayed.")
    ]

    assert select_next_agent(messages) == "customer_query_agent"


@pytest.mark.parametrize(
    "completed_agents,expected_next",
    [
        (
            ["customer_query_agent"],
            "knowledge_base_agent",
        ),
        (
            [
                "customer_query_agent",
                "knowledge_base_agent",
            ],
            "resolution_agent",
        ),
        (
            [
                "customer_query_agent",
                "knowledge_base_agent",
                "resolution_agent",
            ],
            "log_agent",
        ),
    ],
)
def test_agent_sequence(completed_agents, expected_next):
    messages = [
        make_message("user", "My order is delayed.")
    ]

    messages.extend(
        make_message(agent)
        for agent in completed_agents
    )

    assert select_next_agent(messages) == expected_next


def test_log_agent_termination():
    messages = [
        make_message("customer_query_agent"),
        make_message("knowledge_base_agent"),
        make_message("resolution_agent"),
        make_message("log_agent"),
    ]

    assert log_agent_completed(messages) is True


def test_no_early_termination():
    messages = [
        make_message("customer_query_agent"),
        make_message("knowledge_base_agent"),
        make_message("resolution_agent"),
    ]

    assert log_agent_completed(messages) is False


def test_unrelated_message_ignored():
    messages = [
        make_message("user", "Help with my refund."),
        make_message("unknown_agent", "Unrelated response"),
    ]

    assert select_next_agent(messages) == "customer_query_agent"


def test_selector_after_log_response():
    messages = [
        make_message(agent)
        for agent in AGENT_ORDER
    ]

    assert select_next_agent(messages) == "log_agent"
