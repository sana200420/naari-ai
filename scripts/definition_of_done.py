"""Score the project against docs/ROADMAP.md section 7, all in one run.

Section 7 is what the FYP is graded on, and until now each number lived in a
different notebook, message or head. Several had never been measured at all.
This produces the whole table from the live Space in one pass, so "are we done"
stops being a matter of recollection.

    Recall@1 / @5 / @20   gold set, does the right row come back
    Refusal correctness   out-of-scope questions must not be answered
    Citation presence     every non-refusal answer must carry its source
    p95 latency           warm service

Two targets are deliberately NOT scored here:

  Danger-sign recall and false-escalation belong to api/safety and have their
  own harness (eval/run_danger_gate_eval.py). Re-implementing them here would
  mean two numbers that can disagree.

  Faithfulness is "zero facts absent from the retrieved rows", which needs a
  human reading answers against sources. A script claiming to measure it would
  be worse than admitting it is unmeasured -- so it is reported as such.

    python scripts/definition_of_done.py
    python scripts/definition_of_done.py --limit 40     # quick pass
"""

import argparse
import json
import os
import statistics
import sys
import time

import pandas as pd
from gradio_client import Client

SPACE = "Sanapalijo/naari-ai"
GOLD = os.path.join("eval", "gold_eval_280_linked.csv")
OUT_OF_SCOPE = os.path.join("eval", "out_of_scope_eval.csv")
OUT_MD = os.path.join("eval", "definition_of_done.md")

REFUSAL_PATHS = {"refusal", "referral", "danger"}


def retrieval_metrics(client, gold, limit):
    rows, lat = [], []
    n = len(gold)
    for i, (_, r) in enumerate(gold.iterrows(), 1):
        try:
            p = json.loads(client.predict(query=r["query"], top_k=20,
                                          api_name="/retrieve"))
        except Exception as exc:
            print(f"  [{i}/{n}] retrieve error {type(exc).__name__}", flush=True)
            continue
        ids = [int(x["answer_id"]) for x in p["results"]]
        want = int(r.correct_answer_id)
        rank = ids.index(want) + 1 if want in ids else None
        rows.append({"query_id": r.query_id, "rank": rank})
        lat.append(p["latency_ms"])
        if i % 25 == 0 or i == n:
            d = pd.DataFrame(rows)
            print(f"  [{i}/{n}] R@1 {(d['rank'] == 1).mean():.3f}", flush=True)
    d = pd.DataFrame(rows)
    at = lambda k: float((d["rank"].notna() & (d["rank"] <= k)).mean())
    return {"n": len(d), "r1": at(1), "r5": at(5), "r20": at(20),
            "retrieval_p95_ms": float(statistics.quantiles(lat, n=20)[18]) if len(lat) > 1 else None}


def scope_and_citation(client, oos, gold, limit):
    refused, cited, checked, lat = 0, 0, 0, []
    for i, (_, r) in enumerate(oos.iterrows(), 1):
        try:
            d = json.loads(client.predict(query=r["query"], language="sindhi",
                                          api_name="/ask"))
        except Exception:
            continue
        checked += 1
        if d.get("path") in REFUSAL_PATHS:
            refused += 1
        lat.append(d.get("latency_ms") or 0)
        if i % 20 == 0 or i == len(oos):
            print(f"  [{i}/{len(oos)}] refused {refused}/{checked}", flush=True)

    # Citation presence is measured on ANSWERED questions, not refusals --
    # a refusal has nothing to cite.
    answered, with_ids = 0, 0
    for _, r in gold.head(min(40, len(gold))).iterrows():
        try:
            d = json.loads(client.predict(query=r["query"], language="sindhi",
                                          api_name="/ask"))
        except Exception:
            continue
        if d.get("path") in REFUSAL_PATHS:
            continue
        answered += 1
        if d.get("retrieved_ids"):
            with_ids += 1
        lat.append(d.get("latency_ms") or 0)
    return {"scope_n": checked,
            "refusal_correctness": refused / checked if checked else None,
            "answered_n": answered,
            "citation_presence": with_ids / answered if answered else None,
            "ask_p95_ms": float(statistics.quantiles(lat, n=20)[18]) if len(lat) > 1 else None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    gold = pd.read_csv(GOLD)
    oos = pd.read_csv(OUT_OF_SCOPE)
    if args.limit:
        gold, oos = gold.head(args.limit), oos.head(args.limit)

    client = Client(SPACE)
    print(f"retrieval metrics over {len(gold)} gold queries ...", flush=True)
    t0 = time.time()
    rm = retrieval_metrics(client, gold, args.limit)
    print(f"\nscope + citation over {len(oos)} out-of-scope queries ...", flush=True)
    sc = scope_and_citation(client, oos, gold, args.limit)
    took = time.time() - t0

    def verdict(value, target, direction=">="):
        if value is None:
            return "not measured", "—"
        ok = value >= target if direction == ">=" else value <= target
        return f"{value:.3f}", "PASS" if ok else "FAIL"

    rowdefs = [
        ("Recall@5", f"{rm['n']} gold queries", 0.90, rm["r5"], ">="),
        ("Recall@1", f"{rm['n']} gold queries", 0.70, rm["r1"], ">="),
        ("Refusal correctness", f"{sc['scope_n']} out-of-scope", 0.95,
         sc["refusal_correctness"], ">="),
        ("Citation presence", f"{sc['answered_n']} answered", 1.00,
         sc["citation_presence"], ">="),
        ("p95 latency (s)", "warm service", 3.0,
         (sc["ask_p95_ms"] / 1000) if sc["ask_p95_ms"] else None, "<="),
    ]

    lines = ["# Definition of done — measured", "",
             f"Generated by `scripts/definition_of_done.py` against the live Space "
             f"in {took/60:.0f} min. Targets from `docs/ROADMAP.md` section 7.", "",
             "| Metric | Measured on | Target | Actual | |", "|---|---|---:|---:|---|"]
    for name, on, target, value, direction in rowdefs:
        shown, mark = verdict(value, target, direction)
        arrow = "≤" if direction == "<=" else "≥"
        lines.append(f"| {name} | {on} | {arrow} {target} | {shown} | {mark} |")
    lines += ["",
              f"Also measured: Recall@20 = {rm['r20']:.3f} "
              f"(the correct row is in the shortlist this often), "
              f"retrieval-only p95 = {rm['retrieval_p95_ms']:.0f}ms.", "",
              "## Not scored here", "",
              "**Danger-sign recall** and **false-escalation** are owned by "
              "`api/safety` and measured by `eval/run_danger_gate_eval.py`. Two "
              "harnesses for one number can only disagree.", "",
              "**Faithfulness** means zero facts absent from the retrieved rows. "
              "That needs a human reading answers against their sources; a script "
              "claiming to measure it would be worse than recording it as "
              "unmeasured. One known violation exists: an elaborated answer added "
              "a toxic-shock warning that was correct but not in the retrieved "
              "row.", ""]

    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print("\n" + "\n".join(lines))
    print(f"wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
