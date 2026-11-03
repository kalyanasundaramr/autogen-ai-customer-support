
import pytest

from services.human_review_agent_service import (
    collect_human_review,
)


@pytest.mark.asyncio
async def test_collect_approve_decision():
    result = await collect_human_review(
        reviewer="Kalyan",
        action="Approve",
        notes="Policy evidence verified.",
    )

    assert result["reviewer"] == "Kalyan"
    assert result["action"] == "Approve"
    assert result["notes"] == "Policy evidence verified."


@pytest.mark.asyncio
async def test_collect_revision_decision():
    result = await collect_human_review(
        reviewer="Kalyan",
        action="Revise",
        notes="Clarify the refund timeline.",
    )

    assert result["action"] == "Revise"


@pytest.mark.asyncio
async def test_revision_requires_notes():
    with pytest.raises(ValueError):
        await collect_human_review(
            reviewer="Kalyan",
            action="Revise",
            notes="",
        )


@pytest.mark.asyncio
async def test_reject_requires_notes():
    with pytest.raises(ValueError):
        await collect_human_review(
            reviewer="Kalyan",
            action="Reject",
            notes="",
        )
