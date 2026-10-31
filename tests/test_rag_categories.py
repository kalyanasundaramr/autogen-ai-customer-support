
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "rag"))

from search_kb import search_kb


test_cases = [
    (
        "Shipping",
        "My order is delayed. What should I do?",
        "shipping_policy.md"
    ),
    (
        "Refund",
        "Can I return my shoes within 15 days?",
        "refund_policy.md"
    ),
    (
        "Account",
        "I forgot my password. How do I reset it?",
        "account_and_login.md"
    ),
    (
        "Product",
        "My blender arrived damaged. Can I get a replacement?",
        "product_faq.md"
    ),
    (
        "Billing",
        "I was charged three times for one order.",
        "billing_policy.md"
    )
]


for category, question, expected_source in test_cases:
    result = search_kb(question, top_k=5)
    matches = result["matches"]

    source_found = any(
        match["source"] == expected_source
        for match in matches
    )

    print("\n" + "=" * 60)
    print("Category:", category)
    print("Question:", question)
    print("Matches found:", len(matches))
    print("Expected source:", expected_source)
    print("Result:", "PASS" if source_found else "REVIEW")

    for match in matches:
        print(
            "  ",
            match["source"],
            "|",
            match["section"],
            "| Score:",
            match["similarity_score"]
        )
