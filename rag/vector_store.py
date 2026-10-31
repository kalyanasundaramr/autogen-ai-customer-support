
import json
from pathlib import Path

import faiss
import numpy as np

from document_loader import load_documents
from text_chunker import chunk_documents
from embedding_service import generate_embeddings


BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_DIR = BASE_DIR / "data" / "faiss_index"

INDEX_FILE = INDEX_DIR / "policies.index"
METADATA_FILE = INDEX_DIR / "metadata.json"


def build_vector_store():
    """Build and persist the FAISS policy index."""

    documents = load_documents()
    chunks = chunk_documents(documents)

    if not chunks:
        raise ValueError("No policy chunks available.")

    print(f"Documents loaded: {len(documents)}")
    print(f"Chunks prepared: {len(chunks)}")

    embedded_chunks = generate_embeddings(chunks)

    vectors = np.asarray(
        [item["embedding"] for item in embedded_chunks],
        dtype=np.float32
    )

    # Normalize vectors for cosine similarity.
    faiss.normalize_L2(vectors)

    dimensions = vectors.shape[1]
    index = faiss.IndexFlatIP(dimensions)
    index.add(vectors)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(INDEX_FILE))

    metadata = [
        {
            "chunk_id": item["chunk_id"],
            "source": item["source"],
            "section": item["section"],
            "content": item["content"]
        }
        for item in embedded_chunks
    ]

    METADATA_FILE.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"FAISS vectors stored: {index.ntotal}")
    print(f"Vector dimensions: {dimensions}")
    print(f"Index saved: {INDEX_FILE}")
    print(f"Metadata saved: {METADATA_FILE}")


if __name__ == "__main__":
    build_vector_store()
