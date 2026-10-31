
import json
import os
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


def search_kb(
    query: str,
    top_k: int = 5,
    min_score: float = SIMILARITY_THRESHOLD
) -> dict:
    """
    Search the company policy knowledge base.

    Args:
        query: Customer support question.
        top_k: Maximum number of matching passages.

    Returns:
        Matching policy passages with sources and scores.
    """

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

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

    client = OpenAI()

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

    return {
        "query": query,
        "evidence_found": bool(matches),
        "matches": matches,
        "similarity_threshold": SIMILARITY_THRESHOLD,
        "requires_escalation": not bool(matches)
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
