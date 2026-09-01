# Project status

**Current phase:** Phase 1 — The retrieval spike (Sana: items 1/2/3/4/6 of the Phase 1 checklist in `docs/PLAYBOOKS.md` done or superseded; 5/7/8/9 open)

## Who's on what

| Person | Currently | Blocked on |
|---|---|---|
| Sana | Levers 1 and 3 done and tested; Sindhi+English embedded (3999/4000 points); gold eval set human-reviewed and folded in (280→275 rows); next: prefix verification, Lever 4 query-time cascade, reranking, go/no-go | One English translation short (KB `id=2000`, a backfilled row with no source translation) for a full 4000-point collection |
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
- Ablation table (dense/sparse/fused Recall@1/5/20) in `eval/results.md` — provisional pass measured fused against its own top-1, **and** predates a bug fix (2026-09-01): `dense_search`/`sparse_search` had no `lang` filter, so once the English KB shared the collection, a "Sindhi-only" search was silently mixing in English points, double-counting some answer_ids in RRF. Fixed. A final pass against the human-reviewed 275-query gold set, with the fix applied, is queued in `retrieval/scripts/link_and_baseline_gold_queries.ipynb` but needs a live Colab run to produce real numbers.
- `retrieval/translate.py` + `HybridRetriever.cross_lingual_search()` (Lever 4 cascade: SD dense + SD sparse + translated-query EN dense) built and unit-tested against fakes — still needs a live Colab run to measure the actual English-rescue fraction the checklist item asks for.

## Gold eval set — reviewed

- `eval/gold_eval_280_linked.csv`: 280 gold questions linked to `correct_answer_id` via fused search, now folded down to 275 rows after full human review — 129 category-mismatch/low-confidence rows triaged against `docs/PLAYBOOKS.md`'s category-boundary rules down to 24 genuine unknowns, each manually re-searched against the full KB (`eval/gold_eval_280_needs_review_enriched.csv`): 9 corrections, 5 drops, 10 confirmed-OK, 105 confirmed-OK-in-bulk
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
