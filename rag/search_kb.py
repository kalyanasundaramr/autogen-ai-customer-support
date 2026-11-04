
import json
import os
from functools import lru_cache
from pathlib import Path

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI


BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_DIR = BASE_DIR / "data" / "faiss_index"

INDEX_FILE = INDEX_DIR / "policies.index"
METADATA_FILE = INDEX_DIR / "metadata.json"

load_dotenv(BASE_DIR / ".env")

EMBEDDING_MODEL = os.getenv(
    "OPENAI_EMBEDDING_MODEL",
    "text-embedding-3-small"
)
SIMILARITY_THRESHOLD = 0.40


@lru_cache(maxsize=1)
def load_knowledge_base():
    """Load FAISS and metadata once per application process."""

    if not INDEX_FILE.exists() or not METADATA_FILE.exists():
        raise FileNotFoundError(
            "FAISS index missing. Run vector_store.py first."
        )

    index = faiss.read_index(str(INDEX_FILE))

    metadata = json.loads(
        METADATA_FILE.read_text(encoding="utf-8")
    )

    if index.ntotal != len(metadata):
        raise RuntimeError(
            "FAISS index and metadata count mismatch."
        )

    return index, metadata


@lru_cache(maxsize=1)
def get_openai_client():
    """Reuse the OpenAI client across queries."""
    return OpenAI()


def search_kb(
    query: str,
    top_k: int = 5,
    min_score: float = SIMILARITY_THRESHOLD
) -> dict:
    """Search policy documents using cached FAISS resources."""

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    if not INDEX_FILE.exists() or not METADATA_FILE.exists():
        raise FileNotFoundError(
            "FAISS index missing. Run vector_store.py first."
        )

    index, metadata = load_knowledge_base()
    client = get_openai_client()

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query.strip()
    )

    query_vector = np.asarray(
        [response.data[0].embedding],
        dtype=np.float32
    )

    if query_vector.shape[1] != index.d:
        raise RuntimeError(
            "Query embedding dimensions do not match the index."
        )

    faiss.normalize_L2(query_vector)

    scores, indices = index.search(
        query_vector,
        min(top_k, index.ntotal)
    )

    matches = []

    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue

        if float(score) < min_score:
            continue

        chunk = metadata[int(idx)]

        matches.append({
            "chunk_id": chunk["chunk_id"],
            "source": chunk["source"],
            "section": chunk["section"],
            "content": chunk["content"],
            "similarity_score": round(float(score), 4)
        })

    
    # Expand retrieval for refund and return complaints.
    # Use the existing query embedding; no second API call.
    query_lower = query.casefold()

    is_refund_query = any(
        term in query_lower
        for term in ("refund", "return", "exchange")
    )

    if is_refund_query and top_k == 5 and min_score == SIMILARITY_THRESHOLD:
        expanded_scores, expanded_indices = index.search(
            query_vector,
            min(10, index.ntotal),
        )

        expanded_matches = []

        for score, idx in zip(
            expanded_scores[0],
            expanded_indices[0],
        ):
            if idx < 0 or float(score) < 0.35:
                continue

            chunk = metadata[int(idx)]

            expanded_matches.append({
                "chunk_id": chunk["chunk_id"],
                "source": chunk["source"],
                "section": chunk["section"],
                "content": chunk["content"],
                "similarity_score": round(float(score), 4),
            })

        matches = expanded_matches

    return {
        "query": query,
        "evidence_found": bool(matches),
        "matches": matches,
        "similarity_threshold": (
            0.35 if is_refund_query
            and top_k == 5
            and min_score == SIMILARITY_THRESHOLD
            else min_score
        ),
        "requires_escalation": not bool(matches),
    }



if __name__ == "__main__":
    question = "My order is delayed. What should I do?"

    result = search_kb(question, top_k=3)

    print(f"\nQuestion: {result['query']}")
    print(f"Matches found: {len(result['matches'])}")

    for match in result["matches"]:
        print("-" * 50)
        print(f"Source: {match['source']}")
        print(f"Section: {match['section']}")
        print(f"Similarity: {match['similarity_score']}")
        print(match["content"])
