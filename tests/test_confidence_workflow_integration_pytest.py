
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from autogen_agentchat.messages import TextMessage

from services.support_service import process_customer_complaint
from services.ticket_service import get_ticket


@pytest.mark.asyncio
async def test_confidence_from_log_agent_saved_to_sqlite(
    sample_ticket_data,
):
    """Verify Log Agent confidence reaches SQLite."""

    record = sample_ticket_data["record"].copy()
    record["confidence_score"] = 0.85
    record["confidence_explanation"] = (
        "Shipping policy directly supports the proposed response."
    )

    agent_names = [
        "customer_query_agent",
        "knowledge_base_agent",
        "resolution_agent",
        "log_agent",
    ]

    messages = [
        TextMessage(
            source=name,
            content=(
                json.dumps(record)
                if name == "log_agent"
                else "Mock agent response"
            ),
        )
        for name in agent_names
    ]

    mock_result = SimpleNamespace(
        messages=messages,
        stop_reason="Log Agent completed",
    )

    class MockTeam:
        async def run(self, task):
            return mock_result

    with patch(
        "services.support_service.create_support_workflow",
        return_value=MockTeam(),
    ):
        result = await process_customer_complaint(
            complaint=sample_ticket_data["complaint"],
            model_client=None,
        )

    saved_ticket = get_ticket(result["ticket_id"])

    assert saved_ticket is not None
    assert saved_ticket["confidence_score"] == 0.85
    assert saved_ticket["confidence_explanation"] == (
        "Shipping policy directly supports the proposed response."
    )
    assert saved_ticket["ticket_status"] == "Pending"
    assert result["execution_order"] == agent_names
