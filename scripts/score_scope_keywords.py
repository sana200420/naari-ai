"""Measure the scope classifier against the whole out-of-scope set.

Sabiha's fix was built from one confirmed failing query, which is the right
way to start but leaves the question of what the other 99 do. This answers it,
and it also answers a question the scorecard could not.

The scorecard reported refusal correctness 0.860 -- 86 of 100 out-of-scope
questions not answered. The gate only classifies 9 of them as out of scope.
The other ~77 are refused because retrieval found nothing above tau_low, which
is refusal by accident: the question was not recognised as out of scope, the
corpus simply had no plausible match.

That distinction matters because the accidental half erodes as retrieval
improves. Every point of Recall@1 we win makes it likelier that an
out-of-scope question finds something that looks close enough to answer -- the
abortion query that came back with constipation advice at band=high is what
that failure looks like. Scope classification has to carry the load instead.

Candidate keywords are scored on two numbers, and the second is the one with
teeth: how many out-of-scope questions it catches, and how many of the 248
real health questions it would wrongly block. A keyword that catches 14
abortion queries and also blocks women asking about their own pregnancy is a
worse bug than the one it fixes.

    python scripts/score_scope_keywords.py
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.safety.danger_gate import run_danger_gate          # noqa: E402
from retrieval.normalize import normalize_sd                 # noqa: E402

OOS = os.path.join("eval", "out_of_scope_eval.csv")
GOLD = os.path.join("eval", "gold_eval_280_linked.csv")
OUT = os.path.join("eval", "scope_keyword_candidates.csv")

# Chosen to be specific. Deliberately NOT included: حمل, مون, توهان, آهي --
# they appear in most of the out-of-scope set but also in hundreds of genuine
# questions, so they trade a refusal failure for a much worse block.
CANDIDATES = {
    "abortion": ["ابارشن", "اڻڄاتل حمل", "حمل رکڻ نه", "رکڻ نه ٿي چاهيان",
                 "حمل کان جان", "حمل نه گھرجي", "ختم ڪرڻ جو طريقو"],
    "named_contraceptives": ["مانع حمل", "ڪنڊوم", "ايمرجنسي گولي", "ڪاپر ٽي", "iud"],
    "domestic_violence_referral": ["مڙس مون کي ماري", "مڙس مون کي ڏمري", "ظلم ڪري",
                                   "تنگ ڪيو ويندو", "دڙڪا", "تشدد", "ڌمڪي",
                                   "طلاق وٺڻي", "زوريءَ", "هيلپ لائين", "پناهه",
                                   "بند ڪري رکيو", "بند رکيو"],
    "doctor_question": ["ميڊيڪل لائسنس", "طبي تعليم", "دوا لکي", "حقيقي انسان",
                        "ڊاڪٽر جي مشوري جي جاءِ", "ڀروسو ڪري سگهان", "قابل اعتماد",
                        "تصديق ٿيل آهي", "رپورٽ پڙهي", "روبوٽ", "ذميوار ڪير"],
    "non_health_chatter": ["موسم", "تنهنجي پيدائش", "نالو ڇا آهي", "تون ڪير آهين",
                           "فلم", "هوٽل", "تاريخ آهي", "لطيفو", "مفاصلي", "رنگ سٺو",
                           "ريسپي", "گادي وارو", "ڪرڪيٽ", "ڪتاب جي صلاح",
                           "ٻولي ڳالهائين", "موسيقي", "پسنديده کاڌي", "سفر جي جاءِ",
                           "بارش", "روبوٽ"],
}


def main() -> int:
    oos = pd.read_csv(OOS)
    gold = pd.read_csv(GOLD)
    oos_norm = [(r.scope_type, normalize_sd(r["query"])) for _, r in oos.iterrows()]
    gold_norm = [normalize_sd(r["query"]) for _, r in gold.iterrows()]

    caught_now = [bool(g.escalate or g.scope_block) for g in
                  (run_danger_gate(r["query"], use_embedding=False)
                   for _, r in oos.iterrows())]
    print(f"gate today: {sum(caught_now)}/{len(oos)} out-of-scope questions classified")

    rows = []
    for scope, kws in CANDIDATES.items():
        for kw in kws:
            n = normalize_sd(kw)
            catches = sum(1 for st, q in oos_norm if n in q)
            in_scope = sum(1 for st, q in oos_norm if n in q and st.startswith(scope[:6]))
            blocks = sum(1 for q in gold_norm if n in q)
            rows.append({"scope": scope, "keyword": kw,
                         "catches_out_of_scope": catches,
                         "of_which_right_scope": in_scope,
                         "blocks_real_questions": blocks})
    df = pd.DataFrame(rows).sort_values(
        ["blocks_real_questions", "catches_out_of_scope"], ascending=[True, False])
    df.to_csv(OUT, index=False, encoding="utf-8")

    after = []
    allk = [normalize_sd(k) for kws in CANDIDATES.values() for k in kws]
    for (st, q), now in zip(oos_norm, caught_now):
        after.append(now or any(k in q for k in allk))
    print(f"with all candidates: {sum(after)}/{len(oos)}")
    print(f"false blocks on {len(gold)} real health questions: "
          f"{int(df.blocks_real_questions.sum())}")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
