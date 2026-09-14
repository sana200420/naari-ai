"""Take Mahnoor's 9 fever rows onto the corrected KB -- and only those 9.

Her file is 2009 rows and looks like an append, but it is not. It was built on
a copy of the KB taken before the terminology and localisation fixes landed, so
86 of the 2000 shared rows come back changed, and every one of those changes is
a regression:

    iron       آئرن  -> لوھ / لوه     (the metal again)
    period     ماهواري -> عرصو        (a span of time again)
    kale       ڪيل   -> ڪيلي          (banana again)
    nutrition  باجرو / جوئر / ڳُڙ -> ڪوئنو / ٽوفو / پاستا

Not one of the 86 adds fever content -- checked by looking for بخار, which
appears in zero of them. So there is nothing to salvage in the shared rows and
taking her file wholesale would silently undo work that is already embedded in
Qdrant.

The 9 new rows themselves are good: real thresholds (100.4F/38C, 103F), real
source URLs, the KB's "don't self-treat, go to the health centre now" pattern
for the danger-sign cases, and 2008 correctly says fever is NOT a PCOS symptom
rather than inventing a link. All 9 land in categories and subcategories that
already exist, so the payload filters keep working.

    python scripts/merge_fever_rows.py --dry-run
    python scripts/merge_fever_rows.py --apply
"""

import argparse
import os
import sys

import pandas as pd

KB = os.path.join("knowledge_base", "Womens_Health_KB - 2000_final.csv")
INCOMING = os.path.join("data", "incoming", "Womens_Health_KB_-_2009_fever_fix.csv")
FEVER_MARK = "\u0628\u062e\u0627\u0631"   # بخار


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    kb = pd.read_csv(KB)
    incoming = pd.read_csv(INCOMING)

    new_rows = incoming[~incoming.id.isin(set(kb.id))].copy()
    shared = incoming[incoming.id.isin(set(kb.id))]

    # Re-check the claim this script rests on, every run. If a future drop
    # really does carry fever content in the shared rows, this stops being
    # safe and should fail loudly rather than discard it.
    m = kb.merge(shared, on="id", suffixes=("_kb", "_in"))
    touched = m[(m.question_kb.astype(str) != m.question_in.astype(str)) |
                (m.answer_kb.astype(str) != m.answer_in.astype(str))]
    gained = touched[~touched.answer_kb.astype(str).str.contains(FEVER_MARK) &
                     touched.answer_in.astype(str).str.contains(FEVER_MARK)]
    print(f"shared rows changed by the drop : {len(touched)}")
    print(f"  of those, adding fever content: {len(gained)}")
    if len(gained):
        print("\nSTOP -- a shared row carries new fever content. Merging only the "
              "new ids would drop it. Review these by hand:")
        print(sorted(gained.id.tolist()))
        return 1
    print("  -> nothing to salvage in the shared rows, discarding all "
          f"{len(shared)} of them")

    if "review_tier" not in new_rows.columns:
        new_rows["review_tier"] = "B"
    new_rows = new_rows[kb.columns]

    print(f"\nnew rows to append: {len(new_rows)}  ids {new_rows.id.min()}"
          f"-{new_rows.id.max()}")
    bad_cat = new_rows[~new_rows.category.isin(set(kb.category))]
    bad_sub = new_rows[~new_rows.sub_category.isin(set(kb.sub_category))]
    if len(bad_cat) or len(bad_sub):
        print(f"  WARNING unknown category {bad_cat.id.tolist()} "
              f"sub_category {bad_sub.id.tolist()}")
    else:
        print("  all categories and subcategories already exist")

    out = pd.concat([kb, new_rows], ignore_index=True)
    assert out.id.is_unique, "duplicate ids after merge"
    print(f"\nKB {len(kb)} -> {len(out)}")

    if args.apply:
        out.to_csv(KB, index=False, encoding="utf-8")
        print(f"\nwrote {KB}")
        print("next: the 9 rows need embedding before retrieval can reach them --")
        print("      retrieval/scripts/reembed_corrected_rows.ipynb, ids 2001-2009")
    else:
        print("\ndry run -- nothing written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
