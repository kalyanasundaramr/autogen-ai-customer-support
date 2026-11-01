
import os
import sys
import tempfile
from pathlib import Path

# Set the test database path before application imports.
BASE_DIR = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(BASE_DIR))

_test_directory = tempfile.TemporaryDirectory(
    prefix="autogen_support_tests_"
)

TEST_DB_PATH = (
    Path(_test_directory.name) / "test_support_tickets.db"
)

# Override the application's default database path.
os.environ["SUPPORT_DB_PATH"] = str(TEST_DB_PATH)

import pytest
from database.db import DB_PATH, initialize_database


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Initialize an isolated SQLite database for pytest.

    Existing application tickets and audit records
    must remain untouched.
    """
    assert DB_PATH.resolve() == TEST_DB_PATH.resolve(), (
        "Test database isolation failed."
    )

    initialize_database()

    yield

    # TemporaryDirectory cleans up when the process exits.

@pytest.fixture
def sample_ticket_data():
    """Reusable fictional customer complaint and AI output."""

    return {
        "complaint": "My test order has not arrived yet.",
        "record": {
            "category": "Shipping",
            "urgency": "Medium",
            "sentiment": "Neutral",
            "language": "English",
            "summary": "Customer reports a delayed test order.",
            "escalation_signals": [],
            "evidence_found": True,
            "policy_sources": [
                "shipping_policy.md | Delayed Deliveries"
            ],
            
            "proposed_response": (
                "Dear Customer, please provide your order ID "
                "so our support team can investigate."
            ),
            "confidence_score": 0.90,
            "confidence_explanation": (
                "Relevant shipping policy evidence supports "
                "the proposed response."
            ),
            "escalation_decision": "No",

            "escalation_reason": None,
            "ticket_status": "Pending",
            "review_status": "Pending",
        },
    }


@pytest.fixture
def sample_ticket(sample_ticket_data):
    """Create a new test ticket in the isolated database."""

    from services.ticket_service import create_ticket

    ticket_id = create_ticket(
        sample_ticket_data["complaint"],
        sample_ticket_data["record"],
    )

    return ticket_id
