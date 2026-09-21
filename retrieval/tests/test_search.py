"""Tests for retrieval.search: RRF fusion (pure logic, no infra needed) and
HybridRetriever against a fake Qdrant client + fake embedder (no bge-m3 or
real Qdrant connection needed)."""

from types import SimpleNamespace

from retrieval.search import (
    RRF_K,
    VARIANT_LANG,
    HybridRetriever,
    dedupe_by_answer_id,
    reciprocal_rank_fusion,
)


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
        self.filters = []

    def query_points(self, collection_name, query, using, limit, with_payload, query_filter=None):
        self.calls.append(using)
        self.filters.append(query_filter)
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


# ---------------------------------------------------------------------------
# lang filtering — Sindhi and English points share one collection/vectors
# ---------------------------------------------------------------------------

def test_dense_search_defaults_to_sindhi_only_filter():
    client = _FakeQdrantClient(dense_hits=[_FakeHit(1, 0.9)], sparse_hits=[])
    retriever = HybridRetriever(client, embed_fn=_fake_embed)

    retriever.dense_search("query")

    query_filter = client.filters[0]
    assert query_filter is not None
    assert query_filter.must[0].match.value == "sd"


def test_dense_search_lang_none_sends_no_filter():
    client = _FakeQdrantClient(dense_hits=[_FakeHit(1, 0.9)], sparse_hits=[])
    retriever = HybridRetriever(client, embed_fn=_fake_embed)

    retriever.dense_search("query", lang=None)

    assert client.filters[0] is None


def test_sparse_search_defaults_to_sindhi_only_filter():
    client = _FakeQdrantClient(dense_hits=[], sparse_hits=[_FakeHit(1, 0.9)])
    retriever = HybridRetriever(client, embed_fn=_fake_embed)

    retriever.sparse_search("query")

    assert client.filters[0].must[0].match.value == "sd"


def test_fused_search_passes_lang_filter_to_both_legs():
    client = _FakeQdrantClient(
        dense_hits=[_FakeHit(1, 0.9)],
        sparse_hits=[_FakeHit(1, 0.8)],
    )
    retriever = HybridRetriever(client, embed_fn=_fake_embed)

    retriever.fused_search("query", lang="en")

    assert all(f.must[0].match.value == "en" for f in client.filters)


# ---------------------------------------------------------------------------
# cross_lingual_search — Lever 4 cascade: SD dense + SD sparse + EN dense
# ---------------------------------------------------------------------------

class _FakeCrossLingualClient:
    """Distinguishes legs by (using, lang) so cross_lingual_search's three
    queries can be independently canned."""

    def __init__(self, sd_dense, sd_sparse, en_dense):
        self._responses = {
            ("dense", "sd"): sd_dense,
            ("sparse", "sd"): sd_sparse,
            ("dense", "en"): en_dense,
        }
        self.calls = []

    def query_points(self, collection_name, query, using, limit, with_payload, query_filter=None):
        lang = query_filter.must[0].match.value if query_filter else None
        self.calls.append((using, lang))
        hits = self._responses.get((using, lang), [])
        return SimpleNamespace(points=hits[:limit])


def test_cross_lingual_search_queries_all_three_legs():
    client = _FakeCrossLingualClient(
        sd_dense=[_FakeHit(1, 0.9)],
        sd_sparse=[_FakeHit(2, 0.8)],
        en_dense=[_FakeHit(3, 0.7)],
    )
    retriever = HybridRetriever(client, embed_fn=_fake_embed)

    rows = retriever.cross_lingual_search("query", translate_fn=lambda q: "translated")

    assert set(client.calls) == {("dense", "sd"), ("sparse", "sd"), ("dense", "en")}
    ids = {r["answer_id"] for r in rows}
    assert ids == {1, 2, 3}
    assert all(r["path"] == "cross_lingual" for r in rows)


def test_cross_lingual_search_english_leg_rescues_a_miss():
    # id 99 only turns up via the translated English leg -- this is the
    # rescue case Lever 4 exists for.
    client = _FakeCrossLingualClient(
        sd_dense=[_FakeHit(1, 0.9)],
        sd_sparse=[_FakeHit(1, 0.85)],
        en_dense=[_FakeHit(99, 0.6)],
    )
    retriever = HybridRetriever(client, embed_fn=_fake_embed)

    rows = retriever.cross_lingual_search("query", translate_fn=lambda q: "translated")

    assert 99 in {r["answer_id"] for r in rows}


