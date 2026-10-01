"""
Phase 4 -- Demo rehearsal (Risk 3)
Playbook: "Run the exact demo script ten times the day before and count the
429s. If you get any, you will get them tomorrow too."
Done when: ten consecutive clean runs are recorded.

Usage:
    python scripts/demo_rehearsal.py --space Sanapalijo/naari-ai
    python scripts/demo_rehearsal.py --space Sanapalijo/naari-ai --runs 3   # quick check

A "clean run" = every question in the script gets a real, well-formed
answer back, with no error and no response over COLD_START_THRESHOLD_MS
(a cold-start proxy -- a genuinely warm Space should answer well under this).

Rewritten 2026-09-25 -- the previous version POSTed to a plain `{url}/ask`,
which the live Gradio Space has never exposed (the API surface is entirely
`gr.api`, see app.py's ask_api/retrieve_api/feedback_api, reached only
through Gradio's own queue protocol). Every request 404'd, on every one of
the 10 runs it was "rehearsed" against -- and the old "clean" check only
looked at is_429 and is_cold_start, never at whether the call actually
succeeded, so all ten 404-riddled runs were recorded as clean. Fixed by
using gradio_client (same pattern keep_warm.py already uses) and by
checking for a real, non-empty answer before calling anything clean.

429 specifically: the live Space's rate limiter (api/phase3_cache.py's
is_rate_limited) is wired into api/routers/ask.py, a FastAPI route the
live Gradio app.py does not use -- app.py calls run_pipeline() directly.
So a 429 is not currently reachable through this script no matter how
it's written; count_429 stays wired in case that changes, but treat this
run as measuring "does the Space answer correctly and promptly," not
"does rate limiting kick in."
"""
import argparse
import json
import time
from datetime import datetime, timezone

from gradio_client import Client

# Your actual demo script -- the questions you plan to ask in front of
# judges. Replace these with your real rehearsed demo questions.
DEMO_QUESTIONS = [
    "ماهواري ڇا آهي",
    "حمل ۾ الٽي ڇو ٿئي ٿي",
    "گھڻو رت وهي رهيو آهي",  # danger-sign -- must escalate, not hang
    "پي سي او ايس جون علامتون ڪهڙيون آهن",
    "پيريڊ دوران درد لاءِ ڇا ڪجي",
]

COLD_START_THRESHOLD_MS = 5000  # anything slower than this looks like a cold start
RUNS = 10

_client = None


def _get_client(space: str) -> Client:
    global _client
    if _client is None:
        _client = Client(space)
    return _client


def _ask_once(space: str, query: str) -> dict:
    t0 = time.time()
    try:
        raw = _get_client(space).predict(query=query, language="sindhi", api_name="/ask")
        latency_ms = round((time.time() - t0) * 1000, 1)
        payload = json.loads(raw)
        answer = (payload.get("answer") or "").strip()
        ok = bool(answer)
        return {
            "query": query,
            "ok": ok,
            "path": payload.get("path"),
            "latency_ms": latency_ms,
            "is_429": False,  # see module docstring -- not reachable on this path today
            "is_cold_start": latency_ms > COLD_START_THRESHOLD_MS,
            "error": None if ok else "empty answer field in an otherwise valid response",
        }
    except Exception as e:
        latency_ms = round((time.time() - t0) * 1000, 1)
        return {
            "query": query,
            "ok": False,
            "path": None,
            "latency_ms": latency_ms,
            "is_429": False,
            "is_cold_start": False,
            "error": f"{type(e).__name__}: {e}",
        }


def run_once(space: str, run_number: int) -> dict:
    """Send every demo question once. Return per-run stats."""
    results = []
    for q in DEMO_QUESTIONS:
        results.append(_ask_once(space, q))
        # small gap between questions in a run -- real demo pacing, not a hammer
        time.sleep(1)

    n_429 = sum(r["is_429"] for r in results)
    n_cold = sum(r["is_cold_start"] for r in results)
    n_error = sum(not r["ok"] for r in results)
    clean = (n_429 == 0 and n_cold == 0 and n_error == 0)

    return {
        "run": run_number,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "clean": clean,
        "count_429": n_429,
        "count_cold_start": n_cold,
        "count_error": n_error,
        "details": results,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--space", required=True,
                        help="HF Space id, e.g. Sanapalijo/naari-ai (not a URL)")
    parser.add_argument("--runs", type=int, default=RUNS)
    parser.add_argument("--gap-seconds", type=int, default=30,
                         help="Wait between full runs (simulates time between rehearsal passes)")
    parser.add_argument("--out", default="eval/demo_rehearsal_results.json")
    args = parser.parse_args()

    all_runs = []
    consecutive_clean = 0
    max_consecutive_clean = 0

    for i in range(1, args.runs + 1):
        print(f"\n=== Run {i}/{args.runs} ===")
        run = run_once(args.space, i)
        all_runs.append(run)

        if run["clean"]:
            consecutive_clean += 1
            print(f"  CLEAN -- {consecutive_clean} consecutive clean runs so far")
        else:
            consecutive_clean = 0
            print(f"  NOT CLEAN -- 429s: {run['count_429']}, "
                  f"cold-starts: {run['count_cold_start']}, errors: {run['count_error']}")
            for d in run["details"]:
                if d["is_429"] or d["is_cold_start"] or not d["ok"]:
                    print(f"    - {d['query'][:30]}... ok={d['ok']} "
                          f"latency={d['latency_ms']}ms error={d.get('error')}")

        max_consecutive_clean = max(max_consecutive_clean, consecutive_clean)

        if i < args.runs:
            time.sleep(args.gap_seconds)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(all_runs, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"RESULT: {max_consecutive_clean}/{args.runs} max consecutive clean runs")
    print(f"Playbook target: 10 consecutive clean runs")
    print(f"Full results saved to {args.out}")
    print(f"{'='*50}")

    if max_consecutive_clean < args.runs:
        print("\nNOT YET DONE -- fix the causes above and re-run.")
    else:
        print("\nDONE -- 10 consecutive clean runs recorded.")


if __name__ == "__main__":
    main()
