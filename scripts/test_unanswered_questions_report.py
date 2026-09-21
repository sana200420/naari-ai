"""Tests for the clustering logic in unanswered_questions_report.py.

No real Supabase data exists yet (pre-pilot, checked 2026-09-16), so this
proves the clustering itself is correct against synthetic near-duplicate
Sindhi queries -- the same shape of data the report will see once logging
is live -- rather than leaving it untested until the pilot.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from unanswered_questions_report import build_report, cluster_queries  # noqa: E402

import pandas as pd


def test_empty_input_does_not_crash():
    assert cluster_queries([]) == []


def test_single_query_gets_its_own_cluster():
    assert cluster_queries(["حيض جي چڪر ڇا آهي؟"]) == [0]


def test_near_duplicate_sindhi_phrasings_cluster_together():
    """The actual point of the whole script: ten different ways of asking
    the same refused question must land in one cluster, not ten."""
    variants = [
        "حيض جي چڪر ڪيترو ڊگهو هوندو آهي؟",
        "حيض جو چڪر ڪيترا ڏينهن هلندو آهي؟",
        "منهنجي حيض جي چڪر ڪيترو وقت هلي ٿي؟",
        "عام حيض جو چڪر ڪيتري وقت جو هوندو آهي؟",
    ]
    labels = cluster_queries(variants)
    assert len(set(labels)) == 1, f"expected one cluster, got {labels}"


def test_unrelated_queries_do_not_merge():
    queries = [
        "حيض جي چڪر ڇا آهي؟",
        "PCOS جي علامتون ڪهڙيون آهن؟",
        "حمل دوران بخار ٿئي ته ڇا ڪجي؟",
    ]
    labels = cluster_queries(queries)
    assert len(set(labels)) == len(queries), (
        f"unrelated queries merged into fewer clusters than expected: {labels}"
    )


def test_mixed_batch_separates_the_real_cluster_from_singletons():
    queries = [
        "حيض جي چڪر ڪيترو ڊگهو هوندو آهي؟",
        "حيض جو چڪر ڪيترا ڏينهن هلندو آهي؟",
        "منهنجي حيض جي چڪر ڪيترو وقت هلي ٿي؟",
        "PCOS جي علامتون ڪهڙيون آهن؟",
        "حمل دوران بخار ٿئي ته ڇا ڪجي؟",
    ]
    labels = cluster_queries(queries)
    from collections import Counter
    sizes = sorted(Counter(labels).values(), reverse=True)
    assert sizes[0] == 3, f"expected a cluster of 3, got sizes {sizes}"
    assert sizes[1:] == [1, 1]


def test_build_report_on_empty_dataframe_explains_why_not_crash():
    report = build_report(pd.DataFrame(columns=["query", "band", "PATH", "created_at"]))
    assert "No band=" in report
    assert "SUPABASE_URL" in report   # tells the reader how to tell zero from broken


def test_build_report_orders_clusters_biggest_first():
    df = pd.DataFrame({"query": [
        "حيض جي چڪر ڪيترو ڊگهو هوندو آهي؟",
        "حيض جو چڪر ڪيترا ڏينهن هلندو آهي؟",
        "منهنجي حيض جي چڪر ڪيترو وقت هلي ٿي؟",
        "PCOS جي علامتون ڪهڙيون آهن؟",
    ]})
    report = build_report(df)
    cluster_pos = report.find("Cluster of 3")
    singleton_pos = report.find("Singleton")
    assert cluster_pos != -1 and singleton_pos != -1
    assert cluster_pos < singleton_pos, "biggest cluster must be listed first"
