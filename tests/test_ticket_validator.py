
import copy
import sys
from pathlib import Path

from pydantic import ValidationError

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.ticket_validator import validate_ticket_record


VALID_RECORD = {
    "category": "Billing",
    "urgency": "High",
    "sentiment": "Very Angry",
    "language": "English",
    "summary": "Customer reports three charges for one order.",
    "escalation_signals": ["Legal threat"],
    "evidence_found": True,
    "policy_sources": [
        "billing_policy.md | Duplicate Charges"
    ],
    "proposed_response": (
        "Please provide your order ID and transaction "
        "references for human billing support review."
    ),
    "escalation_decision": "Pending",
    "escalation_reason": None,
    "ticket_status": "Pending",
    "review_status": "Pending",
}


def expect_invalid(name, changes):
    record = copy.deepcopy(VALID_RECORD)
    record.update(changes)

    try:
        validate_ticket_record(record)
    except ValidationError:
        print(f"PASS: {name} rejected")
        return

    raise AssertionError(
        f"FAIL: {name} was incorrectly accepted"
    )


def main():
    print("\n========== PYDANTIC VALIDATION TEST ==========")

    validated = validate_ticket_record(
        copy.deepcopy(VALID_RECORD)
    )

    assert validated["category"] == "Billing"
    assert validated["urgency"] == "High"
    assert validated["evidence_found"] is True

    print("PASS: Valid ticket accepted")

    expect_invalid(
        "Invalid category",
        {"category": "Finance"},
    )

    expect_invalid(
        "Invalid urgency",
        {"urgency": "Critical"},
    )

    expect_invalid(
        "Invalid sentiment",
        {"sentiment": "Extremely Upset"},
    )

    expect_invalid(
        "Blank proposed response",
        {"proposed_response": "   "},
    )

    expect_invalid(
        "Incorrect evidence type",
        {"evidence_found": "yes"},
    )

    expect_invalid(
        "Invalid review status",
        {"review_status": "Approved"},
    )

    expect_invalid(
        "Blank policy source",
        {"policy_sources": ["   "]},
    )

    extra_record = copy.deepcopy(VALID_RECORD)
    extra_record["invented_ticket_id"] = "TKT-999999"

    try:
        validate_ticket_record(extra_record)
    except ValidationError:
        print("PASS: Unexpected field rejected")
    else:
        raise AssertionError(
            "FAIL: Unexpected field was accepted"
        )

    print("\n========================================")
    print("ALL PYDANTIC VALIDATION TESTS PASSED")
    print("========================================")


if __name__ == "__main__":
    main()
