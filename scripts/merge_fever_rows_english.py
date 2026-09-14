"""Take Mahnoor's English translations of the 9 fever rows (ids 2001-2009).

Content is faithful to the Sindhi originals -- checked by hand. The only
defect is category/sub_category text: her file paraphrases the existing
English taxonomy instead of matching it exactly ("Common Everyday Illnesses"
vs the KB's actual "Common Everyday Ailments"), which would create orphaned
duplicate categories on the English side rather than joining the real ones.
This is mechanical, not a content judgement call, so it's corrected here by
snapping to the canonical string rather than sent back for a rewrite.

The canonical mapping is derived from the 2000 rows that are already
correctly aligned across both files -- Sindhi category -> whichever English
category appears on the same id. Not hand-maintained, so it can't go stale.

    python scripts/merge_fever_rows_english.py --dry-run
    python scripts/merge_fever_rows_english.py --apply
"""

import argparse
import os
import sys

import pandas as pd

SD_KB = os.path.join("knowledge_base", "Womens_Health_KB - 2000_final.csv")
EN_KB = os.path.join("knowledge_base", "Womens_Health_KB_English - 2000_final.csv")
INCOMING = os.path.join("data", "incoming", "fever_gap_new_rows_only_english.csv")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    sd = pd.read_csv(SD_KB)
    en = pd.read_csv(EN_KB)
    new = pd.read_csv(INCOMING)

    if set(new.id) & set(en.id):
        print(f"STOP -- ids already present in the English KB: "
              f"{sorted(set(new.id) & set(en.id))}")
        return 1
    if set(new.id) - set(sd.id):
        print(f"STOP -- ids not present in the Sindhi KB either: "
              f"{sorted(set(new.id) - set(sd.id))}")
        return 1

    # Canonical Sindhi->English category/sub_category, derived from the rows
    # already correctly aligned across both files.
    aligned = sd[sd.id <= 2000][["id", "category", "sub_category"]].merge(
        en[en.id <= 2000][["id", "category", "sub_category"]],
        on="id", suffixes=("_sd", "_en"))
    cat_map = dict(aligned[["category_sd", "category_en"]].drop_duplicates().values)
    sub_map = dict(aligned[["sub_category_sd", "sub_category_en"]].drop_duplicates().values)

    sd_new = sd[sd.id.isin(new.id)].set_index("id")
    new = new.set_index("id")
    fixed, unmapped = 0, []
    for i in new.index:
        want_cat = cat_map.get(sd_new.at[i, "category"])
        want_sub = sub_map.get(sd_new.at[i, "sub_category"])
        if want_cat is None or want_sub is None:
            unmapped.append(i)
            continue
        if new.at[i, "category"] != want_cat:
            print(f"  id {i}: category {new.at[i, 'category']!r} -> {want_cat!r}")
            new.at[i, "category"] = want_cat
            fixed += 1
        if new.at[i, "sub_category"] != want_sub:
            print(f"  id {i}: sub_category {new.at[i, 'sub_category']!r} -> {want_sub!r}")
            new.at[i, "sub_category"] = want_sub
            fixed += 1
    new = new.reset_index()

    print(f"\ncorrected {fixed} category/sub_category values")
    if unmapped:
        print(f"WARNING -- no canonical mapping found for ids {unmapped}, left as-is")

    if "review_tier" not in new.columns:
        new["review_tier"] = "B"
    new = new[en.columns]

    out = pd.concat([en, new], ignore_index=True)
    assert out.id.is_unique, "duplicate ids after merge"
    assert (out[out.id <= 2000].id.values == sd[sd.id <= 2000].id.values).all(), \
        "id order drifted for the original 2000 rows"
    print(f"\nEnglish KB {len(en)} -> {len(out)}")
    print(f"Sindhi/English now both at {len(sd)} rows: "
          f"{'aligned' if len(sd) == len(out) else 'STILL MISALIGNED'}")

    if args.apply:
        out.to_csv(EN_KB, index=False, encoding="utf-8")
        print(f"\nwrote {EN_KB}")
        print("next: python scripts/fix_terminology.py --dry-run  (id-alignment "
              "assert should pass now)")
    else:
        print("\ndry run -- nothing written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
