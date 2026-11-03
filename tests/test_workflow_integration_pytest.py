
from unittest.mock import MagicMock

from workflows import support_workflow


def test_workflow_construction(monkeypatch):
    """Verify that the four-agent team is constructed correctly."""

    model_client = object()

    agent_names = [
        "customer_query_agent",
        "knowledge_base_agent",
        "resolution_agent",
        "log_agent",
    ]

    fake_agents = [
        MagicMock(name=name)
        for name in agent_names
    ]

    factory_names = [
        "create_customer_query_agent",
        "create_knowledge_base_agent",
        "create_resolution_agent",
        "create_log_agent",
    ]

    for factory_name, agent in zip(factory_names, fake_agents):
        factory = MagicMock(return_value=agent)
        monkeypatch.setattr(
            support_workflow,
            factory_name,
            factory,
        )

    fake_team = object()
    team_constructor = MagicMock(return_value=fake_team)

    monkeypatch.setattr(
        support_workflow,
        "SelectorGroupChat",
        team_constructor,
    )

    result = support_workflow.create_support_workflow(
        model_client
    )

    assert result is fake_team

    team_constructor.assert_called_once()

    kwargs = team_constructor.call_args.kwargs

    assert kwargs["participants"] == fake_agents
    assert kwargs["model_client"] is model_client
    assert "selector_func" not in kwargs
    assert "selector_prompt" in kwargs
    assert kwargs["allow_repeated_speaker"] is False
    assert kwargs["termination_condition"] is not None

    for factory_name in factory_names:
        factory = getattr(
            support_workflow,
            factory_name,
        )
        factory.assert_called_once_with(model_client)

import json
from autogen_agentchat.messages import TextMessage



def test_log_agent_termination_validation():
    """Terminate on valid Log Agent JSON, including message deltas."""

    def msg(source, content):
        return TextMessage(source=source, content=content)

    valid_log = msg(
        "log_agent",
        json.dumps({"category": "Billing"}),
    )

    # A valid Log Agent response triggers termination.
    assert support_workflow.log_agent_completed([valid_log])

    # Earlier agents alone must not trigger termination.
    assert not support_workflow.log_agent_completed([
        msg("customer_query_agent", "Analysis completed"),
        msg("knowledge_base_agent", "Evidence retrieved"),
        msg("resolution_agent", "Response drafted"),
    ])

    # Invalid JSON must not trigger termination.
    assert not support_workflow.log_agent_completed([
        msg("log_agent", "Invalid JSON")
    ])

    # A JSON array is not a valid ticket object.
    assert not support_workflow.log_agent_completed([
        msg("log_agent", "[]")
    ])




def test_log_agent_termination_with_repeated_agents():
    """Terminate on valid Log Agent JSON, regardless of prior messages."""

    def msg(source, content):
        return TextMessage(source=source, content=content)

    valid_messages = [
        msg("customer_query_agent", "Complaint analyzed"),
        msg("knowledge_base_agent", "Initial evidence"),
        msg("knowledge_base_agent", "Additional evidence"),
        msg("resolution_agent", "Response drafted"),
        msg("log_agent", '{"category": "Billing"}'),
    ]

    # Valid Log Agent JSON triggers termination.
    assert support_workflow.log_agent_completed(valid_messages)

    # Termination also works when only the latest message is supplied.
    assert support_workflow.log_agent_completed([
        valid_messages[-1]
    ])

    # A backward transition does not prevent termination.
    # The support service must reject the invalid agent sequence.
    invalid_messages = [
        msg("customer_query_agent", "Complaint analyzed"),
        msg("knowledge_base_agent", "Evidence retrieved"),
        msg("resolution_agent", "Response drafted"),
        msg("customer_query_agent", "Late analysis"),
        msg("log_agent", '{"category": "Billing"}'),
    ]

    assert support_workflow.log_agent_completed(invalid_messages)

