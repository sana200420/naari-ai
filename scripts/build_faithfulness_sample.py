"""Stratified sample for the faithfulness check (Sabiha, Phase 3 exit gate).

Faithfulness means zero facts in a served answer that aren't in its
retrieved source. It has been completely unmeasured so far -- no one has
started it. This builds the 100-row list to check, stratified by confidence
band using real, live-measured scores from eval/gold_top1_scores.csv
(scripts/tune_tau_high.py's Colab run), not guessed.

Stratified, not cherry-picked: sampling only easy verbatim-band rows would
undersell the actual risk. The riskiest band is "mid" (generated/elaborated
-- an LLM touches the answer), so it's included even though it's the
smallest available pool, and a known faithfulness violation already exists
there (an elaborated answer added a toxic-shock-syndrome warning that was
correct but not in the retrieved row -- see eval/definition_of_done.md).

Target split: 40 high (verbatim path -- served as-is, should be trivially
faithful, worth confirming rather than assuming), 40 confirm ("did you mean
X?" band), 20 mid (generated/elaborated -- highest risk). Below TAU_LOW is
excluded: a refusal has no answer to check.

For each row, pulls the retrieved row's actual question/answer/source from
the live KB so the reference material is at hand -- but the ANSWER TEXT TO
CHECK must come from actually calling the live system (`/ask`, not
`/retrieve`), because the mid/generated band runs the answer through an
LLM and no cached score can stand in for what it actually said. This script
produces the query list and the ground truth to check against; it does not
fabricate what the system would answer.

    python scripts/build_faithfulness_sample.py
"""

import sys

import pandas as pd

SCORES = "eval/gold_top1_scores.csv"
KB = "knowledge_base/Womens_Health_KB - 2000_final.csv"
OUT = "eval/faithfulness_sample_100.csv"

TAU_HIGH, TAU_CONFIRM, TAU_LOW = 0.95, 0.75, 0.2034
TARGET = {"high": 40, "confirm": 40, "mid": 20}
SEED = 42


def band_of(score: float) -> str:
    if score >= TAU_HIGH:
        return "high"
    if score >= TAU_CONFIRM:
        return "confirm"
    if score >= TAU_LOW:
        return "mid"
    return "low"


def main() -> int:
    scores = pd.read_csv(SCORES)
    kb = pd.read_csv(KB).set_index("id")

    scores["band"] = scores.top1_score.apply(band_of)

    rows = []
    for band, n in TARGET.items():
        pool = scores[scores.band == band]
        if len(pool) < n:
            print(f"WARNING: only {len(pool)} queries in '{band}' band, "
                  f"wanted {n} -- taking all of them", file=sys.stderr)
            n = len(pool)
        rows.append(pool.sample(n=n, random_state=SEED))

    sample = pd.concat(rows, ignore_index=True)

    out_rows = []
    for _, r in sample.iterrows():
        src = kb.loc[int(r.top1_id)] if int(r.top1_id) in kb.index else None
        out_rows.append({
            "query_id": r.query_id,
            "query": r["query"],
            "confidence_band": r.band,
            "top1_score": round(float(r.top1_score), 4),
            "retrieved_answer_id": int(r.top1_id),
            "source_question": src["question"] if src is not None else "",
            "source_answer": src["answer"] if src is not None else "",
            "source_citation": src["source"] if src is not None else "",
            "served_answer_actually_shown": "",   # fill from a live /ask call
            "unsupported_claim_found": "",          # yes / no
            "notes": "",
        })

    out = pd.DataFrame(out_rows)
    out = out.sample(frac=1, random_state=SEED).reset_index(drop=True)  # shuffle band order
    out.to_csv(OUT, index=False, encoding="utf-8")

    print(f"wrote {OUT}: {len(out)} rows")
    print(out.confidence_band.value_counts())
    return 0


if __name__ == "__main__":
    sys.exit(main())
