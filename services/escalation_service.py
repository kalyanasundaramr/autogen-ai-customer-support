
import re


def evaluate_escalation(
    original_complaint: str,
    record: dict
) -> dict:
    """
    Apply deterministic escalation rules.

    Returns:
        {
            "escalation_decision": "Escalated" or "Pending",
            "escalation_reason": str or None,
            "requires_human_review": bool
        }
    """

    complaint = original_complaint.lower()
    urgency = str(record.get("urgency", "")).lower()
    sentiment = str(record.get("sentiment", "")).lower()

    signals = record.get("escalation_signals") or []
    if not isinstance(signals, list):
        signals = []

    signal_text = " ".join(str(s) for s in signals).lower()

    combined_text = complaint + " " + signal_text

    reasons = []
    
    # Confidence-based escalation.
    # The threshold is a project-defined heuristic.
    confidence_threshold = 0.70
    confidence_score = record.get("confidence_score")

    if confidence_score is None:
        reasons.append("AI confidence score unavailable")
    elif (
        isinstance(confidence_score, bool)
        or not isinstance(confidence_score, (int, float))
        or not (0.0 <= confidence_score <= 1.0)
    ):
        reasons.append("Invalid AI confidence score")
    elif confidence_score < confidence_threshold:
        reasons.append(
            f"Low AI confidence ({confidence_score:.2f} "
            f"< {confidence_threshold:.2f})"
        )


    if urgency == "high":
        reasons.append("High urgency")

    if sentiment in ("very angry", "very negative"):
        reasons.append("Very angry customer sentiment")

    legal_terms = [
        "legal action",
        "lawsuit",
        "sue you",
        "lawyer",
        "attorney",
        "consumer court",
        "legal threat",
    ]

    if any(term in combined_text for term in legal_terms):
        reasons.append("Legal threat detected")

    payment_terms = [
        "charged twice",
        "charged three times",
        "charged multiple times",
        "duplicate charge",
        "double charged",
        "triple charged",
        "unauthorized charge",
        "billing dispute",
        "payment dispute",
    ]

    if any(term in combined_text for term in payment_terms):
        reasons.append("Payment or billing dispute")

    security_terms = [
        "fraud",
        "fraudulent",
        "hacked",
        "unauthorized access",
        "account compromised",
        "identity theft",
    ]

    if any(term in combined_text for term in security_terms):
        reasons.append("Fraud or account security concern")

    if record.get("evidence_found") is not True:
        reasons.append("Insufficient knowledge-base evidence")

    # Match explicit delays exceeding 7 days.
    delay_pattern = (
        r"(?:delayed|delay|late|overdue)"
        r".{0,50}?"
        r"\b(\d+)\s*(?:calendar\s+|business\s+)?days?\b"
    )

    delay_match = re.search(delay_pattern, complaint)

    if delay_match and int(delay_match.group(1)) > 7:
        reasons.append("Delivery delayed more than 7 days")

    # Also handle "10 days late" wording.
    late_pattern = (
        r"\b(\d+)\s*(?:calendar\s+|business\s+)?days?"
        r"\s+(?:late|overdue|delayed)\b"
    )

    late_match = re.search(late_pattern, complaint)

    if late_match and int(late_match.group(1)) > 7:
        if "Delivery delayed more than 7 days" not in reasons:
            reasons.append("Delivery delayed more than 7 days")
    # Detect deliveries expected more than 7 days ago
    # that have still not arrived.
    

    expected_ago_pattern = (
    r"\b(?:order|package|parcel|delivery|shipment)\b"
    r".{0,100}?"
    r"\b(?:expected|due|scheduled|supposed\s+to\s+arrive)\b"
    r".{0,60}?"
    r"(\d+)\s+days?\s+ago\b"
)
    
    not_delivered_pattern = (
        r"\b(?:"
        r"not arrived|"
        r"not delivered|"
        r"not been delivered|"
        r"still not arrived|"
        r"still not delivered|"
        r"hasn't arrived|"
        r"has not arrived|"
        r"hasn't been delivered|"
        r"has not been delivered|"
        r"haven't received|"
        r"have not received"
        r")\b"
    )


    expected_match = re.search(expected_ago_pattern, complaint)

    if (
        expected_match
        and int(expected_match.group(1)) > 7
        and re.search(not_delivered_pattern, complaint)
    ):
        if "Delivery delayed more than 7 days" not in reasons:
            reasons.append("Delivery delayed more than 7 days")

    if reasons:
        return {
            "escalation_decision": "Escalated",
            "escalation_reason": "; ".join(reasons),
            "requires_human_review": True,
        }

    return {
        "escalation_decision": "Pending",
        "escalation_reason": None,
        "requires_human_review": False,
    }