def test_cross_lingual_search_translates_before_english_leg():
    seen_queries = []

    class _RecordingClient(_FakeCrossLingualClient):
        def query_points(self, collection_name, query, using, limit, with_payload, query_filter=None):
            lang = query_filter.must[0].match.value if query_filter else None
            if (using, lang) == ("dense", "en"):
                seen_queries.append(query)
            return super().query_points(collection_name, query, using, limit, with_payload, query_filter)

    client = _RecordingClient(sd_dense=[], sd_sparse=[], en_dense=[_FakeHit(1, 0.9)])
    retriever = HybridRetriever(client, embed_fn=lambda q: {"dense": [q], "sparse": {}})

    retriever.cross_lingual_search("سنڌي سوال", translate_fn=lambda q: f"EN:{q}")

    # embed_fn echoes its input into the dense vector, so we can see the
    # English leg was embedded from the *translated* text, not the original.
    assert seen_queries == [["EN:سنڌي سوال"]]


# ---------------------------------------------------------------------------
# Variant index — weighted RRF, dedupe, and the extra legs
# ---------------------------------------------------------------------------

def test_weights_default_to_plain_rrf():
    """Passing no weights must be byte-identical to the old behaviour."""
    lists = [[1, 2, 3], [3, 1]]
    assert reciprocal_rank_fusion(lists) == reciprocal_rank_fusion(
        lists, weights=[1.0, 1.0]
    )


def test_weight_scales_a_list_contribution():
    half = dict(reciprocal_rank_fusion([[1], [2]], weights=[1.0, 0.5]))
    assert half[1] == 1.0 / (RRF_K + 1)
    assert half[2] == 0.5 / (RRF_K + 1)


def test_zero_weight_removes_a_list_influence():
    """A weight of 0 must make a list inert. reciprocal_rank_fusion() keeps
    this general-purpose parameter even though the variant rescue leg
    (HybridRetriever.fused_search / retrieval.pipeline.search) no longer uses
    per-list weighting -- see those functions' docstrings for why."""
    with_legs = dict(reciprocal_rank_fusion([[1, 2], [9]], weights=[1.0, 0.0]))
    assert with_legs[9] == 0.0
    assert with_legs[1] > with_legs[2]


def test_mismatched_weights_raise():
    try:
        reciprocal_rank_fusion([[1], [2]], weights=[1.0])
    except ValueError as exc:
        assert "2 lists" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_dedupe_keeps_first_occurrence_per_answer_id():
    rows = [
        {"answer_id": 7, "question": "variant a"},
        {"answer_id": 7, "question": "variant b"},
        {"answer_id": 9, "question": "variant c"},
    ]
    out = dedupe_by_answer_id(rows)
    assert [r["answer_id"] for r in out] == [7, 9]
    assert out[0]["question"] == "variant a"   # best-ranked one survives


def test_variant_legs_do_not_double_count_a_row():
    """
    The failure this guards against: a KB row has two variants, both match,
    both land in one ranked list, and RRF awards the row two separate
    1/(k+rank) terms. It would then outrank a row that was simply retrieved
    better, purely for having more paraphrases in the index.
    """
    client = _FakeQdrantClient(
        dense_hits=[_FakeHit(7, 0.9), _FakeHit(7, 0.88), _FakeHit(9, 0.4)],
        sparse_hits=[],
    )
    retriever = HybridRetriever(client, embed_fn=_fake_embed)

    var_dense, _ = retriever.variant_search("query", top_k=25)

    assert [r["answer_id"] for r in var_dense] == [7, 9]


def test_variant_search_filters_on_the_variant_lang():
    client = _FakeQdrantClient(dense_hits=[_FakeHit(1, 0.9)], sparse_hits=[])
    retriever = HybridRetriever(client, embed_fn=_fake_embed)

    retriever.variant_search("query")

    matched = client.filters[0].must[0].match.value
    assert matched == VARIANT_LANG


