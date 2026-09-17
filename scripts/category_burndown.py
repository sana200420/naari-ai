"""Sort a category's failures into buckets that have different owners.

"Pregnancy is weak" is not actionable. Three quite different problems hide
behind it, and each needs a different person to fix it:

  MISSING    the correct row never appears in the shortlist at all. No amount
             of reranking or threshold tuning reaches it. Needs knowledge base
             content -- Mahnoor.
  RANKING    the correct row is in the shortlist but not first. Retrieval found
             it and ordering lost it. Needs variants or ranking work -- Sana.
  PASSING    the correct row is already first. Nothing to do.

Until they are separated, you cannot tell whether to write content or tune
retrieval, so the category sits on the board looking equally bad in both
directions.

Runs against the live Space's /retrieve endpoint, which returns the whole
shortlist rather than the five results /ask exposes.

    python scripts/category_burndown.py
    python scripts/category_burndown.py --categories "PCOS & Hormonal Health"
"""

import argparse
import io
import json
import os
import sys
import time

import pandas as pd
from gradio_client import Client

GOLD = os.path.join("eval", "gold_eval_280_linked.csv")
OUT_CSV = os.path.join("eval", "category_burndown.csv")
SPACE = "Sanapalijo/naari-ai"
DEFAULT_CATEGORIES = ["Pregnancy & Maternal Health", "PCOS & Hormonal Health"]
TOP_K = 20


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--categories", nargs="*", default=DEFAULT_CATEGORIES)
    ap.add_argument("--limit", type=int, default=0, help="cap rows, for a smoke run")
    args = ap.parse_args()

    gold = pd.read_csv(GOLD)
    rows = gold[gold.stated_category.isin(args.categories)]
    if args.limit:
        rows = rows.head(args.limit)
    print(f"{len(rows)} gold queries across {len(args.categories)} categories", flush=True)

    client = Client(SPACE)
    out, t0 = [], time.time()

    for n, (_, r) in enumerate(rows.iterrows(), 1):
        correct = int(r.correct_answer_id)
        try:
            payload = json.loads(client.predict(query=r["query"], top_k=TOP_K,
                                                api_name="/retrieve"))
            ids = [int(x["answer_id"]) for x in payload["results"]]
            scores = [float(x["score"]) for x in payload["results"]]
        except Exception as exc:
            out.append({"query_id": r.query_id, "category": r.stated_category,
                        "query": r["query"], "correct_answer_id": correct,
                        "bucket": "ERROR", "rank": None, "top1_id": None,
                        "top1_score": None, "note": f"{type(exc).__name__}"})
            print(f"  [{n}/{len(rows)}] ERROR {type(exc).__name__}", flush=True)
            continue

        rank = ids.index(correct) + 1 if correct in ids else None
        if rank == 1:
            bucket = "PASSING"
        elif rank is not None:
            bucket = "RANKING"
        else:
            bucket = "MISSING"

        out.append({
            "query_id": r.query_id,
            "category": r.stated_category,
            "query": r["query"],
            "correct_answer_id": correct,
            "bucket": bucket,
            "rank": rank,
            "top1_id": ids[0] if ids else None,
            "top1_score": round(scores[0], 4) if scores else None,
            "shortlist": ";".join(str(i) for i in ids[:TOP_K]),
            "note": "",
        })
        if n % 10 == 0 or n == len(rows):
            done = pd.DataFrame(out)
            counts = done.bucket.value_counts().to_dict()
            print(f"  [{n}/{len(rows)}] {counts}  ({time.time()-t0:.0f}s)", flush=True)

    df = pd.DataFrame(out)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8")

    print("\n" + "=" * 62)
    total = len(df)
    for cat in args.categories:
        sub = df[df.category == cat]
        if not len(sub):
            continue
        print(f"\n{cat}  (n={len(sub)})")
        for bucket in ("PASSING", "RANKING", "MISSING", "ERROR"):
            k = int((sub.bucket == bucket).sum())
            if k:
                print(f"  {bucket:8} {k:3}  ({k/len(sub)*100:.0f}%)")
        ranked = sub[sub.bucket == "RANKING"]
        if len(ranked):
            print(f"  ranks of recoverable misses: "
                  f"{sorted(int(x) for x in ranked['rank'].dropna())}")

    print(f"\noverall: {total} queries")
    for bucket in ("PASSING", "RANKING", "MISSING", "ERROR"):
        k = int((df.bucket == bucket).sum())
        if k:
            print(f"  {bucket:8} {k:3}  ({k/total*100:.0f}%)")
    print(f"\nwrote {OUT_CSV}")
    print("MISSING rows are the content list for Mahnoor; "
          "RANKING rows are retrieval work.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
