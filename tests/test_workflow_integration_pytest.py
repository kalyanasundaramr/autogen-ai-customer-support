
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
    assert kwargs["selector_func"] is (
        support_workflow.select_next_agent
    )
    assert kwargs["allow_repeated_speaker"] is True
    assert kwargs["termination_condition"] is not None

    for factory_name in factory_names:
        factory = getattr(
            support_workflow,
            factory_name,
        )
        factory.assert_called_once_with(model_client)
