# Corpus Validation Report

- Original row count: 2000
- Invalid rows (null/empty question or answer, excluded): 0
- Exact duplicate rows (removed): 0
- Duplicate answer_id (NOT removed, needs manual review): 0
- Duplicate questions (NOT removed, flagged for review): 0
- Final row count: 2000
- Schema validation: PASSED (['answer_id', 'category', 'subcategory', 'question', 'answer', 'sources'])

**Note:** the input to this build was already the cleaned, deduplicated
`knowledge_base/Womens_Health_KB - 2000_final.csv` (Lever 1 cleanup, same day) — this run
only renamed columns to the target schema and re-validated; it did not re-merge the four
members' raw per-owner source files. That per-owner merge/dedup work still needs to happen
if `data/raw/` is populated with the four separate 500-row files per `data/raw/README.md`.

