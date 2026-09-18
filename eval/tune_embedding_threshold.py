"""
Sweep EMBEDDING_THRESHOLD for the danger gate's embedding-similarity path.

Re-run this after any change to DANGER_CATEGORIES or
_build_embedding_reference(), and update the table in
docs/adr/0003-danger-gate-matching.md with the new numbers.

Usage:
    python eval/tune_embedding_threshold.py

Requires:
    eval/danger_sign_eval_100.csv   (danger set — has ground-truth answers)
    eval/negative_set_100.csv       (ordinary health questions, no danger)
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.safety.danger_gate import (
    _load_embedder,
    _embedding_match,
    _danger_phrase_embeddings,
    EMBEDDING_THRESHOLD,
)


THRESHOLDS_TO_SWEEP = [0.86, 0.88, 0.90, 0.92, 0.94, 0.96, 0.98]


def load_queries(csv_path: str) -> list[str]:
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # adjust column name if the CSV uses a different header
            text = row.get("query") or row.get("text") or row.get("question")
            if text:
                rows.append(text.strip())
    return rows


def sweep():
    _load_embedder()

    danger_queries = load_queries("eval/danger_sign_eval_100.csv")
    negative_queries = load_queries("eval/negative_set_100.csv")

    print(f"Loaded {len(danger_queries)} danger queries, "
          f"{len(negative_queries)} negative queries.\n")
    print(f"{'threshold':>10} | {'danger recall':>14} | {'negative FP rate':>17}")
    print("-" * 48)

    for threshold in THRESHOLDS_TO_SWEEP:
        import api.safety.danger_gate as dg
        dg.EMBEDDING_THRESHOLD = threshold

        danger_hits = sum(1 for q in danger_queries if _embedding_match(q) is not None)
        danger_recall = danger_hits / len(danger_queries) if danger_queries else 0.0

        negative_hits = sum(1 for q in negative_queries if _embedding_match(q) is not None)
        negative_fp_rate = negative_hits / len(negative_queries) if negative_queries else 0.0

        print(f"{threshold:>10.2f} | {danger_recall:>14.3f} | {negative_fp_rate:>17.3f}")

    print(f"\nCurrent production EMBEDDING_THRESHOLD = {EMBEDDING_THRESHOLD}")


if __name__ == "__main__":
    sweep()