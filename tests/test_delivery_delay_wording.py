from services.escalation_service import evaluate_escalation


def test_expected_delivery_ten_days_ago():
    complaint = (
        "My order was expected 10 days ago, "
        "but it has still not arrived."
    )

    record = {
        "urgency": "Medium",
        "sentiment": "Negative",
        "evidence_found": True,
        "confidence_score": 0.95,
        "escalation_signals": [],
    }

    result = evaluate_escalation(complaint, record)

    assert result["escalation_decision"] == "Escalated"
    assert result["requires_human_review"] is True
    assert (
        result["escalation_reason"]
        == "Delivery delayed more than 7 days"
    )


def test_expected_delivery_five_days_ago():
    complaint = (
        "My order was expected 5 days ago, "
        "but it has still not arrived."
    )

    record = {
        "urgency": "Medium",
        "sentiment": "Negative",
        "evidence_found": True,
        "confidence_score": 0.95,
        "escalation_signals": [],
    }

    result = evaluate_escalation(complaint, record)

    assert result["escalation_decision"] == "Pending"
    assert result["requires_human_review"] is False

from services.escalation_service import evaluate_escalation


def test_delivery_expected_10_days_ago_escalates():
    complaint = (
        "My order was supposed to arrive 10 days ago, "
        "but I still haven't received it. "
        "The tracking status hasn't changed."
    )

    record = {
        "urgency": "Medium",
        "sentiment": "Negative",
        "confidence_score": 1.0,
        "evidence_found": True,
        "escalation_signals": [],
    }

    result = evaluate_escalation(complaint, record)

    assert result["escalation_decision"] == "Escalated"
    assert result["escalation_reason"] == (
        "Delivery delayed more than 7 days"
    )
    assert result["requires_human_review"] is True