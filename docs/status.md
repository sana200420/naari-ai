# Project status

**Current phase:** Phase 2 — Make it a service. Phase 1 checklist fully closed 2026-09-01 (GO, fused Recall@5 = 0.971). Phase 2 started same day: `retrieval/pipeline.py`'s `search()` built. Live-verified 2026-09-02: warm loading/latency/memory effectively done (a real GPU-device bug in NLLB was found and fixed along the way — was 25000-60000ms/query, now ~1s). **Blocked on gold-set quality, not code:** τ threshold tuning (Lever 5) can't produce a usable τ_high — correct/incorrect score distributions overlap too heavily, because 146/275 gold rows were never individually reviewed (only the original 24 flagged ones were). **This is now the top-priority next task** — it's blocking both threshold tuning and a clean read on the conditional-English-leg comparison.

## Who's on what

| Person | Currently | Blocked on |
|---|---|---|
| Sana | Levers 1, 3, 4 done and measured; reranking (item 8) built and measured; Sindhi+English fully embedded (4000/4000 points, verified live); gold eval set at 296 rows (275 original + 25 new, individually reviewed); Phase 1 go/no-go is a GO, checklist fully closed; Phase 2: pipeline.py latency/memory fixed and verified, τ threshold tuning blocked on the ~146 legacy rows that were never individually reviewed (only bulk category-matched) | Gold-set review of the remaining ~146 legacy rows — top priority, blocking Lever 5 threshold tuning |
| Sabiha | FastAPI skeleton + first deploy | — |
| Tooba | Next.js skeleton, Sindhi font audit | — |
| Mahnoor | Corpus merge landed; variant + eval pipeline landed but partial (see below) | Reviewer outreach and real-question harvesting not started yet |

## Lever 1 — Script normalisation: done

- `knowledge_base/Womens_Health_KB - 2000_final.csv` cleaned: 2,000 rows, 6 columns, `id` 1–2000, 250/category, zero duplicate questions, zero blank fields
- `docs/adr/0002-normalisation-map.md`: 145-codepoint histogram, keep/map/drop decision for every one
- `retrieval/normalize.py`: `normalize_sd()`, the fixed 7-step pipeline
- `retrieval/embed.py`: `embed_text()` — real `BGEM3FlagModel` implementation, normalises unconditionally before anything else, the only public embedding entry point
- `retrieval/tests/`: 74 tests passing — idempotence over all 4,000 question+answer strings, 47 golden fixtures, non-destruction (0 collisions), embed-gating check
- CI (`.github/workflows/ci.yml`) now runs `pytest retrieval/ data/tests/` and `eval/run_eval.py` on every PR, fixed to work with bare `pytest` (not just `python -m pytest`)

## Lever 3 — Hybrid dense + sparse + RRF: done

