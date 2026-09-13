# /data — corpus, variants, evaluation inputs (Mahnoor)

## Layout
- `raw/` — per-owner source CSVs (see `raw/README.md`)
- `build_corpus.py` — reproducible build: `python data/build_corpus.py <input_csv> <output_csv> <report_md>`. Never hand-edit `processed/final_corpus.csv` — edit a source and rebuild.
- `processed/final_corpus.csv` + `validation_report.md` — the merged, schema-validated corpus (2000 rows) and its build report
- `variants/` — colloquial question variants for Lever 2 (`colloquial_variants.csv`, generation report, resumable `_progress.json`, `variants_needing_review.csv`)
- `tests/` — pytest coverage for the corpus and eval sets (`../eval/`)

## Normalization lives in `retrieval/`, not here
Sindhi script normalisation (Lever 1) is intentionally **not** duplicated in `data/` — the
project rule is one normaliser, imported everywhere, so index-time and query-time text stay
identical (see `docs/PLAYBOOKS.md`, Lever 1). The canonical implementation is
`retrieval/normalize_sd()` (Sana), with its own tests in `retrieval/tests/`. A second
`normalization.py` produced from an earlier pipeline draft was deliberately left out of this
folder to avoid two competing normalisers silently drifting apart.

## Known open items (see `eval/results.md` for the full list)
- Gold eval set needs an independently-harvested real-question source
  (`variants/seed_real.csv`) — not started yet.
- Variant generation is at answer_id 30/~2000 (smoke-test batch).
- Danger-sign eval set blocked on an approved clinical source file.
