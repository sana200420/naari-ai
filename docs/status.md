# Project status

**Current phase:** Phase 1 — The retrieval spike

## Who's on what

| Person | Currently | Blocked on |
|---|---|---|
| Sana | Lever 1 (normalisation) done; next: embed 2,000 rows + Qdrant collection | Qdrant Cloud account, Mahnoor's first 100 gold queries for the dense baseline |
| Sabiha | FastAPI skeleton + first deploy | — |
| Tooba | Next.js skeleton, Sindhi font audit | — |
| Mahnoor | Corpus merge, reviewer outreach | — |

## Lever 1 — Script normalisation: done

- `knowledge_base/Womens_Health_KB - 2000_final.csv` cleaned: 2,000 rows, 6 columns, `id` 1–2000, 250/category, zero duplicate questions, zero blank fields
- `docs/adr/0002-normalisation-map.md`: 145-codepoint histogram, keep/map/drop decision for every one
- `retrieval/normalize.py`: `normalize_sd()`, the fixed 7-step pipeline
- `retrieval/embed.py`: `embed_text()` stub — normalises unconditionally before anything else; the only public embedding entry point (model itself not wired up yet)
- `retrieval/tests/`: 52 tests passing — idempotence over all 4,000 question+answer strings, 47 golden fixtures, non-destruction (0 collisions), embed-gating check
- CI (`.github/workflows/ci.yml`) now actually runs `pytest retrieval/` on every PR
- **Open:** Recall@5 with/without normalisation — blocked on embeddings + gold queries, tracked in the ADR

## Latest eval numbers

Not yet measured.

## Variant review burn-down

Not yet started.

---
*Update this file when reality changes, not on a schedule.*
