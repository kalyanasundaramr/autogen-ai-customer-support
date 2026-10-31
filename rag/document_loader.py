
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"


def load_documents() -> list[dict]:
    """
    Load Markdown policy documents from the knowledge base.

    Returns:
        List of dictionaries containing source and content.
    """
    documents = []

    for file_path in sorted(KNOWLEDGE_BASE_DIR.glob("*.md")):
        content = file_path.read_text(encoding="utf-8-sig")

        if not content.strip():
            print(f"Skipping empty document: {file_path.name}")
            continue

        documents.append({
            "source": file_path.name,
            "content": content.strip()
        })

    return documents


if __name__ == "__main__":
    documents = load_documents()

    print(f"\nTotal documents loaded: {len(documents)}")

    for document in documents:
        print(
            f"Source: {document['source']} | "
            f"Characters: {len(document['content'])}"
        )
