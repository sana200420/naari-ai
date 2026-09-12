"""
eval/run_eval.py

Runs the danger gate against eval/danger_sign_eval_100.csv and reports recall.
All rows in this set are expected to trigger ESCALATE (positive class).

Usage:
    python eval/run_eval.py            # verbose report
    python eval/run_eval.py --ci       # same report, for CI (does not fail the build)

Full miss list (all missed cases, untruncated) is written to
eval/danger_gate_misses.csv on every run, so the phrase-bank work has
a real artifact to work from instead of an 80-char stdout snippet.
"""

import argparse
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.safety.danger_gate import run_danger_gate

CSV_PATH = Path(__file__).resolve().parent / "danger_sign_eval_100.csv"
MISSES_CSV_PATH = Path(__file__).resolve().parent / "danger_gate_misses.csv"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Run in CI mode. Exits non-zero if recall is below 1.00.",
    )
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
                misses.append({**row, "gate_method": result.method})
        else:
            # not expected in this file, but handle gracefully
            if not result.escalate:
                hits += 1
            else:
                misses.append({**row, "gate_method": result.method})

    recall = hits / total if total else 0.0

    print(f"Total cases: {total}")
    print(f"Correctly escalated: {hits}")
    print(f"Missed: {len(misses)}")
    print(f"Recall: {recall:.4f}")

    if misses:
        with open(MISSES_CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["question", "subcategory", "expected_behavior", "reason", "gate_method"]
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(misses)
        print(f"\nFull miss list ({len(misses)} rows) written to {MISSES_CSV_PATH}")

    if recall < 1.0:
        print(
            f"\nNOTE: recall {recall:.4f} is below the 1.00 target. "
            f"See eval/danger_gate_misses.csv.",
            file=sys.stderr,
        )
        if args.ci:
            sys.exit(1)
    else:
        print("\nOK: recall meets the 1.00 target.")

    sys.exit(0)


if __name__ == "__main__":
    main()
