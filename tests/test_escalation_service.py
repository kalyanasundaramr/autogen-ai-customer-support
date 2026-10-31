
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.escalation_service import evaluate_escalation


def main():
    test_cases = [
        {
            "name": "Normal shipping delay",
            "complaint": "My order is one day late.",
            "urgency": "Medium",
            "sentiment": "Negative",
            "evidence_found": True,
            "expected": "Pending",
        },
        {
            "name": "High urgency",
            "complaint": "I need help with my order immediately.",
            "urgency": "High",
            "sentiment": "Negative",
            "evidence_found": True,
            "expected": "Escalated",
        },
        {
            "name": "Triple charge and legal threat",
            "complaint": (
                "I was charged three times for one order! "
                "If you don't fix it, I will take legal action."
            ),
            "urgency": "High",
            "sentiment": "Very Angry",
            "evidence_found": True,
            "expected": "Escalated",
        },
        {
            "name": "Unsupported gift card request",
            "complaint": (
                "Can you provide 500 customized corporate "
                "gift cards for our employees?"
            ),
            "urgency": "Low",
            "sentiment": "Neutral",
            "evidence_found": False,
            "expected": "Escalated",
        },
        {
            "name": "Account security concern",
            "complaint": (
                "Someone hacked my account and gained "
                "unauthorized access."
            ),
            "urgency": "Medium",
            "sentiment": "Negative",
            "evidence_found": True,
            "expected": "Escalated",
        },
        {
            "name": "Delivery delayed 10 days",
            "complaint": (
                "My delivery is delayed by 10 days "
                "beyond the estimated delivery date."
            ),
            "urgency": "Medium",
            "sentiment": "Negative",
            "evidence_found": True,
            "expected": "Escalated",
        },
        {
            "name": "Normal password reset",
            "complaint": (
                "I forgot my password. "
                "How can I reset it?"
            ),
            "urgency": "Low",
            "sentiment": "Neutral",
            "evidence_found": True,
            "expected": "Pending",
        },
        {
            "name": "Very angry customer",
            "complaint": (
                "My product arrived damaged "
                "and I'm extremely disappointed."
            ),
            "urgency": "Medium",
            "sentiment": "Very Angry",
            "evidence_found": True,
            "expected": "Escalated",
        },
    ]

    print("\n========== ESCALATION RULE TESTS ==========")

    passed = 0

    for index, case in enumerate(test_cases, start=1):
        record = {
            "urgency": case["urgency"],
            "sentiment": case["sentiment"],
            "evidence_found": case["evidence_found"],
            "escalation_signals": [],
        }

        result = evaluate_escalation(
            case["complaint"],
            record,
        )

        actual = result["escalation_decision"]
        expected = case["expected"]

        status = "PASS" if actual == expected else "FAIL"

        print(f"\n[{index}] {case['name']}")
        print(f"Expected: {expected}")
        print(f"Actual:   {actual}")
        print(f"Result:   {status}")

        if result["escalation_reason"]:
            print(
                "Reason:",
                result["escalation_reason"],
            )

        if actual == expected:
            passed += 1

    print("\n========== TEST SUMMARY ==========")
    print(f"Passed: {passed}/{len(test_cases)}")

    assert passed == len(test_cases), (
        "One or more escalation rules failed."
    )

    print("ALL ESCALATION TESTS PASSED")


if __name__ == "__main__":
    main()
