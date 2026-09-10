"""
eval/run_eval.py

Runs the danger gate against eval/danger_sign_eval_100.csv and reports recall.
All rows in this set are expected to trigger ESCALATE (positive class).

Usage:
    python eval/run_eval.py            # verbose report
    python eval/run_eval.py --ci       # exit 1 if recall < 1.0 (for CI)
"""

import argparse
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.safety.danger_gate import run_danger_gate

CSV_PATH = Path(__file__).resolve().parent / "danger_sign_eval_100.csv"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ci", action="store_true", help="Exit non-zero if recall < 1.0")
    args = parser.parse_args()

    with open(CSV_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)
    hits = 0
    misses = []

    for row in rows:
        question = row["question"]
        expected = row["expected_behavior"].strip().upper()

        result = run_danger_gate(question)

        if expected == "ESCALATE":
            if result.escalate:
                hits += 1
            else:
                misses.append(row)
        else:
            # not expected in this file, but handle gracefully
            if not result.escalate:
                hits += 1
            else:
                misses.append(row)

    recall = hits / total if total else 0.0

    print(f"Total cases: {total}")
    print(f"Correctly escalated: {hits}")
    print(f"Missed: {len(misses)}")
    print(f"Recall: {recall:.4f}")

    if misses:
        print("\n--- MISSED CASES ---")
        for m in misses:
            print(f"[{m['subcategory']}] {m['question'][:80]}...")

    if args.ci and recall < 1.0:
        print("\nCI FAIL: recall below 1.00", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
