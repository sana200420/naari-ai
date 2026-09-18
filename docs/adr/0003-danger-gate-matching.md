\# ADR 0003: Danger Gate Matching — Embedding Path Disabled



\## Status

Accepted (2026-09)



\## Context

The danger-sign gate originally used two matching paths: keyword/token-bag

matching, and embedding-similarity matching as a semantic fallback for

phrasings that share no keyword with the danger phrase bank.



After Sabiha's token-bag generalisation fix (commit dfcd1f2, tolerates

word-order and connector changes) and the addition of 33 keywords from

Sana's Phase 3 miss list, the keyword-only path was re-measured against

the full danger set (`eval/run\_danger\_gate\_eval.py`).



\## Measurement



Embedding threshold sweep (cosine similarity), against the danger set and

a negative set of ordinary health questions:



| threshold | danger recall (embedding-dependent rows) | negative FP rate |

|---|---|---|

| 0.86 | 1.000 | 0.150 |

| 0.88 | 1.000 | 0.130 |

| 0.90 | 1.000 | 0.130 |

| 0.92 | 1.000 | 0.100 |

| 0.94 | 1.000 | 0.060 |

| 0.96 | 1.000 | 0.030 |

| 0.98 | 1.000 | 0.000 |



Key finding: with the token-bag fix and added keywords, the keyword path

alone reaches 100/100 recall on the danger set. Rows that previously

depended on the embedding path dropped from 3/100 to 0/100.



Measured cost of keeping the embedding path active: \~15.5ms/question

(2.0ms keyword-only vs 17.5ms with embedding enabled), for zero

additional recall on the current eval set.



\## Decision



The embedding-similarity path is \*\*disabled\*\* in production

(`api/pipeline.py`, `run\_danger\_gate(query, use\_embedding=False)`), but

not deleted. `EMBEDDING\_THRESHOLD` is kept at 0.96 — the lowest value

that holds recall at 1.00 with an acceptable \~3% false-positive rate —

so the path can be re-enabled without re-deriving the threshold.



\## When to revisit



\- A future case the keyword/token-bag path genuinely can't reach

\- Once `\_build\_embedding\_reference()` is curated down to fewer,

&#x20; more clinically-distinctive anchors per category



Re-run the threshold sweep after any change to `DANGER\_CATEGORIES` or

`\_build\_embedding\_reference()` and update the table above.



\## Note on script provenance



The sweep above was run manually; `eval/tune\_embedding\_threshold.py`

(referenced in the `danger\_gate.py` code comment) was not committed at

the time. A minimal reproducible version has been added in this same

change — see that file for the sweep logic.

