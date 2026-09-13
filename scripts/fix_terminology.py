"""Correct mistranslated health terms in the Sindhi knowledge base.

The Sindhi rows were translated from English and carry a recurring class of
error: an English word rendered by its *other* sense. Found so far:

    "fortified"  -> قلعي وارا     ("castle-like", as in a fort)
    "kale"       -> ڪيلي           ("banana")
    "iron"       -> لوھ / لوه      (the metal, not the dietary mineral)
    "period"     -> عرصو / عرصي    ("a span of time", not menstruation)

The last one is the most damaging because it sits in the core menstrual
category. "How many days does a period usually last?" became
"هڪ عرصو عام طور تي ڪيترا ڏينهن گذري ٿو؟" -- "how many days does a duration
pass?", which is not a question. It also costs recall: a woman typing
ماهواري cannot lexically match a row that says عرصو.

Every rule is GATED ON THE ENGLISH ROW, never on a bare Sindhi match. عرصو
legitimately means "duration" in 18 rows whose English says nothing about
periods, and rewriting those would introduce the opposite error.

Questions are rewritten as well as answers, so affected rows need a re-embed
before retrieval sees the change -- the payload sync corrects the displayed
text immediately, the vector only catches up when the notebook re-runs.

    python scripts/fix_terminology.py --dry-run
    python scripts/fix_terminology.py --apply
"""

import argparse
import os
import re
import sys

import pandas as pd

SD_KB = os.path.join("knowledge_base", "Womens_Health_KB - 2000_final.csv")
EN_KB = os.path.join("knowledge_base", "Womens_Health_KB_English - 2000_final.csv")
PROPOSAL = os.path.join("data", "processed", "terminology_fixes.csv")

# (label, english gate regex, wrong Sindhi forms longest-first, correct Sindhi)
RULES = [
    ("period -> ماهواري",
     r"\bperiods?\b",
     ("عرصن", "عرصي", "عرصا", "عرصو"),
     "ماهواري"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    sd = pd.read_csv(SD_KB)
    en = pd.read_csv(EN_KB)
    assert (sd.id.values == en.id.values).all(), "KB files are not id-aligned"

    rows, skipped = [], []
    for idx in range(len(sd)):
        en_text = f"{en.at[idx, 'question']} {en.at[idx, 'answer']}".lower()
        sd_q, sd_a = str(sd.at[idx, "question"]), str(sd.at[idx, "answer"])

        for label, gate, wrong, right in RULES:
            present = any(w in sd_q or w in sd_a for w in wrong)
            if not present:
                continue
            if not re.search(gate, en_text):
                # the other sense -- عرصو really does mean "duration" here
                skipped.append((int(sd.at[idx, "id"]), label))
                continue
            new_q, new_a = sd_q, sd_a
            for w in wrong:                     # longest first, so عرصي is not left as ماهواريي
                new_q = new_q.replace(w, right)
                new_a = new_a.replace(w, right)
            rows.append({
                "id": int(sd.at[idx, "id"]),
                "rule": label,
                "category": sd.at[idx, "category"],
                "question_before": sd_q, "question_after": new_q,
                "answer_before": sd_a, "answer_after": new_a,
                "question_changed": new_q != sd_q,
            })
            sd.at[idx, "question"], sd.at[idx, "answer"] = new_q, new_a
            sd_q, sd_a = new_q, new_a

    proposal = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(PROPOSAL), exist_ok=True)
    proposal.to_csv(PROPOSAL, index=False, encoding="utf-8")

    print(f"rows to fix : {len(proposal)}")
    if len(proposal):
        print(f"  of which change the QUESTION: {int(proposal.question_changed.sum())}"
              f"  (these need a re-embed)")
        for _, r in proposal.head(3).iterrows():
            print(f"\n  id {r.id}")
            print(f"    before: {r.question_before[:76]}")
            print(f"    after : {r.question_after[:76]}")
    print(f"\nleft alone (English has no 'period', so عرصو is genuinely "
          f"'duration'): {len(skipped)}")
    print(f"proposal written to {PROPOSAL}")

    if args.apply:
        sd.to_csv(SD_KB, index=False, encoding="utf-8")
        print(f"\napplied to {SD_KB}")
        print("next: python scripts/sync_kb_payloads.py --allow-question-drift --apply")
    else:
        print("\ndry run -- nothing written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
