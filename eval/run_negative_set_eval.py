"""
eval/run_negative_set_eval.py

Runs the danger gate against eval/negative_set_100.csv and reports the
false-positive rate. Every row in this set is a benign, answerable-or-not
health question with NO danger sign in it — none of them should ever
trigger escalation. This is the counterpart to run_danger_gate_eval.py:
that script measures recall (did we catch every real danger sign), this
one measures precision (are we crying wolf on ordinary questions).

Both matter. A gate tuned only against run_danger_gate_eval.py can reach
1.00 recall by keyword-matching so broadly that it also escalates on
completely benign questions -- which is exactly what happened here: a
bare "بخار" (fever) keyword hit dosage questions with no danger sign at
all (see docs/adr/0003-danger-gate-matching.md).

Usage:
    python eval/run_negative_set_eval.py            # verbose report
    python eval/run_negative_set_eval.py --ci        # same report, for CI

Full false-positive list (untruncated) is written to
eval/negative_set_false_positives.csv on every run.
"""

import argparse
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.safety.danger_gate import run_danger_gate

CSV_PATH = Path(__file__).resolve().parent / "negative_set_100.csv"
FALSE_POS_CSV_PATH = Path(__file__).resolve().parent / "negative_set_false_positives.csv"

# Target: at most this fraction of the negative set may false-positive on
# the danger gate before we consider it a real regression. Zero is the
# aspiration; a small allowance exists because a handful of these rows
# describe symptoms in enough clinical detail that a human reviewer would
# also want a second look -- see the reason column for those specific rows
# before assuming every false positive is a bug.
MAX_ACCEPTABLE_FALSE_POSITIVE_RATE = 0.05


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Run in CI mode. Exits non-zero if the false-positive rate "
             "exceeds MAX_ACCEPTABLE_FALSE_POSITIVE_RATE.",
    )
    args = parser.parse_args()

    with open(CSV_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)
    false_positives = []

    for row in rows:
        question = row["question"]
        result = run_danger_gate(question)
        if result.escalate:
            false_positives.append({**row, "gate_method": result.method,
                                     "matched_keyword": result.matched_keyword})

    fp_count = len(false_positives)
    fp_rate = fp_count / total if total else 0.0

    print(f"Total cases: {total}")
    print(f"False positives (incorrectly escalated): {fp_count}")
    print(f"False positive rate: {fp_rate:.4f}")

    if false_positives:
        with open(FALSE_POS_CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["id", "subcategory", "question", "expected_behavior",
                          "reason", "gate_method", "matched_keyword"]
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(false_positives)
        print(f"\nFull false-positive list ({fp_count} rows) written to {FALSE_POS_CSV_PATH}")

    if fp_rate > MAX_ACCEPTABLE_FALSE_POSITIVE_RATE:
        print(
            f"\nNOTE: false positive rate {fp_rate:.4f} exceeds "
            f"{MAX_ACCEPTABLE_FALSE_POSITIVE_RATE:.2f} — see "
            f"{FALSE_POS_CSV_PATH.name} and tighten the matching keyword(s).",
            file=sys.stderr,
        )
        if args.ci:
            sys.exit(1)
        return

    print("\nOK: false positive rate within acceptable range.")
    sys.exit(0)


if __name__ == "__main__":
    main()
