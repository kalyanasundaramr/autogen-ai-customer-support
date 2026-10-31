
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import (
    MaxMessageTermination,
    FunctionalTermination,
)
from autogen_agentchat.messages import TextMessage

from agents.customer_query_agent import create_customer_query_agent
from agents.knowledge_base_agent import create_knowledge_base_agent
from agents.resolution_agent import create_resolution_agent
from agents.log_agent import create_log_agent


AGENT_ORDER = [
    "customer_query_agent",
    "knowledge_base_agent",
    "resolution_agent",
    "log_agent",
]


def select_next_agent(messages):
    """Select the next agent based on completed text responses."""

    completed = [
        message.source
        for message in messages
        if isinstance(message, TextMessage)
        and message.source in AGENT_ORDER
    ]

    if not completed:
        return AGENT_ORDER[0]

    last_agent = completed[-1]

    if last_agent == AGENT_ORDER[-1]:
        return AGENT_ORDER[-1]

    next_index = AGENT_ORDER.index(last_agent) + 1
    return AGENT_ORDER[next_index]


def log_agent_completed(messages):
    """Return True when the Log Agent has produced a text response."""

    return any(
        isinstance(message, TextMessage)
        and message.source == "log_agent"
        for message in messages
    )


def create_support_workflow(model_client):
    """
    Create the four-agent customer support workflow.

    Expected execution:
    Customer Query -> Knowledge Base -> Resolution -> Log

    Termination:
    - Log Agent produces a TextMessage.
    - Maximum of 20 messages.
    """

    query_agent = create_customer_query_agent(model_client)
    kb_agent = create_knowledge_base_agent(model_client)
    resolution_agent = create_resolution_agent(model_client)
    log_agent = create_log_agent(model_client)

    participants = [
        query_agent,
        kb_agent,
        resolution_agent,
        log_agent,
    ]

    termination = (
        FunctionalTermination(log_agent_completed)
        | MaxMessageTermination(max_messages=20)
    )

    team = SelectorGroupChat(
        participants=participants,
        model_client=model_client,
        selector_func=select_next_agent,
        termination_condition=termination,
        allow_repeated_speaker=True,
    )

    return team
