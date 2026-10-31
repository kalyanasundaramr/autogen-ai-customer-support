
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from autogen_agentchat.messages import TextMessage

from services import support_service
from services.ticket_service import get_ticket
from services.ticket_audit_query_service import (
    list_ticket_audit_history,
)


def make_agent_messages(record):
    """Build a complete four-agent conversation."""

    return [
        TextMessage(
            source="customer_query_agent",
            content="Shipping complaint; medium urgency.",
        ),
        TextMessage(
            source="knowledge_base_agent",
            content="Relevant shipping policy retrieved.",
        ),
        TextMessage(
            source="resolution_agent",
            content="Please provide your order ID.",
        ),
        TextMessage(
            source="log_agent",
            content=json.dumps(record),
        ),
    ]


@pytest.mark.asyncio
async def test_support_service_end_to_end(
    monkeypatch,
    sample_ticket_data,
):
    """Verify orchestration, validation, persistence and audit."""

    complaint = sample_ticket_data["complaint"]
    record = sample_ticket_data["record"].copy()

    # Deliberately provide AI-controlled statuses.
    # The service must override these.
    record["ticket_status"] = "Closed"
    record["review_status"] = "Approved"
    record["escalation_decision"] = "Yes"

    messages = make_agent_messages(record)

    fake_team = MagicMock()
    fake_team.run = MagicMock()

    async def fake_run(task):
        assert task == complaint

        return SimpleNamespace(
            messages=messages,
            stop_reason="Log Agent completed",
        )

    fake_team.run.side_effect = fake_run

    monkeypatch.setattr(
        support_service,
        "create_support_workflow",
        lambda model_client: fake_team,
    )

    result = await support_service.process_customer_complaint(
        complaint=complaint,
        model_client=object(),
    )

    ticket_id = result["ticket_id"]
    saved_ticket = get_ticket(ticket_id)

    assert saved_ticket is not None
    assert saved_ticket["original_complaint"] == complaint

    assert saved_ticket["review_status"] == "Pending"

    # Status may be Pending or Escalated based on
    # deterministic escalation business rules.
    assert saved_ticket["ticket_status"] in (
        "Pending",
        "Escalated",
    )

    assert result["execution_order"] == [
        "customer_query_agent",
        "knowledge_base_agent",
        "resolution_agent",
        "log_agent",
    ]

    assert result["stop_reason"] == "Log Agent completed"

    events = list_ticket_audit_history(ticket_id)

    assert any(
        event["action"] == "TICKET_CREATED"
        for event in events
    )


@pytest.mark.asyncio
async def test_empty_complaint_blocked(monkeypatch):
    """Invalid complaints must not start the AI workflow."""

    factory = MagicMock()

    monkeypatch.setattr(
        support_service,
        "create_support_workflow",
        factory,
    )

    with pytest.raises(ValueError):
        await support_service.process_customer_complaint(
            complaint="   ",
            model_client=object(),
        )

    factory.assert_not_called()


@pytest.mark.asyncio
async def test_invalid_agent_order_rejected(
    monkeypatch,
    sample_ticket_data,
):
    """Out-of-order agent responses must be rejected."""

    record = sample_ticket_data["record"].copy()
    messages = make_agent_messages(record)

    # Swap the first two agent responses.
    messages[0], messages[1] = messages[1], messages[0]

    class FakeTeam:
        async def run(self, task):
            return SimpleNamespace(
                messages=messages,
                stop_reason="Completed",
            )

    monkeypatch.setattr(
        support_service,
        "create_support_workflow",
        lambda model_client: FakeTeam(),
    )

    with pytest.raises(RuntimeError, match="execution order"):
        await support_service.process_customer_complaint(
            complaint=sample_ticket_data["complaint"],
            model_client=object(),
        )


@pytest.mark.asyncio
async def test_invalid_log_json_rejected(
    monkeypatch,
    sample_ticket_data,
):
    """Invalid Log Agent JSON must not create a ticket."""

    messages = make_agent_messages(
        sample_ticket_data["record"]
    )

    messages[-1] = TextMessage(
        source="log_agent",
        content="This is not valid JSON",
    )

    class FakeTeam:
        async def run(self, task):
            return SimpleNamespace(
                messages=messages,
                stop_reason="Completed",
            )

    monkeypatch.setattr(
        support_service,
        "create_support_workflow",
        lambda model_client: FakeTeam(),
    )

    with pytest.raises(ValueError, match="valid JSON"):
        await support_service.process_customer_complaint(
            complaint=sample_ticket_data["complaint"],
            model_client=object(),
        )

@pytest.mark.asyncio
async def test_missing_log_agent_response_rejected(
    monkeypatch,
    sample_ticket_data,
):
    """A missing Log Agent response must block ticket creation."""

    messages = make_agent_messages(
        sample_ticket_data["record"]
    )

    # Simulate a workflow that stops before the Log Agent.
    messages = messages[:-1]

    class FakeTeam:
        async def run(self, task):
            return SimpleNamespace(
                messages=messages,
                stop_reason="Maximum messages reached",
            )

    monkeypatch.setattr(
        support_service,
        "create_support_workflow",
        lambda model_client: FakeTeam(),
    )

    with pytest.raises(RuntimeError, match="execution order"):
        await support_service.process_customer_complaint(
            complaint=sample_ticket_data["complaint"],
            model_client=object(),
        )

@pytest.mark.asyncio
async def test_autogen_workflow_failure_does_not_create_ticket(
    monkeypatch,
    sample_ticket_data,
):
    """An AutoGen failure must not create a support ticket."""

    complaint = sample_ticket_data["complaint"]

    class FailingTeam:
        async def run(self, task):
            raise RuntimeError("Simulated AutoGen API failure")

    monkeypatch.setattr(
        support_service,
        "create_support_workflow",
        lambda model_client: FailingTeam(),
    )

    # Track whether ticket creation is attempted.
    create_ticket_mock = MagicMock()

    monkeypatch.setattr(
        support_service,
        "create_ticket",
        create_ticket_mock,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated AutoGen API failure",
    ):
        await support_service.process_customer_complaint(
            complaint=complaint,
            model_client=object(),
        )

    create_ticket_mock.assert_not_called()

@pytest.mark.asyncio
async def test_ticket_persistence_failure_propagates(
    monkeypatch,
    sample_ticket_data,
):
    """Database failure must not return a successful ticket."""

    complaint = sample_ticket_data["complaint"]
    record = sample_ticket_data["record"].copy()

    messages = make_agent_messages(record)

    class FakeTeam:
        async def run(self, task):
            return SimpleNamespace(
                messages=messages,
                stop_reason="Log Agent completed",
            )

    monkeypatch.setattr(
        support_service,
        "create_support_workflow",
        lambda model_client: FakeTeam(),
    )

    def failing_create_ticket(*args, **kwargs):
        raise RuntimeError("Simulated database write failure")

    monkeypatch.setattr(
        support_service,
        "create_ticket",
        failing_create_ticket,
    )

    get_ticket_mock = MagicMock()

    monkeypatch.setattr(
        support_service,
        "get_ticket",
        get_ticket_mock,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated database write failure",
    ):
        await support_service.process_customer_complaint(
            complaint=complaint,
            model_client=object(),
        )

    # The service must not retrieve or return a ticket
    # after the database write has failed.
    get_ticket_mock.assert_not_called()
