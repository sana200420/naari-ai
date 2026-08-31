"""Codepoint frequency histogram over the KB corpus.

Regenerate the evidence behind docs/adr/0002-normalisation-map.md:

    python retrieval/scripts/build_normalisation_table.py

Prints every distinct codepoint in the `question` and `answer` columns,
sorted by frequency, with its Unicode name and category. Re-run this after
any KB rebuild to check whether the decision table still covers everything
the corpus actually contains.
"""

import csv
import sys
import unicodedata
from collections import Counter
from pathlib import Path

KB_PATH = (
    Path(__file__).resolve().parents[2]
    / "knowledge_base"
    / "Womens_Health_KB - 2000_final.csv"
)


def main():
    with open(KB_PATH, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    counter = Counter()
    for row in rows:
        counter.update(row["question"])
        counter.update(row["answer"])

    print(f"{len(rows)} rows scanned, {len(counter)} distinct codepoints\n")
    print(f"{'codepoint':<10} {'char':<4} {'count':>7}  name")
    for ch, count in sorted(counter.items(), key=lambda x: -x[1]):
        cat = unicodedata.category(ch)
        display = ch if cat[0] not in ("C", "M") else "<nonprint>"
        try:
            name = unicodedata.name(ch)
        except ValueError:
            name = "<no name>"
        print(f"U+{ord(ch):04X}    {display:<4} {count:>7}  {name}")


if __name__ == "__main__":
    sys.exit(main())
