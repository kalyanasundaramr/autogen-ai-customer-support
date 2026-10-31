
from types import SimpleNamespace

import numpy as np
import pytest

from rag import search_kb as rag_search


class FakeIndex:
    """Deterministic FAISS replacement for testing."""

    ntotal = 2
    d = 3

    def search(self, query_vector, top_k):
        assert query_vector.shape == (1, 3)

        scores = np.array(
            [[0.85, 0.25]], dtype=np.float32
        )
        indices = np.array(
            [[0, 1]], dtype=np.int64
        )

        return scores[:, :top_k], indices[:, :top_k]


@pytest.fixture
def mocked_rag(monkeypatch, tmp_path):
    """Mock OpenAI, FAISS loading, and metadata."""

    metadata = [
        {
            "chunk_id": "shipping-001",
            "source": "shipping_policy.md",
            "section": "Delayed Deliveries",
            "content": "Contact support for delayed orders.",
        },
        {
            "chunk_id": "refund-001",
            "source": "refund_policy.md",
            "section": "Refunds",
            "content": "Refunds follow the refund policy.",
        },
    ]

    index_file = tmp_path / "policies.index"
    metadata_file = tmp_path / "metadata.json"

    index_file.touch()

    import json
    metadata_file.write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        rag_search, "INDEX_FILE", index_file
    )
    monkeypatch.setattr(
        rag_search, "METADATA_FILE", metadata_file
    )
    monkeypatch.setattr(
        rag_search.faiss,
        "read_index",
        lambda path: FakeIndex(),
    )

    class FakeEmbeddings:
        def create(self, model, input):
            return SimpleNamespace(
                data=[
                    SimpleNamespace(
                        embedding=[1.0, 0.0, 0.0]
                    )
                ]
            )

    class FakeOpenAI:
        def __init__(self):
            self.embeddings = FakeEmbeddings()

    monkeypatch.setattr(
        rag_search, "OpenAI", FakeOpenAI
    )

    return metadata


def test_relevant_policy_retrieved(mocked_rag):
    result = rag_search.search_kb(
        "My order is delayed",
        top_k=2,
    )

    assert result["evidence_found"] is True
    assert result["requires_escalation"] is False
    assert len(result["matches"]) == 1

    match = result["matches"][0]

    assert match["source"] == "shipping_policy.md"
    assert match["section"] == "Delayed Deliveries"
    assert match["similarity_score"] == 0.85


def test_low_similarity_filtered(mocked_rag):
    result = rag_search.search_kb(
        "Unrelated question",
        top_k=2,
        min_score=0.90,
    )

    assert result["evidence_found"] is False
    assert result["matches"] == []
    assert result["requires_escalation"] is True


def test_empty_query_rejected(mocked_rag):
    with pytest.raises(ValueError):
        rag_search.search_kb("   ")


def test_top_k_limit(mocked_rag):
    result = rag_search.search_kb(
        "Shipping question",
        top_k=1,
    )

    assert len(result["matches"]) == 1


def test_missing_index_rejected(mocked_rag, tmp_path):
    rag_search.INDEX_FILE.unlink()

    with pytest.raises(FileNotFoundError):
        rag_search.search_kb("Shipping question")
