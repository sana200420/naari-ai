"""Standardise the Sindhi word for dietary iron on آئرن.

The knowledge base uses three spellings for the same nutrient -- آئرن (36
rows), لوه (24) and لوھ (18). لوه/لوھ is iron the *metal*; for the dietary
mineral, Sindhi speakers use the borrowed آئرن, which is already the majority
usage here. So this is both a correctness fix and a consistency one.

Checked before running: all 42 rows carrying لوه/لوھ have an English
counterpart containing "iron", so there are no metal-sense false positives to
protect.

Questions are rewritten as well as answers, which has a consequence worth
stating: the stored embedding encodes the OLD wording, and only re-running
the embedding notebook changes that. Retrieval therefore behaves exactly as
before until then -- the displayed text is corrected, the vector is not.

    python scripts/fix_iron_terminology.py --dry-run
    python scripts/fix_iron_terminology.py --apply
"""

import argparse
import os
import sys

import pandas as pd

SD_KB = os.path.join("knowledge_base", "Womens_Health_KB - 2000_final.csv")
EN_KB = os.path.join("knowledge_base", "Womens_Health_KB_English - 2000_final.csv")

WRONG = ("لوهه", "لوھه", "لوھ", "لوه", "لوہ")
RIGHT = "آئرن"


def fix(text: str) -> tuple[str, bool]:
    out = str(text)
    before = out
    for w in WRONG:                      # longest first, so لوهه is not left as آئرنه
        out = out.replace(w, RIGHT)
    return out, out != before


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    sd = pd.read_csv(SD_KB)
    en = pd.read_csv(EN_KB)
    assert (sd.id.values == en.id.values).all(), "KB files are not id-aligned"
    en_has_iron = (en.answer.astype(str).str.lower().str.contains("iron")
                   | en.question.astype(str).str.lower().str.contains("iron"))

    changed_q, changed_a, skipped = [], [], []
    for idx in range(len(sd)):
        new_q, hit_q = fix(sd.at[idx, "question"])
        new_a, hit_a = fix(sd.at[idx, "answer"])
        if not (hit_q or hit_a):
            continue
        if not en_has_iron.iat[idx]:
            # would be the metal sense; leave it alone
            skipped.append(int(sd.at[idx, "id"]))
            continue
        if hit_q:
            changed_q.append(int(sd.at[idx, "id"]))
            sd.at[idx, "question"] = new_q
        if hit_a:
            changed_a.append(int(sd.at[idx, "id"]))
            sd.at[idx, "answer"] = new_a

    print(f"answers to fix  : {len(changed_a)}")
    print(f"questions to fix: {len(changed_q)}  {changed_q[:10]}")
    print(f"skipped (no 'iron' in the English row, likely metal sense): {len(skipped)}")

    if args.apply:
        sd.to_csv(SD_KB, index=False, encoding="utf-8")
        print(f"\napplied to {SD_KB}")
        print("next: python scripts/sync_kb_payloads.py --apply   (answers only)")
        if changed_q:
            print("NOTE: the questions above still have their OLD wording embedded in "
                  "Qdrant. Re-run retrieval/scripts/embed_and_index.ipynb to fix that; "
                  "until then retrieval behaves as it did before.")
    else:
        print("\ndry run -- nothing written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
