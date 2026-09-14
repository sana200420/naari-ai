"""Repair the variant queue before it becomes a retrieval index.

Mahnoor's 4,000-row queue is 2 genuine rewordings per KB question and the
quality is good -- real rephrasings rather than the prefix padding that got the
previous 10,059-row batch rejected. Only 7 rows show the containment signature.

Two defects have to be fixed before these become an index, both of which come
from the queue being generated against the pre-fix KB:

  44 variants carry the old mistranslations (iron as لوھ, period as عرصو, kale
  as ڪيلي). A variant is supposed to widen lexical coverage of a KB row; one
  spelling iron as "the metal" widens coverage of the wrong word and pulls
  queries toward a row that no longer says that.

  86 variants are byte-identical to their original. They add nothing to the
  index and would inflate the row count while doing no retrieval work.

Identical rows are marked rather than deleted -- the KB id still needs its two
variants, so the gap should be visible to whoever regenerates them.

    python scripts/clean_variant_queue.py --dry-run
    python scripts/clean_variant_queue.py --apply
"""

import argparse
import os
import sys

import pandas as pd

IN_CSV = os.path.join("data", "incoming", "variant_queue_FINAL_combined.csv")
OUT_CSV = os.path.join("data", "processed", "variant_queue_clean.csv")

# Same corrections as scripts/fix_terminology.py and fix_iron_terminology.py,
# longest form first so عرصي does not become ماهواريي.
TERMS = [
    ("\u0639\u0631\u0635\u0646", "\u0645\u0627\u0647\u0648\u0627\u0631\u064a"),
    ("\u0639\u0631\u0635\u064a", "\u0645\u0627\u0647\u0648\u0627\u0631\u064a"),
    ("\u0639\u0631\u0635\u0627", "\u0645\u0627\u0647\u0648\u0627\u0631\u064a"),
    ("\u0639\u0631\u0635\u0648", "\u0645\u0627\u0647\u0648\u0627\u0631\u064a"),
    ("\u0644\u0648\u06be\u0647", "\u0622\u0626\u0631\u0646"),
    ("\u0644\u0648\u06be", "\u0622\u0626\u0631\u0646"),
    ("\u0644\u0648\u0647", "\u0622\u0626\u0631\u0646"),
    ("\u06aa\u064a\u0644\u064a", "\u06aa\u064a\u0644"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    v = pd.read_csv(IN_CSV)
    before = v.variant_question.astype(str).copy()

    fixed = before.copy()
    for wrong, right in TERMS:
        fixed = fixed.str.replace(wrong, right, regex=False)
    n_terms = int((fixed != before).sum())
    v["variant_question"] = fixed

    same = v.variant_question.astype(str) == v.original_question.astype(str)
    v.loc[same, "review_status"] = "regenerate"
    v.loc[same, "review_notes"] = "identical to original, adds no lexical coverage"
    v.loc[(~same) & (v.review_status == "pending"), "review_status"] = "auto_ok"

    contained = [
        i for i, (o, x) in enumerate(zip(v.original_question.astype(str),
                                         v.variant_question.astype(str)))
        if o != x and (o in x or x in o)
    ]
    v.loc[v.index[contained], "review_status"] = "regenerate"
    v.loc[v.index[contained], "review_notes"] = "one string contains the other, likely padding"

    print(f"rows                        : {len(v)}")
    print(f"terminology corrected       : {n_terms}")
    print(f"marked regenerate (identical): {int(same.sum())}")
    print(f"marked regenerate (padding) : {len(contained)}")
    print(f"usable now                  : {int((v.review_status == 'auto_ok').sum())}")
    short = v[v.review_status == "auto_ok"].groupby("source_kb_id").size()
    print(f"KB ids left with <2 usable variants: {int((short < 2).sum())}")

    if args.apply:
        os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
        v.to_csv(OUT_CSV, index=False, encoding="utf-8")
        print(f"\nwrote {OUT_CSV}")
    else:
        print("\ndry run -- nothing written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
