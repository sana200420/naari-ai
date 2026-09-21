"""Find a tau_high that means something.

tau_high gates the high-confidence path -- above it, a stored answer is served
as fact. It is set to 0.75, and on real traffic 83% of queries clear it with a
median top-1 score of 0.957. That is not a confidence gate, it is a
pass-through, which is why the verbatim path served so many wrong answers and
why the confirmation band fired on nearly everything.

This sweeps candidate thresholds over the gold set and reports, for each:

    coverage   how many queries land in the high band
    precision  of those, how many actually have the right answer first

A threshold is only useful where precision is high AND coverage is
meaningful. Diagnostic 4 already showed 0.95 precision is unreachable on this
pipeline, so the question is not "which value hits 0.95" but "where does
precision stop improving", and what coverage that leaves.

Runs against the Space's /retrieve endpoint so it measures the deployed
pipeline, not a local reconstruction.

    python scripts/tune_tau_high.py
"""

import io
import json
import os
import sys
import time

import pandas as pd
from gradio_client import Client

GOLD = os.path.join("eval", "gold_eval_280_linked.csv")
OUT_CSV = os.path.join("eval", "tau_high_sweep.csv")
SCORES_CSV = os.path.join("eval", "gold_top1_scores.csv")
SPACE = "Sanapalijo/naari-ai"
CANDIDATES = [0.00, 0.50, 0.75, 0.85, 0.90, 0.93, 0.95, 0.97, 0.98, 0.99, 0.995]


def collect(client, gold) -> pd.DataFrame:
    rows, t0 = [], time.time()
    for n, (_, r) in enumerate(gold.iterrows(), 1):
        try:
            payload = json.loads(client.predict(query=r["query"], top_k=5,
                                                api_name="/retrieve"))
            res = payload["results"]
            top1 = int(res[0]["answer_id"]) if res else None
            score = float(res[0]["score"]) if res else 0.0
        except Exception as exc:
            print(f"  [{n}] ERROR {type(exc).__name__}", flush=True)
            continue
        rows.append({
            "query_id": r.query_id,
            "query": r["query"],
            "category": r.stated_category,
            "correct_answer_id": int(r.correct_answer_id),
            "top1_id": top1,
            "top1_score": round(score, 5),
            "correct": top1 == int(r.correct_answer_id),
        })
        if n % 25 == 0 or n == len(gold):
            done = pd.DataFrame(rows)
            print(f"  [{n}/{len(gold)}] recall@1 so far "
                  f"{done.correct.mean():.3f}  ({time.time()-t0:.0f}s)", flush=True)
    return pd.DataFrame(rows)


def main() -> int:
    gold = pd.read_csv(GOLD)
    print(f"{len(gold)} gold queries -> {SPACE}/retrieve", flush=True)
    df = collect(Client(SPACE), gold)
    df.to_csv(SCORES_CSV, index=False, encoding="utf-8")

    n = len(df)
    print(f"\noverall Recall@1: {df.correct.mean():.3f}  (n={n})")
    print(f"median top-1 score: {df.top1_score.median():.3f}\n")

    sweep = []
    for tau in CANDIDATES:
        band = df[df.top1_score >= tau]
        cov = len(band) / n if n else 0.0
        prec = band.correct.mean() if len(band) else float("nan")
        # what the high band would get wrong, as a share of ALL traffic --
        # this is the number that matters: how often a woman is told something
        # incorrect as though it were verified fact.
        harm = (len(band) - band.correct.sum()) / n if n else 0.0
        sweep.append({"tau_high": tau, "coverage": round(cov, 4),
                      "precision": round(float(prec), 4) if len(band) else None,
                      "wrong_share_of_all_traffic": round(harm, 4),
                      "n_in_band": len(band)})

    out = pd.DataFrame(sweep)
    out.to_csv(OUT_CSV, index=False, encoding="utf-8")

    print(f"{'tau':>7} {'coverage':>9} {'precision':>10} {'wrong/all':>10} {'n':>5}")
    for _, r in out.iterrows():
        p = f"{r.precision:.3f}" if r.precision is not None else "  -  "
        print(f"{r.tau_high:7.3f} {r.coverage:9.1%} {p:>10} "
              f"{r.wrong_share_of_all_traffic:10.1%} {int(r.n_in_band):5}")

    print(f"\nwrote {OUT_CSV} and {SCORES_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