def test_fused_search_without_variants_never_queries_them():
    """Default off: the existing measured pipeline must be untouched."""
    client = _FakeQdrantClient(
        dense_hits=[_FakeHit(1, 0.9)], sparse_hits=[_FakeHit(2, 0.8)]
    )
    retriever = HybridRetriever(client, embed_fn=_fake_embed)

    rows = retriever.fused_search("query", top_k=5)

    assert client.calls == ["dense", "sparse"]      # two legs, not four
    assert rows[0]["path"] == "fused"


def test_fused_search_with_variants_adds_two_legs_when_room_remains():
    client = _FakeQdrantClient(
        dense_hits=[_FakeHit(1, 0.9)], sparse_hits=[_FakeHit(2, 0.8)]
    )
    retriever = HybridRetriever(client, embed_fn=_fake_embed)

    rows = retriever.fused_search("query", top_k=5, use_variants=True)

    assert client.calls == ["dense", "sparse", "dense", "sparse"]
    assert rows[0]["path"] == "fused"


def test_fused_search_skips_variant_legs_when_canonical_fills_top_k():
    """
    The regression this guards against: a first design let variant legs
    compete with canonical legs for the same fixed top_k slots via weighted
    RRF, and a Colab measurement (eval/variant_index_lift.csv) showed it cost
    0.125 of Recall@1 for a 0.008 gain in Recall@20 -- noisy variant matches
    were outranking correct canonical rows before reranking ever saw them.
    When canonical fusion already fills every slot, there is no room for a
    rescue and the variant legs should not even be queried.
    """
    client = _FakeQdrantClient(
        dense_hits=[_FakeHit(1, 0.9), _FakeHit(2, 0.8)], sparse_hits=[]
    )
    retriever = HybridRetriever(client, embed_fn=_fake_embed)

    rows = retriever.fused_search("query", top_k=2, use_variants=True)

    assert client.calls == ["dense", "sparse"]     # variant legs never queried
    assert [r["answer_id"] for r in rows] == [1, 2]


def test_fused_search_variant_rescue_never_displaces_a_canonical_row():
    """
    A variant match that would rank ABOVE every canonical candidate must
    still never evict one of them -- it may only occupy an otherwise-empty
    slot. This is the property the regression above violated.
    """
    client = _FakeQdrantClient(
        dense_hits=[_FakeHit(1, 0.9)], sparse_hits=[]
    )

    class _Client(_FakeQdrantClient):
        def query_points(self, collection_name, query, using, limit,
                         with_payload, query_filter=None):
            self.calls.append(using)
            self.filters.append(query_filter)
            is_variant = (
                query_filter is not None
                and query_filter.must[0].match.value == VARIANT_LANG
            )
            if is_variant and using == "dense":
                # A variant match for a DIFFERENT row than canonical found,
                # ranked as strongly as possible.
                return SimpleNamespace(points=[_FakeHit(99, 0.99)][:limit])
            return SimpleNamespace(points=(self._dense_hits if using == "dense"
                                          else self._sparse_hits)[:limit])

    retriever = HybridRetriever(_Client([_FakeHit(1, 0.9)], []), embed_fn=_fake_embed)

    rows = retriever.fused_search("query", top_k=1, use_variants=True)

    # top_k=1 and canonical already found one row -- there is no room, so the
    # variant's row 99 must not appear even though it would outrank row 1 in
    # a straight fusion.
    assert [r["answer_id"] for r in rows] == [1]


def test_canonical_payload_wins_over_a_variant_payload():
    """
    A variant point carries its source row's answer, but the canonical row is
    the one whose question was reviewed. When both legs return the same
    answer_id, the displayed row must be the canonical one.
    """
    canonical = _FakeHit(5, 0.9)
    canonical.payload["question"] = "canonical question"
    variant = _FakeHit(5, 0.95)
    variant.payload["question"] = "colloquial variant"

    class _Client(_FakeQdrantClient):
        def query_points(self, collection_name, query, using, limit,
                         with_payload, query_filter=None):
            self.calls.append(using)
            self.filters.append(query_filter)
            is_variant = (
                query_filter is not None
                and query_filter.must[0].match.value == VARIANT_LANG
            )
            hits = [variant] if is_variant else [canonical]
            return SimpleNamespace(points=hits[:limit])

    retriever = HybridRetriever(_Client([], []), embed_fn=_fake_embed)
    rows = retriever.fused_search("query", top_k=5, use_variants=True)

    assert rows[0]["answer_id"] == 5
    assert rows[0]["question"] == "canonical question"
