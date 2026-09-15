"""Take only the genuinely new rows from a Mahnoor KB drop -- discard the rest.

Twice now (fever, 2026-09-14; PCOS, 2026-09-15) a "combined" KB file has
turned out to be an append built on a stale pre-fix local copy: alongside the
new ids, every shared row that carries a terminology fix (iron, period, kale)
or the rural-appropriateness pass (mustard oil/millet/jaggery over
avocado/quinoa/tofu) comes back reverted. Both times, zero of the reverted
rows overlapped with the new content -- there was nothing to salvage, only
to discard.

This generalises the pattern rather than writing a third copy of it: diff the
incoming file against the live KB, print every shared-row change so a human
can eyeball that none of it is real, and append ONLY the ids the live KB
does not already have.

    python scripts/merge_new_kb_rows.py data/incoming/<combined_file>.csv --dry-run
    python scripts/merge_new_kb_rows.py data/incoming/<combined_file>.csv --apply
"""

import argparse
import os
import sys

import pandas as pd

KB = os.path.join("knowledge_base", "Womens_Health_KB - 2000_final.csv")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("incoming", help="the combined KB file to pull new rows from")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    kb = pd.read_csv(KB)
    incoming = pd.read_csv(args.incoming)

    new_rows = incoming[~incoming.id.isin(set(kb.id))].copy()
    shared = incoming[incoming.id.isin(set(kb.id))]

    m = kb.merge(shared, on="id", suffixes=("_kb", "_in"))
    touched = m[(m.question_kb.astype(str) != m.question_in.astype(str)) |
                (m.answer_kb.astype(str) != m.answer_in.astype(str))]
    print(f"shared rows in the drop      : {len(shared)}")
    print(f"shared rows that came back changed: {len(touched)}")
    if len(touched):
        print("  (none of these are applied -- review a sample before trusting that)")
        for _, r in touched.head(5).iterrows():
            print(f"\n  id {r.id}")
            if str(r.question_kb) != str(r.question_in):
                print(f"    Q kb: {str(r.question_kb)[:80]}")
                print(f"    Q in: {str(r.question_in)[:80]}")
            if str(r.answer_kb) != str(r.answer_in):
                print(f"    A kb: {str(r.answer_kb)[:80]}")
                print(f"    A in: {str(r.answer_in)[:80]}")
        if len(touched) > 5:
            print(f"\n  ... and {len(touched) - 5} more")

    if "review_tier" not in new_rows.columns:
        new_rows["review_tier"] = "B"
    new_rows = new_rows[kb.columns]

    bad_cat = new_rows[~new_rows.category.isin(set(kb.category))]
    bad_sub = new_rows[~new_rows.sub_category.isin(set(kb.sub_category))]
    print(f"\nnew rows to append: {len(new_rows)}  ids "
          f"{new_rows.id.min() if len(new_rows) else '-'}-"
          f"{new_rows.id.max() if len(new_rows) else '-'}")
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
    else:
        print("\ndry run -- nothing written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
