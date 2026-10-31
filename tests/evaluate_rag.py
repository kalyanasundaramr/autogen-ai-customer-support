
from rag.search_kb import search_kb

test_cases = [
    {
        "question": "My order has not arrived. What should I do?",
        "expected_source": "shipping_policy.md",
    },
    {
        "question": "How can I request a refund for my purchase?",
        "expected_source": "refund_policy.md",
    },
    {
        "question": "I forgot my password and cannot log in.",
        "expected_source": "account_and_login.md",
    },
    {
        "question": "I was charged twice for my order.",
        "expected_source": "billing_policy.md",
    },
    {
        "question": "Is this product covered under warranty?",
        "expected_source": "product_faq.md",
    },
]

passed = 0

for number, test in enumerate(test_cases, start=1):
    result = search_kb(
        test["question"],
        top_k=5,
        min_score=0.40,
    )

    sources = [
        match["source"]
        for match in result["matches"]
    ]

    success = test["expected_source"] in sources

    if success:
        passed += 1

    print(f"\nTest {number}: {'PASS' if success else 'FAIL'}")
    print(f"Question: {test['question']}")
    print(f"Expected: {test['expected_source']}")
    print(f"Retrieved: {sources}")

print("\n" + "=" * 45)
print(f"RAG Retrieval Hit Rate@5: {passed}/{len(test_cases)}")
print(f"Accuracy: {passed / len(test_cases) * 100:.1f}%")
