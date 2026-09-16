"""Phase 4, Sana's item: the unanswered-question pipeline.

"Done when a weekly export lists every query below tau_low, clustered by
similarity" (docs/PLAYBOOKS.md). These are the highest-value data the
project will produce post-launch -- free, real, and pointed exactly at
retrieval's blind spots, but only if someone can see the PATTERN in them
rather than 200 individual refused rows nobody has time to read one at a
time.

Pulls from Supabase's query_logs table (api/logging/logger.py writes it;
band="low" is exactly BAND_LOW from api/pipeline.py, i.e. below tau_low --
no need to recompute from scores) over a trailing window, and clusters the
refused queries by text similarity so ten different phrasings of the same
underlying gap show up as one cluster of ten, not ten unrelated rows.

Clustering is TF-IDF over character n-grams (analyzer="char_wb") into
agglomerative clustering with a cosine-distance threshold -- no bge-m3, no
GPU, no Colab. This is a deliberate choice: a *weekly ops report* has to
run on its own, unattended, which the rest of this project's embedding
work (Kaggle/Colab only, see CLAUDE.md) cannot. Char n-grams need no
tokenizer or language model, which matters for Sindhi, and they are good
enough for "these are near-duplicate phrasings" even though they would be
too weak for retrieval itself. If this needs Recall-grade similarity later,
rerun the query list through retrieval/embed.py's bge-m3 in a notebook
instead of extending this script -- keep this one dependency-light.

Nothing has run against real data yet: SUPABASE_URL/KEY are unset (checked
2026-09-16 -- pre-pilot, as expected). The clustering logic itself is
covered by scripts/test_unanswered_questions_report.py against synthetic
data, so this is ready the moment real logs exist rather than something to
debug for the first time during the pilot.

    python scripts/unanswered_questions_report.py                 # live Supabase, last 7 days
    python scripts/unanswered_questions_report.py --days 30
    python scripts/unanswered_questions_report.py --csv path.csv  # test/offline mode, skip Supabase
"""

import argparse
import datetime
import os
import sys

import pandas as pd

OUT_MD = os.path.join("eval", "unanswered_questions_report.md")
OUT_CSV = os.path.join("eval", "unanswered_questions_raw.csv")

DISTANCE_THRESHOLD = 0.75   # cosine distance; lower = stricter clusters
# Calibrated against synthetic near-duplicate Sindhi phrasings, not guessed:
# three genuine rewordings of one menstrual-cycle question came back at
# pairwise cosine distance 0.54-0.69 (different words for "how long" --
# char n-grams penalise vocabulary substitution harder than semantics would),
# while unrelated questions (PCOS, fever) sat at 0.91-0.97 against everything.
# 0.75 sits in the gap. See scripts/test_unanswered_questions_report.py.


def fetch_low_band_queries(days: int) -> pd.DataFrame:
    """Pull query_logs rows with band="low" from the last `days` days.

    Returns empty (not an error) if Supabase isn't configured -- a report
    that correctly says "nothing to show, logging isn't wired up here" is
    more useful than a script that crashes when someone runs it against a
    dev environment.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        print("SUPABASE_URL/KEY not set -- nothing to fetch. "
              "Set them (or pass --csv for a local file) to run this for real.",
              file=sys.stderr)
        return pd.DataFrame(columns=["query", "band", "PATH", "created_at"])

    from supabase import create_client
    client = create_client(url, key)

    since = (datetime.datetime.now(datetime.timezone.utc)
             - datetime.timedelta(days=days)).isoformat()
    resp = (client.table("query_logs")
                  .select("*")
                  .eq("band", "low")
                  .gte("created_at", since)
                  .execute())
    return pd.DataFrame(resp.data)


def cluster_queries(queries: list[str], distance_threshold: float = DISTANCE_THRESHOLD) -> list[int]:
    """Cluster queries by character-n-gram cosine similarity.

    Returns a cluster label per query (same length/order as `queries`).
    A single query, or all-identical queries, is handled without going
    through sklearn's fit (which errors on n_samples < 2 for some settings)
    -- the "weekly report has 3 rows" case is the common case early on and
    must not crash.
    """
    if len(queries) == 0:
        return []
    if len(queries) == 1:
        return [0]

    from sklearn.cluster import AgglomerativeClustering
    from sklearn.feature_extraction.text import TfidfVectorizer

    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=1)
    X = vec.fit_transform(queries)

    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=distance_threshold,
        metric="cosine",
        linkage="average",
    )
    return list(clustering.fit_predict(X.toarray()))


def build_report(df: pd.DataFrame) -> str:
    if df.empty:
        return ("# Unanswered-question report\n\n"
                "No band=\"low\" (below tau_low) queries in this window. "
                "Either nothing was refused (good), or logging isn't "
                "reaching Supabase from this environment yet -- check "
                "SUPABASE_URL/SUPABASE_SERVICE_KEY before trusting a zero.\n")

    df = df.copy()
    df["cluster"] = cluster_queries(df["query"].astype(str).tolist())

    lines = ["# Unanswered-question report", "",
             f"{len(df)} refused queries (band=low), "
             f"{df['cluster'].nunique()} clusters.", ""]

    sizes = df.groupby("cluster").size().sort_values(ascending=False)
    for cluster_id, size in sizes.items():
        group = df[df["cluster"] == cluster_id]
        lines.append(f"## Cluster of {size}" if size > 1 else "## Singleton")
        for q in group["query"].head(10 if size > 10 else size):
            lines.append(f"- {q}")
        if size > 10:
            lines.append(f"- ... and {size - 10} more")
        lines.append("")

    lines += ["---", "",
              "**Next step (this is the item's actual payoff, not this "
              "report alone):** the biggest clusters are candidate new KB "
              "rows or variants -- turn the top few into either and "
              "reindex, then remeasure recall on real user questions "
              "(the next Phase 4 item). A report nobody acts on is just a "
              "longer refusal log."]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--csv", help="read from a local CSV instead of Supabase "
                                  "(needs a 'query' column) -- for testing "
                                  "or an offline export")
    args = ap.parse_args()

    if args.csv:
        df = pd.read_csv(args.csv)
    else:
        df = fetch_low_band_queries(args.days)

    report = build_report(df)

    os.makedirs("eval", exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(report)
    if not df.empty:
        df.to_csv(OUT_CSV, index=False, encoding="utf-8")

    print(report)
    print(f"\nwrote {OUT_MD}" + (f" and {OUT_CSV}" if not df.empty else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
