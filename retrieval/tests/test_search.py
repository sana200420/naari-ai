"""Tests for retrieval.search: RRF fusion (pure logic, no infra needed) and
HybridRetriever against a fake Qdrant client + fake embedder (no bge-m3 or
real Qdrant connection needed)."""

from types import SimpleNamespace

from retrieval.search import RRF_K, HybridRetriever, reciprocal_rank_fusion


# ---------------------------------------------------------------------------
# reciprocal_rank_fusion — pure function
# ---------------------------------------------------------------------------

def test_single_list_preserves_order():
    fused = reciprocal_rank_fusion([[10, 20, 30]])
    assert [item_id for item_id, _ in fused] == [10, 20, 30]


def test_matches_the_exact_formula():
    fused = dict(reciprocal_rank_fusion([[1, 2, 3]], k=60))
    assert fused[1] == 1 / 61
    assert fused[2] == 1 / 62
    assert fused[3] == 1 / 63


def test_item_in_both_lists_outranks_item_in_one():
    # id 5 is rank 3 in both lists; id 1 is rank 1 in only the first list.
    fused = reciprocal_rank_fusion([[1, 2, 5], [9, 8, 5]])
    fused_scores = dict(fused)
    assert fused_scores[5] > fused_scores[1]
    assert fused_scores[5] > fused_scores[9]


def test_item_missing_from_a_list_gets_no_credit_from_it():
    fused_a = dict(reciprocal_rank_fusion([[1, 2, 3]]))
    fused_b = dict(reciprocal_rank_fusion([[1, 2, 3], [1, 2, 3]]))
    # present in both identical lists -> exactly double the single-list score
    assert fused_b[1] == fused_a[1] * 2


def test_empty_lists_produce_empty_result():
    assert reciprocal_rank_fusion([]) == []
    assert reciprocal_rank_fusion([[], []]) == []


def test_sorted_best_first():
    fused = reciprocal_rank_fusion([[100, 200], [200, 100]])
    scores = [s for _, s in fused]
    assert scores == sorted(scores, reverse=True)


def test_ties_broken_by_id_for_determinism():
    # two disjoint singleton lists -> both get the same rank-1 score
    fused = reciprocal_rank_fusion([[5], [3]])
    assert fused == [(3, 1 / (RRF_K + 1)), (5, 1 / (RRF_K + 1))]


# ---------------------------------------------------------------------------
# HybridRetriever — against fakes, no real Qdrant/model needed
# ---------------------------------------------------------------------------

class _FakeHit:
    def __init__(self, answer_id, score):
        self.score = score
        self.payload = {
            "answer_id": answer_id,
            "category": "cat",
            "sub_category": "sub",
            "question": f"question {answer_id}",
            "answer": f"answer {answer_id}",
            "source": "src",
            "review_tier": "B",
        }


class _FakeQdrantClient:
    """Returns canned hits per `using` leg, ignoring the actual query vector."""

    def __init__(self, dense_hits, sparse_hits):
        self._dense_hits = dense_hits
        self._sparse_hits = sparse_hits
        self.calls = []

    def query_points(self, collection_name, query, using, limit, with_payload):
        self.calls.append(using)
        hits = self._dense_hits if using == "dense" else self._sparse_hits
        return SimpleNamespace(points=hits[:limit])


def _fake_embed(query):
    return {"dense": [0.1, 0.2], "sparse": {"1": 0.9}}


def test_dense_search_returns_rows_in_order():
    client = _FakeQdrantClient(
        dense_hits=[_FakeHit(1, 0.9), _FakeHit(2, 0.5)],
        sparse_hits=[],
    )
    retriever = HybridRetriever(client, embed_fn=_fake_embed)

    rows = retriever.dense_search("query", top_k=25)

    assert [r["answer_id"] for r in rows] == [1, 2]
    assert client.calls == ["dense"]


def test_sparse_search_uses_sparse_leg():
    client = _FakeQdrantClient(
        dense_hits=[],
        sparse_hits=[_FakeHit(7, 0.8)],
    )
    retriever = HybridRetriever(client, embed_fn=_fake_embed)

    rows = retriever.sparse_search("query", top_k=25)

    assert [r["answer_id"] for r in rows] == [7]
    assert client.calls == ["sparse"]


def test_fused_search_queries_both_legs_and_dedupes():
    client = _FakeQdrantClient(
        dense_hits=[_FakeHit(1, 0.9), _FakeHit(2, 0.5)],
        sparse_hits=[_FakeHit(2, 0.7), _FakeHit(3, 0.3)],
    )
    retriever = HybridRetriever(client, embed_fn=_fake_embed)

    rows = retriever.fused_search("query", top_k=5)

    assert client.calls == ["dense", "sparse"]
    ids = [r["answer_id"] for r in rows]
    assert len(ids) == len(set(ids)), "fused_search must not return a duplicate answer_id"
    # id 2 appears in both legs, should rank first
    assert ids[0] == 2
    assert all(r["path"] == "fused" for r in rows)


def test_fused_search_respects_top_k():
    client = _FakeQdrantClient(
        dense_hits=[_FakeHit(i, 1.0 / i) for i in range(1, 30)],
        sparse_hits=[],
    )
    retriever = HybridRetriever(client, embed_fn=_fake_embed)

    rows = retriever.fused_search("query", top_k=5, leg_k=25)

    assert len(rows) == 5
