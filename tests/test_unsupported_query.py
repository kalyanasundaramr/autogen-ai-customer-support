
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "rag"))

from search_kb import search_kb


query = "Can you provide 500 customized corporate gift cards for our employees?"

result = search_kb(query, top_k=3)

print("\nQuestion:", query)
print("Matches found:", len(result["matches"]))

for match in result["matches"]:
    print("-" * 50)
    print("Source:", match["source"])
    print("Section:", match["section"])
    print("Similarity:", match["similarity_score"])
