
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

    with pytest.raises(RuntimeError, match="Agent dependencies violated"):
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

    with pytest.raises(
            RuntimeError,
            match="maximum message limit",
        ):
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

@pytest.mark.asyncio
async def test_backward_agent_transition_rejected(
    monkeypatch,
    sample_ticket_data,
):
    """Reject an agent returning after a downstream stage."""

    record = sample_ticket_data["record"].copy()
    messages = make_agent_messages(record)

    # Insert another customer analysis after resolution.
    messages.insert(3, messages[0])

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

    with pytest.raises(
        RuntimeError,
        match="Agent dependencies violated",
    ):
        await support_service.process_customer_complaint(
            sample_ticket_data["complaint"],
            object(),
        )

@pytest.mark.asyncio
async def test_premature_log_agent_rejected(
    monkeypatch,
    sample_ticket_data,
):
    """Reject logging before resolution is complete."""

    record = sample_ticket_data["record"].copy()
    messages = make_agent_messages(record)

    # Simulate logging before resolution.
    messages[2], messages[3] = messages[3], messages[2]

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

    with pytest.raises(
        RuntimeError,
        match="Agent dependencies violated",
    ):
        await support_service.process_customer_complaint(
            sample_ticket_data["complaint"],
            object(),
        )

@pytest.mark.asyncio
async def test_incomplete_log_record_rejected(
    monkeypatch,
    sample_ticket_data,
):
    """Reject incomplete Log Agent JSON before ticket creation."""

    messages = make_agent_messages(
        sample_ticket_data["record"].copy()
    )

    # Valid JSON, but missing required ticket fields.
    messages[-1] = TextMessage(
        source="log_agent",
        content='{"category": "Billing"}',
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

    with pytest.raises((ValueError, KeyError, TypeError)):
        await support_service.process_customer_complaint(
            sample_ticket_data["complaint"],
            object(),
        )

@pytest.mark.asyncio
async def test_max_message_termination_rejected(
    monkeypatch,
    sample_ticket_data,
):
    """Reject a workflow stopped by its message limit."""

    messages = make_agent_messages(
        sample_ticket_data["record"].copy()
    )

    class FakeTeam:
        async def run(self, task):
            return SimpleNamespace(
                messages=messages,
                stop_reason="Maximum number of messages reached",
            )

    monkeypatch.setattr(
        support_service,
        "create_support_workflow",
        lambda model_client: FakeTeam(),
    )

    with pytest.raises(RuntimeError):
        await support_service.process_customer_complaint(
            sample_ticket_data["complaint"],
            object(),
        )


@pytest.mark.asyncio
async def test_missing_log_agent_without_message_limit(
    monkeypatch,
    sample_ticket_data,
):
    """Reject an incomplete workflow without a message-limit error."""

    messages = make_agent_messages(
        sample_ticket_data["record"].copy()
    )[:-1]

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

    with pytest.raises(
        RuntimeError,
        match="Workflow incomplete",
    ):
        await support_service.process_customer_complaint(
            sample_ticket_data["complaint"],
            object(),
        )
@pytest.mark.asyncio
async def test_agent_order_retry_recovers(
    monkeypatch,
    sample_ticket_data,
):
    """Retry an invalid agent sequence and persist only once."""

    record = sample_ticket_data["record"].copy()
    valid_messages = make_agent_messages(record)

    invalid_messages = valid_messages.copy()
    invalid_messages[1], invalid_messages[2] = (
        invalid_messages[2],
        invalid_messages[1],
    )

    attempts = []
    saved_tickets = []

    class FakeTeam:
        def __init__(self, attempt_number):
            self.attempt_number = attempt_number

        async def run(self, task):
            assert task == sample_ticket_data["complaint"]
            attempts.append(self.attempt_number)

            return SimpleNamespace(
                messages=(
                    invalid_messages
                    if self.attempt_number == 1
                    else valid_messages
                ),
                stop_reason="Log Agent completed",
            )

    def fake_create_workflow(model_client):
        return FakeTeam(len(attempts) + 1)

    monkeypatch.setattr(
        support_service,
        "create_support_workflow",
        fake_create_workflow,
    )

    original_create_ticket = support_service.create_ticket

    def tracked_create_ticket(*args, **kwargs):
        ticket_id = original_create_ticket(*args, **kwargs)
        saved_tickets.append(ticket_id)
        return ticket_id

    monkeypatch.setattr(
        support_service,
        "create_ticket",
        tracked_create_ticket,
    )

    result = await support_service.process_customer_complaint(
        complaint=sample_ticket_data["complaint"],
        model_client=object(),
    )

    assert attempts == [1, 2]
    assert len(saved_tickets) == 1
    assert result["ticket_id"] == saved_tickets[0]
    assert result["execution_order"] == [
        "customer_query_agent",
        "knowledge_base_agent",
        "resolution_agent",
        "log_agent",
    ]
@pytest.mark.asyncio
async def test_agent_order_retry_exhausted(
    monkeypatch,
    sample_ticket_data,
):
    """Two invalid attempts must fail without saving a ticket."""

    record = sample_ticket_data["record"].copy()
    messages = make_agent_messages(record)

    # Incorrect order: Resolution before Knowledge Base.
    messages[1], messages[2] = messages[2], messages[1]

    attempts = []
    create_ticket_mock = MagicMock()

    class FakeTeam:
        async def run(self, task):
            attempts.append(task)
            return SimpleNamespace(
                messages=messages,
                stop_reason="Log Agent completed",
            )

    monkeypatch.setattr(
        support_service,
        "create_support_workflow",
        lambda model_client: FakeTeam(),
    )

    monkeypatch.setattr(
        support_service,
        "create_ticket",
        create_ticket_mock,
    )

    with pytest.raises(
        RuntimeError,
        match="Agent dependencies violated",
    ):
        await support_service.process_customer_complaint(
            complaint=sample_ticket_data["complaint"],
            model_client=object(),
        )

    assert len(attempts) == 2
    create_ticket_mock.assert_not_called()