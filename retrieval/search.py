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


def reciprocal_rank_fusion(ranked_lists: list[list], k: int = RRF_K) -> list[tuple]:
    """Fuse multiple best-first ranked lists of IDs by Reciprocal Rank Fusion.

    score(id) = sum over lists containing id of 1 / (k + rank_in_that_list)

    An id absent from a list contributes nothing from that list — it is not
    penalised beyond simply not getting that list's points.

    Returns (id, fused_score) pairs sorted best-first. Ties broken by id for
    determinism.
    """
    scores: dict = {}
    for ranked in ranked_lists:
        for rank, item_id in enumerate(ranked, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))


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

    def fused_search(self, query: str, top_k: int = 5, leg_k: int = 25, lang: str | None = "sd") -> list[dict]:
        dense_rows = self.dense_search(query, top_k=leg_k, lang=lang)
        sparse_rows = self.sparse_search(query, top_k=leg_k, lang=lang)

        row_by_id = {}
        for row in dense_rows + sparse_rows:
            row_by_id.setdefault(row["answer_id"], row)

        dense_ranked = [row["answer_id"] for row in dense_rows]
        sparse_ranked = [row["answer_id"] for row in sparse_rows]
        fused = reciprocal_rank_fusion([dense_ranked, sparse_ranked])

        results = []
        for answer_id, fused_score in fused[:top_k]:
            row = dict(row_by_id[answer_id])
            row["score"] = fused_score
            row["path"] = "fused"
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
