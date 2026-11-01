
import pytest

from services.escalation_service import evaluate_escalation


@pytest.mark.parametrize(
    "confidence_score, expected_status",
    [
        (0.90, "Pending"),
        (0.70, "Pending"),
        (0.69, "Escalated"),
        (0.30, "Escalated"),
        (None, "Escalated"),
        (-0.1, "Escalated"),
        (1.5, "Escalated"),
        ("invalid", "Escalated"),
    ],
)
def test_confidence_escalation(
    confidence_score,
    expected_status,
):
    record = {
        "urgency": "Low",
        "sentiment": "Neutral",
        "escalation_signals": [],
        "evidence_found": True,
        "confidence_score": confidence_score,
    }

    result = evaluate_escalation(
        "Please explain your return policy.",
        record,
    )

    assert result["escalation_decision"] == expected_status
    assert result["requires_human_review"] == (
        expected_status == "Escalated"
    )

    if expected_status == "Escalated":
        assert result["escalation_reason"]
    else:
        assert result["escalation_reason"] is None
