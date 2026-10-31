
import os

from dotenv import load_dotenv
from openai import OpenAI

from document_loader import load_documents
from text_chunker import chunk_documents


load_dotenv()

EMBEDDING_MODEL = os.getenv(
    "OPENAI_EMBEDDING_MODEL",
    "text-embedding-3-small"
)


def generate_embeddings(chunks: list[dict]) -> list[dict]:
    """
    Generate OpenAI embeddings for policy chunks.

    Returns each chunk with its embedding vector.
    """
    if not chunks:
        return []

    client = OpenAI()

    texts = [chunk["content"] for chunk in chunks]

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )

    embeddings_by_index = {
        item.index: item.embedding
        for item in response.data
    }

    if len(embeddings_by_index) != len(chunks):
        raise RuntimeError("Embedding count mismatch")

    results = []

    for index, chunk in enumerate(chunks):
        results.append({
            **chunk,
            "embedding": embeddings_by_index[index]
        })

    return results


if __name__ == "__main__":
    documents = load_documents()
    chunks = chunk_documents(documents)

    print(f"Documents loaded: {len(documents)}")
    print(f"Chunks prepared: {len(chunks)}")

    embedded_chunks = generate_embeddings(chunks)

    print(f"Embeddings generated: {len(embedded_chunks)}")

    if embedded_chunks:
        print(
            "Embedding dimensions:",
            len(embedded_chunks[0]["embedding"])
        )

    print("Embedding generation successful!")
