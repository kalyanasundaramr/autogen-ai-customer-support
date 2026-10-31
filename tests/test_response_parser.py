
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.response_parser import extract_customer_response


def expect_invalid(test_name, agent_output):
    try:
        extract_customer_response(agent_output)
    except ValueError:
        print(f"PASS: {test_name}")
    else:
        raise AssertionError(
            f"FAIL: {test_name} was incorrectly accepted"
        )


def main():
    print("\n========== RESPONSE PARSER TEST ==========")

    # Test 1: Valid Resolution Agent output
    agent_output = """
Customer Response:
Dear Customer,

We sincerely apologize for the shipping delay.
Please share your order ID so our support team
can review the shipment status.

Thank you,
Customer Support Team

Supporting Policies:
- shipping_policy.md | Delayed Deliveries

Recommended Action:
Request the customer's order ID.

Human Review Recommended:
Yes

Reason:
The revised draft requires human approval.
"""

    response = extract_customer_response(agent_output)

    assert "Dear Customer" in response
    assert "shipping delay" in response
    assert "Supporting Policies:" not in response
    assert "Recommended Action:" not in response
    assert "Human Review Recommended:" not in response

    print("PASS: Customer response extracted")
    print("PASS: Internal sections excluded")

    # Test 2: Missing customer response heading
    expect_invalid(
        "Missing Customer Response heading rejected",
        "Supporting Policies:\n- shipping_policy.md",
    )

    # Test 3: Empty customer response
    expect_invalid(
        "Empty customer response rejected",
        """
Customer Response:

Supporting Policies:
- shipping_policy.md
""",
    )

    # Test 4: Invalid input type
    expect_invalid(
        "Non-string input rejected",
        None,
    )

    # Test 5: Internal section leaked into response
    expect_invalid(
        "Internal section leakage rejected",
        """
Customer Response:
Dear Customer,
Please provide your order ID.

Recommended Action:
Escalate to support.
""",
    )

    print("\n========== EXTRACTED RESPONSE ==========")
    print(response)

    print("\n======================================")
    print("ALL RESPONSE PARSER TESTS PASSED")
    print("======================================")


if __name__ == "__main__":
    main()
