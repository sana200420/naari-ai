"""Hybrid dense + sparse retrieval with Reciprocal Rank Fusion (Lever 3).

Dense embeddings blur rare/specific words — exactly what a low-resource
language like Sindhi is full of. Sparse (lexical) retrieval catches what
dense similarity misses. RRF fuses the two ranked lists without needing to
calibrate two differently-scaled scores against each other.

See docs/PLAYBOOKS.md, Lever 3, for the method and the ablation-table
requirement this module exists to produce.
"""

from qdrant_client import models

from retrieval.embed import embed_text
from retrieval.translate import translate_sd_to_en

RRF_K = 60
COLLECTION = "naari_ai_kb"

# Variant points live in the same collection as the canonical rows, separated
# only by this lang value. Keeping them in one collection means a variant hit
# already carries its source row's payload, so it fuses on answer_id with no
# join step -- and because every existing search filters lang="sd", variants
# are invisible to the current paths until something opts in.
VARIANT_LANG = "sd_var"


def reciprocal_rank_fusion(
    ranked_lists: list[list], k: int = RRF_K, weights: list[float] | None = None
) -> list[tuple]:
    """Fuse multiple best-first ranked lists of IDs by Reciprocal Rank Fusion.

    score(id) = sum over lists containing id of w_list / (k + rank_in_that_list)

    An id absent from a list contributes nothing from that list — it is not
    penalised beyond simply not getting that list's points.

    `weights` scales each list's contribution and defaults to 1.0 for every
    list, which is plain RRF. It exists for the variant legs: variants are
    paraphrases of a question rather than the vetted question itself, so
    whether they should count as much as the canonical legs is an empirical
    question. A weight makes that tunable from the outside instead of
    requiring a code change to answer it.

    Returns (id, fused_score) pairs sorted best-first. Ties broken by id for
    determinism.
    """
    if weights is None:
        weights = [1.0] * len(ranked_lists)
    if len(weights) != len(ranked_lists):
        raise ValueError(
            f"weights has {len(weights)} entries for {len(ranked_lists)} lists"
        )
    scores: dict = {}
    for ranked, weight in zip(ranked_lists, weights):
        for rank, item_id in enumerate(ranked, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + weight / (k + rank)
    return sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))


def dedupe_by_answer_id(rows: list[dict]) -> list[dict]:
    """Collapse rows to one per answer_id, keeping the best-ranked occurrence.

    Mandatory for the variant legs and the reason they are not simply passed
    to RRF as-is. Each KB row has two variants, so a single answer_id can
    occupy several positions in one variant ranked list, and RRF adds a
    separate 1/(k+rank) term for every occurrence — a row would collect points
    for being retrieved twice rather than for being retrieved well. That is
    the same double-counting the lang filter exists to prevent for English
    twins, arriving by a different door.
    """
    seen: dict = {}
    for row in rows:
        seen.setdefault(row["answer_id"], row)
    return list(seen.values())


def _lang_filter(lang: str | None):
    if lang is None:
        return None
    return models.Filter(must=[models.FieldCondition(key="lang", match=models.MatchValue(value=lang))])


