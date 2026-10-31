
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.db import initialize_database
from services.ticket_query_service import list_pending_review_tickets


def main():
    initialize_database()

    print("\n========== PENDING REVIEW QUERY TEST ==========")

    tickets = list_pending_review_tickets()

    print(f"\nTotal pending review tickets: {len(tickets)}")

    # Test 1: Returned data is a list
    assert isinstance(tickets, list)
    print("PASS: Result is a list")

    # Test 2: Every returned ticket awaits review
    assert all(
        ticket["review_status"] == "Pending"
        for ticket in tickets
    )
    print("PASS: Only pending review tickets returned")

    # Test 3: Previously approved/revised/rejected tickets excluded
    excluded_ids = {
        "TKT-000006",
        "TKT-000007",
        "TKT-000008",
    }

    returned_ids = {
        ticket["ticket_id"]
        for ticket in tickets
    }

    assert not excluded_ids.intersection(returned_ids)
    print("PASS: Previously reviewed tickets excluded")

    # Test 4: Most recent tickets appear first
    ids = [
        int(ticket["ticket_id"].split("-")[1])
        for ticket in tickets
    ]

    assert ids == sorted(ids, reverse=True)
    print("PASS: Tickets ordered newest first")

    print("\n========== PENDING TICKETS ==========")

    for ticket in tickets:
        print(
            f"{ticket['ticket_id']} | "
            f"{ticket['category']} | "
            f"{ticket['urgency']} | "
            f"{ticket['ticket_status']} | "
            f"{ticket['review_status']}"
        )

    print("\n======================================")
    print("ALL TICKET QUERY TESTS PASSED")
    print("======================================")


if __name__ == "__main__":
    main()
