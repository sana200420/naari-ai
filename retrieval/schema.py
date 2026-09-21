"""Schema validator for the KB corpus.

Enforces the six original columns plus `review_tier`, added per Risk 4 in
PLAYBOOKS.md: clinical review is incomplete, so every row is tagged A
(clinician-reviewed, served normally), B (sourced but not clinician-verified,
served with a visible disclosure), or C (uncertain/flagged, never served).
Every row defaults to B until a reviewer promotes it.

    python -m retrieval.schema                 # validate the real KB file
    from retrieval.schema import validate_kb_schema
"""

import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "id",
    "category",
    "sub_category",
    "question",
    "answer",
    "source",
    "review_tier",
]

VALID_TIERS = {"A", "B", "C"}

DEFAULT_KB_PATH = (
    Path(__file__).resolve().parent.parent
    / "knowledge_base"
    / "Womens_Health_KB - 2000_final.csv"
)


def validate_kb_schema(path: Path = DEFAULT_KB_PATH) -> list[str]:
    """Returns a list of violation messages. Empty list means the file is valid."""
    violations = []

    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != REQUIRED_COLUMNS:
            violations.append(
                f"header mismatch: expected {REQUIRED_COLUMNS}, got {reader.fieldnames}"
            )
            return violations  # can't check rows meaningfully with a bad header

        rows = list(reader)

    seen_ids = set()
    for row in rows:
        rid = row["id"]

        if rid in seen_ids:
            violations.append(f"duplicate id: {rid}")
        seen_ids.add(rid)

        for col in ("category", "sub_category", "question", "answer", "source"):
            if not row[col].strip():
                violations.append(f"id={rid}: blank '{col}'")

        tier = row["review_tier"]
        if tier not in VALID_TIERS:
            violations.append(f"id={rid}: invalid review_tier {tier!r}, must be one of {VALID_TIERS}")

    return violations


if __name__ == "__main__":
    problems = validate_kb_schema()
    if problems:
        print(f"{len(problems)} schema violation(s):")
        for p in problems[:50]:
            print(" -", p)
        sys.exit(1)
    print("Schema valid.")
