
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rag.search_kb import search_kb


QUESTIONS_FILE = PROJECT_ROOT / "evaluation" / "questions.json"
RESULTS_DIR = PROJECT_ROOT / "data" / "evaluation"


def evaluate():
    questions = json.loads(
        QUESTIONS_FILE.read_text(encoding="utf-8")
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    reciprocal_ranks = []
    hits = 0

    for item in questions:
        question_id = item["id"]
        question = item["question"]
        expected_source = item["expected_source"]
        expected_section = item["expected_section"]

        # Disable similarity filtering for ranking evaluation.
        response = search_kb(
            query=question,
            top_k=5,
            min_score=-1.0
        )

        matches = response["matches"]

        rank = None

        for position, match in enumerate(matches, start=1):
            if (
                match["source"] == expected_source
                and match["section"] == expected_section
            ):
                rank = position
                break

        hit = rank is not None
        reciprocal_rank = 1.0 / rank if hit else 0.0

        hits += int(hit)
        reciprocal_ranks.append(reciprocal_rank)

        results.append({
            "id": question_id,
            "question": question,
            "expected_source": expected_source,
            "expected_section": expected_section,
            "hit_at_5": hit,
            "rank": rank,
            "reciprocal_rank": reciprocal_rank,
            "retrieved_sections": [
                f"{m['source']}::{m['section']}"
                for m in matches
            ]
        })

        status = "PASS" if hit else "FAIL"
        print(f"{question_id}: {status} | rank={rank}")

    total = len(results)

    hit_rate = hits / total if total else 0.0
    mrr = (
        sum(reciprocal_ranks) / total
        if total else 0.0
    )

    summary = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "total_questions": total,
        "hit_rate_at_5": round(hit_rate, 4),
        "mrr_at_5": round(mrr, 4),
        "results": results
    }

    json_file = RESULTS_DIR / "rag_evaluation.json"
    json_file.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8"
    )

    csv_file = RESULTS_DIR / "rag_evaluation.csv"

    with csv_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "id",
                "question",
                "expected_source",
                "expected_section",
                "hit_at_5",
                "rank",
                "reciprocal_rank",
                "retrieved_sections"
            ]
        )
        writer.writeheader()

        for result in results:
            writer.writerow(result)

    print("\n" + "=" * 45)
    print("RAG RETRIEVAL EVALUATION")
    print("=" * 45)
    print(f"Questions       : {total}")
    print(f"Hits@5          : {hits}/{total}")
    print(f"Hit Rate@5      : {hit_rate:.2%}")
    print(f"MRR@5           : {mrr:.4f}")
    print(f"JSON Report     : {json_file}")
    print(f"CSV Report      : {csv_file}")


if __name__ == "__main__":
    evaluate()