class HybridRetriever:
    """Dense + sparse retrieval against the naari_ai_kb Qdrant collection.

    Sindhi and English points share the same collection and the same named
    `dense`/`sparse` vectors, distinguished only by a `lang` payload field
    ("sd"/"en"). Every search here defaults to `lang="sd"` — without that
    filter, English twins of the same answer_id silently mix into a
    "Sindhi-only" search's results, which both crowds out other distinct
    answer_ids from the top-k window and double-counts a single answer_id
    across two points when RRF-fusing (each occurrence in a ranked list adds
    its own 1/(k+rank) term). Pass lang="en" or lang=None explicitly for the
    Lever 4 cross-lingual leg or an intentionally unfiltered search.

    The embed function is injected (defaults to the real embed_text, which
    calls normalize_sd() internally) so this class is testable against a
    fake embedder + fake Qdrant client without loading bge-m3.
    """

    def __init__(self, qdrant_client, collection: str = COLLECTION, embed_fn=embed_text):
        self.client = qdrant_client
        self.collection = collection
        self.embed_fn = embed_fn

    def dense_search(self, query: str, top_k: int = 25, lang: str | None = "sd") -> list[dict]:
        vec = self.embed_fn(query)
        hits = self.client.query_points(
            collection_name=self.collection,
            query=vec["dense"],
            using="dense",
            limit=top_k,
            with_payload=True,
            query_filter=_lang_filter(lang),
        ).points
        return [self._hit_to_row(h) for h in hits]

    def sparse_search(self, query: str, top_k: int = 25, lang: str | None = "sd") -> list[dict]:
        vec = self.embed_fn(query)
        sparse_vector = models.SparseVector(
            indices=[int(idx) for idx in vec["sparse"].keys()],
            values=[float(v) for v in vec["sparse"].values()],
        )
        hits = self.client.query_points(
            collection_name=self.collection,
            query=sparse_vector,
            using="sparse",
            limit=top_k,
            with_payload=True,
            query_filter=_lang_filter(lang),
        ).points
        return [self._hit_to_row(h) for h in hits]

    def variant_search(self, query: str, top_k: int = 25) -> tuple[list[dict], list[dict]]:
        """Dense and sparse legs over the variant points, deduped by answer_id.

        Variants are colloquial rewordings of each KB question. The canonical
        questions are FAQ-shaped and the gold queries are not, which is the
        gap this index closes: Recall@20 sits at 0.762 while Recall@1 is
        0.528, so for three-quarters of queries the right row is already
        reachable and merely not first. A variant that matches how a woman
        actually phrases something gives that row a second, better-matching
        surface to be found by.

        Returns (dense_rows, sparse_rows) rather than a fused list so the
        caller decides how to weight them against the canonical legs.
        """
        dense_rows = self.dense_search(query, top_k=top_k, lang=VARIANT_LANG)
        sparse_rows = self.sparse_search(query, top_k=top_k, lang=VARIANT_LANG)
        return dedupe_by_answer_id(dense_rows), dedupe_by_answer_id(sparse_rows)

    def fused_search(
        self,
        query: str,
        top_k: int = 5,
        leg_k: int = 25,
        lang: str | None = "sd",
        use_variants: bool = False,
        variant_weight: float = 1.0,
    ) -> list[dict]:
        dense_rows = self.dense_search(query, top_k=leg_k, lang=lang)
        sparse_rows = self.sparse_search(query, top_k=leg_k, lang=lang)

        ranked_lists = [
            [row["answer_id"] for row in dense_rows],
            [row["answer_id"] for row in sparse_rows],
        ]
        weights = [1.0, 1.0]
        all_rows = dense_rows + sparse_rows

        if use_variants:
            var_dense, var_sparse = self.variant_search(query, top_k=leg_k)
            ranked_lists += [
                [row["answer_id"] for row in var_dense],
                [row["answer_id"] for row in var_sparse],
            ]
            weights += [variant_weight, variant_weight]
            # Canonical rows are appended FIRST above, so setdefault below keeps
            # the canonical payload for any answer_id both legs found. A variant
            # point's payload carries its source row's answer text, but the
            # canonical row is the one whose question was vetted -- it is what
            # should be shown and what the reranker should score.
            all_rows = all_rows + var_dense + var_sparse

        row_by_id = {}
        for row in all_rows:
            row_by_id.setdefault(row["answer_id"], row)

        fused = reciprocal_rank_fusion(ranked_lists, weights=weights)

        results = []
        for answer_id, fused_score in fused[:top_k]:
            row = dict(row_by_id[answer_id])
            row["score"] = fused_score
            row["path"] = "fused_variants" if use_variants else "fused"
            results.append(row)
        return results

    def cross_lingual_search(
        self,
        query: str,
        top_k: int = 5,
        leg_k: int = 25,
        translate_fn=translate_sd_to_en,
    ) -> list[dict]:
        """Lever 4: Sindhi dense + Sindhi sparse + translated-query English
        dense, fused by answer_id (the join key shared across languages).

        Unconditional for Phase 1 (always runs the English leg) so its rescue
        rate can be measured; Phase 2 makes it conditional on the Sindhi leg's
        confidence to save the translation cost on the common case.
        """
        sd_dense_rows = self.dense_search(query, top_k=leg_k, lang="sd")
        sd_sparse_rows = self.sparse_search(query, top_k=leg_k, lang="sd")
        en_query = translate_fn(query)
        en_dense_rows = self.dense_search(en_query, top_k=leg_k, lang="en")

        row_by_id = {}
        for row in sd_dense_rows + sd_sparse_rows + en_dense_rows:
            row_by_id.setdefault(row["answer_id"], row)

        ranked_lists = [
            [row["answer_id"] for row in sd_dense_rows],
            [row["answer_id"] for row in sd_sparse_rows],
            [row["answer_id"] for row in en_dense_rows],
        ]
        fused = reciprocal_rank_fusion(ranked_lists)

        results = []
        for answer_id, fused_score in fused[:top_k]:
            row = dict(row_by_id[answer_id])
            row["score"] = fused_score
            row["path"] = "cross_lingual"
            results.append(row)
        return results

    @staticmethod
    def _hit_to_row(hit) -> dict:
        payload = hit.payload
        return {
            "answer_id": payload["answer_id"],
            "category": payload["category"],
            "sub_category": payload["sub_category"],
            "question": payload["question"],
            "answer": payload["answer"],
            "source": payload["source"],
            "review_tier": payload["review_tier"],
            "score": hit.score,
        }
