"""English-side counterpart to merge_new_kb_rows.py.

Appends only the new ids from a Mahnoor drop, and snaps category/sub_category
to whatever English string already exists for the same Sindhi category on an
aligned row -- derived, not hand-maintained, so it can't go stale. Twice now
(fever, PCOS) the English file has paraphrased the existing taxonomy instead
of matching it exactly, which would otherwise create orphaned categories with
no relationship to the real one.

    python scripts/merge_new_kb_rows_english.py data/incoming/<file>.csv --dry-run
    python scripts/merge_new_kb_rows_english.py data/incoming/<file>.csv --apply
"""

import argparse
import os
import sys

import pandas as pd

SD_KB = os.path.join("knowledge_base", "Womens_Health_KB - 2000_final.csv")
EN_KB = os.path.join("knowledge_base", "Womens_Health_KB_English - 2000_final.csv")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("incoming", help="the new-rows-only English file to merge")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    sd = pd.read_csv(SD_KB)
    en = pd.read_csv(EN_KB)
    new = pd.read_csv(args.incoming)

    if set(new.id) & set(en.id):
        print(f"STOP -- ids already present in the English KB: "
              f"{sorted(set(new.id) & set(en.id))}")
        return 1
    if set(new.id) - set(sd.id):
        print(f"STOP -- ids not present in the Sindhi KB yet -- merge the "
              f"Sindhi side first: {sorted(set(new.id) - set(sd.id))}")
        return 1

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
    aligned_now = len(sd) == len(out)
    print(f"Sindhi/English now {'aligned' if aligned_now else 'STILL MISALIGNED'} "
          f"({len(sd)} vs {len(out)})")

    if args.apply:
        out.to_csv(EN_KB, index=False, encoding="utf-8")
        print(f"\nwrote {EN_KB}")
    else:
        print("\ndry run -- nothing written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
