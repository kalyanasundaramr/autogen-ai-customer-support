
import re

from document_loader import load_documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Split Markdown documents into section-based chunks.

    Preserve the source filename, section title,
    and chunk identifier.
    """
    chunks = []

    for document in documents:
        source = document["source"]
        content = document["content"]

        sections = re.split(
            r"(?=^##\s+)",
            content,
            flags=re.MULTILINE
        )

        chunk_number = 0

        for section in sections:
            section = section.strip()

            if not section:
                continue

            # Skip the document's standalone title.
            if section.startswith("# ") and "\n" not in section:
                continue

            lines = section.splitlines()

            if lines[0].startswith("## "):
                section_title = lines[0][3:].strip()
            else:
                section_title = "Introduction"

            chunk_number += 1

            chunks.append({
                "chunk_id": (
                    f"{source.replace('.md', '')}_"
                    f"{chunk_number:03d}"
                ),
                "source": source,
                "section": section_title,
                "content": section
            })

    return chunks


if __name__ == "__main__":
    documents = load_documents()
    chunks = chunk_documents(documents)

    print(f"\nTotal documents: {len(documents)}")
    print(f"Total chunks created: {len(chunks)}")

    print("\nSample chunks:")

    for chunk in chunks[:5]:
        print("-" * 50)
        print(f"ID: {chunk['chunk_id']}")
        print(f"Source: {chunk['source']}")
        print(f"Section: {chunk['section']}")
        print(f"Characters: {len(chunk['content'])}")
        print(chunk["content"][:150])