- `retrieval/search.py`: `HybridRetriever` (dense/sparse/fused search against Qdrant) + `reciprocal_rank_fusion`, tested against fakes and verified against the live collection
- Sindhi KB (2000 rows) + English KB (1999/2000 rows) embedded into Qdrant Cloud collection `naari_ai_kb`: named `dense` (1024-d cosine) + `sparse` vectors, `lang` payload field (`sd`/`en`) with a payload index, shared `answer_id` join key across languages
- **Final ablation table (`eval/results.md`, 2026-09-01), 275-query human-reviewed gold set, `lang="sd"` bug fixed:**

  | Leg | Recall@1 | Recall@5 | Recall@20 |
  |---|---:|---:|---:|
  | dense | 0.462 | 0.880 | 0.975 |
  | sparse | 0.542 | 0.898 | 0.971 |
  | fused | 0.967 | 0.971 | 0.975 |

  Fused clears the Phase 1 exit gate (≥0.85) comfortably. Getting here took two real bugs found and fixed along the way: (1) `dense_search`/`sparse_search` had no `lang` filter, so a "Sindhi-only" search was silently mixing in English points once the English KB shared the collection — fixed by defaulting to `lang="sd"`; (2) the first two re-run attempts of the Colab notebook silently kept using stale pre-fix code (`git pull` run from the wrong directory, then Python's module cache not reloaded, then a reconnected Colab tab reusing an already-stale VM) — fixed by making the notebook re-clone unconditionally and reload modules explicitly rather than trusting `git pull`.
- `retrieval/translate.py` + `HybridRetriever.cross_lingual_search()` (Lever 4 cascade): built and measured. Of 8 Sindhi-only misses in the corrected gold set, English rescued **0 (0%)** — small sample, but a real number, not yet a flattering one. Worth checking the actual NLLB translations on those 8 before Phase 2 makes this leg conditional.
- **Prefix convention empirically confirmed:** no-prefix Recall@1 0.552 vs. prefixed 0.431 on the same candidate pool — confirms ADR 0001, bge-m3 needs none.
- **Reranking (item 8):** `retrieval/rerank.py` (`bge-reranker-v2-m3`) built and measured. Raw Recall@1 dropped to 0.385, which looked alarming — but a 40-row manual audit of the disagreements (`eval/rerank_regression_audit.csv`) found the reranker was right about as often (12/40) as genuinely wrong (11/40), with another 12/40 cases where fused's own top-1 was *also* wrong (i.e. the never-individually-reviewed gold rows, not reranking, are the actual weak point) and 5/40 near-duplicate-content ties. One real, occasional weakness confirmed: cross-category confusion from surface phrase overlap. Latency is well inside budget (p95 112ms/20 candidates). **Flag before Phase 2:** don't feed reranking's raw Recall@1 into Lever 5 threshold tuning until the remaining ~146 gold rows get the same individual review the original 24 got.

## Gold eval set — 296 rows, partially reviewed

- `eval/gold_eval_280_linked.csv`: original 280 gold questions linked via fused search, folded down to 275 after full human review — 129 category-mismatch/low-confidence rows triaged against `docs/PLAYBOOKS.md`'s category-boundary rules down to 24 genuine unknowns, each manually re-searched against the full KB (`eval/gold_eval_280_needs_review_enriched.csv`): 9 corrections, 5 drops, 10 confirmed-OK, 105 confirmed-OK-in-bulk (this last 105 is the **unreviewed-at-the-individual-row-level chunk** blocking τ threshold tuning, see Phase 2 note above)
- 2026-09-02: Mahnoor's 25 new independently-written questions (`eval/New_25_Gold_Questions.csv`) reviewed individually — 11 confirmed OK, 10 corrected to a better KB match (full reasoning in `eval/new25_review_final.csv`), 4 dropped as genuine KB content gaps (postpartum swelling, first-labor duration, period symptoms at work, PMS breast tenderness — worth a content-team follow-up). **275 → 296 rows**, 4 short of the 300 target. These 21 are now fully individually reviewed — the still-unreviewed ~146 are all from the original 280, not these.
- `New_300_Womens_Health_Gold_Set_KB.csv` (a separate attempt) was rejected — every one of its 300 questions was a byte-identical copy of an existing KB question, unusable as an independent gold set

## Lever 2 / data & eval pipeline — landed, partial

Mahnoor's `data/build_corpus.py` + eval pipeline is landed in `/data` and `/eval`. Details and dataset sizes: `eval/results.md`.

- `data/processed/final_corpus.csv`: 2,000 rows, schema-validated, 0 duplicates — ready for embedding
- `eval/out_of_scope_eval.csv`: 100 rows, 20/scope-type — **fixed** a generator bug that had produced only 4 distinct queries per type repeated to pad to 20 (80% exact duplicates); regression tests added in `data/tests/test_eval_sets.py`
- `eval/run_eval.py`: harness works end-to-end for dataset sizes; retrieval/safety metrics correctly report "NOT AVAILABLE" rather than fabricating numbers until predictions exist — **fixed** a crash when the (expected-missing) danger-sign file isn't present yet
- `eval/negative_set_100.csv`, `eval/danger_sign_eval_100.csv`, `eval/out_of_scope_eval_v2_100.csv`: newer deliverables from Mahnoor, verified clean (0 dup, 0 blank)
- `data/variants/colloquial_variants.csv`: smoke-test batch only, answer_id 1–30 of ~2000 (resumable via `_progress.json`)
- Danger-sign eval set: correctly not generated — blocked on an approved clinical source file, not fabricated

## Latest eval numbers

See `eval/results.md`. Provisional dense/sparse/fused ablation exists; final numbers against the human-reviewed 275-query gold set are queued but not yet run (needs a live Colab pass with GPU + the bge-m3 model — local machine is RAM-constrained).

## Variant review burn-down

Not yet started — variant generation itself is only ~1.5% complete (30/2000 answer_ids).

---
*Update this file when reality changes, not on a schedule.*
