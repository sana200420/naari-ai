# ADR 0001 — Initial stack decisions

**Status:** accepted · **Date:** 2026-08-30 · **Author:** Sana

Record what we chose, what we rejected, and why. Fill each section in as the
decision is actually made — not afterwards from memory.

## Embedding model
**Chosen:** BAAI/bge-m3
**Rejected:** intfloat/multilingual-e5-large
**Why:** bge-m3's backbone is XLM-R, which was pretrained on Sindhi (unlike
many multilingual models that skip low-resource languages entirely). It also
returns dense *and* sparse (lexical) vectors from a single forward pass,
which is what makes Lever 3 (hybrid dense+sparse retrieval) affordable —
e5-large would need a second model or a hand-rolled sparse method for the
same result. e5 also requires exact `"query: "`/`"passage: "` prefix
conventions that are easy to get backwards and silently tank recall; bge-m3
has no such prefix requirement, which removes one whole class of bug. Kept
as the documented fallback in case bge-m3's Sindhi coverage turns out too
weak in the Phase 1 baseline (see Risk 1 in `PLAYBOOKS.md`).

## Vector store
**Chosen:** Qdrant Cloud free tier
**Rejected:** FAISS in-process
**Why:** Qdrant natively supports named dense + sparse vectors on the same
point with server-side fusion, which is exactly the shape Lever 3 needs —
FAISS would require running two separate indexes and fusing client-side
ourselves. At the scale this project runs at (2,000 KB rows, ~10k once
Lever 2's variants are indexed) the free 1GB tier is comfortably enough
headroom, and a managed service means one less piece of infrastructure a
four-person team has to keep alive. FAISS stays the documented fallback if
Qdrant's free tier or reliability becomes a problem mid-project.

## Backend hosting
**Chosen:** Hugging Face Spaces (Docker, free CPU)
**Rejected:** Render free, Fly.io
**Why:** This is the only free tier in the comparison with enough RAM
(16GB) to hold a 568M-parameter embedding model *and* a reranker resident in
memory between requests without cold-loading them on every call — Render and
Fly's free tiers cap out well below that, which would push latency past the
3-second target on every single request. Docker support means the same
container config works locally and in production.

## Generation model
**Chosen:** Gemini 2.5 Flash free tier
**Rejected:** Groq Llama 3.3 70B (kept as fallback)
**Why:** Of the free-tier options, Gemini 2.5 Flash has the strongest
Sindhi comprehension, which matters because it's only ever asked to
constrained-stitch already-retrieved Sindhi text, not generate freely — poor
comprehension there would mean paraphrasing errors slipping into a health
answer. Groq's Llama 3.3 70B is kept wired up as an automatic fallback
(Risk 3 in `PLAYBOOKS.md`) for when Gemini rate-limits, since the generation
step is deliberately a minority path anyway — most traffic should resolve
through the verbatim path and never call an LLM at all.
