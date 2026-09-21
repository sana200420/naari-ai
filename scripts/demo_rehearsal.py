"""
Phase 4 -- Demo rehearsal (Risk 3)
Playbook: "Run the exact demo script ten times the day before and count the
429s. If you get any, you will get them tomorrow too."
Done when: ten consecutive clean runs are recorded.

Usage:
    python scripts/demo_rehearsal.py --url https://<your-space>.hf.space
    python scripts/demo_rehearsal.py --url http://localhost:8000  # local test

A "clean run" = every question in the script gets a 200, no 429, and no
response over COLD_START_THRESHOLD_MS (a cold-start proxy -- a genuinely
warm Space should answer well under this).
"""
import argparse
import json
import time
from datetime import datetime, timezone

import requests

# Your actual demo script -- the questions you plan to ask in front of
# judges. Replace these with your real rehearsed demo questions.
DEMO_QUESTIONS = [
    "ماهواري ڇا آهي",
    "حمل ۾ الٽي ڇو ٿئي ٿي",
    "گھڻو رت وهي رهيو آهي",  # danger-sign -- must escalate, not hang
    "بارش نه ٿيڻ جو سبب ڇا آهي",
    "پيريڊ دوران درد لاءِ ڇا ڪجي",
]

COLD_START_THRESHOLD_MS = 5000  # anything slower than this looks like a cold start
RUNS = 10


def run_once(base_url: str, run_number: int) -> dict:
    """Send every demo question once. Return per-run stats."""
    results = []
    for q in DEMO_QUESTIONS:
        t0 = time.time()
        try:
            resp = requests.post(
                f"{base_url}/ask",
                json={"query": q, "language": "sindhi"},
                timeout=60,
            )
            latency_ms = round((time.time() - t0) * 1000, 1)
            results.append({
                "query": q,
                "status": resp.status_code,
                "latency_ms": latency_ms,
                "is_429": resp.status_code == 429,
                "is_cold_start": latency_ms > COLD_START_THRESHOLD_MS,
            })
        except requests.RequestException as e:
            latency_ms = round((time.time() - t0) * 1000, 1)
            results.append({
                "query": q,
                "status": None,
                "latency_ms": latency_ms,
                "is_429": False,
                "is_cold_start": False,
                "error": str(e),
            })
        # small gap between questions in a run -- real demo pacing, not a hammer
        time.sleep(1)

    n_429 = sum(r["is_429"] for r in results)
    n_cold = sum(r["is_cold_start"] for r in results)
    n_error = sum("error" in r for r in results)
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
    parser.add_argument("--url", required=True, help="Base URL of the deployed API")
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
        run = run_once(args.url, i)
        all_runs.append(run)

        if run["clean"]:
            consecutive_clean += 1
            print(f"  CLEAN -- {consecutive_clean} consecutive clean runs so far")
        else:
            consecutive_clean = 0
            print(f"  NOT CLEAN -- 429s: {run['count_429']}, "
                  f"cold-starts: {run['count_cold_start']}, errors: {run['count_error']}")
            for d in run["details"]:
                if d["is_429"] or d["is_cold_start"] or "error" in d:
                    print(f"    - {d['query'][:30]}... status={d.get('status')} "
                          f"latency={d['latency_ms']}ms")

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
