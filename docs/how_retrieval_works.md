# How Retrieval Works

*Naari AI — retrieval core*

What happens between a woman typing a question in Sindhi and an answer coming back: each stage, why it exists, and what breaks without it.

**Who this is for.** Sections 1 and 2 are for the team — section 1 is the contract the API depends on, and section 2 says which stage owns which failure, so a bug lands with the right person. Sections 3 and 4 are for the report and viva — the design rationale for each choice over its obvious alternative, with the measured evidence behind it.

Owner: Sana (retrieval core). Contract: `docs/contracts/retrieval.json`. All figures: `eval/results.md`.

---

## 1. The contract

Everything in this document sits behind a single call. The API never touches Qdrant, an embedding model, or a reranker directly — it calls this, and gets back the same shape every time.

```python
from retrieval.pipeline import search

result = search("حيض جي چڪر ڇا آهي؟")

{
  "query_normalised": str,   # after normalize_sd(), for logs
  "latency_ms": int,
  "results": [{
     "answer_id": int,       # the KB id, stable across languages
     "question": str,        # the KB question that matched
     "answer": str,          # the Sindhi answer text
     "category": str, "sub_category": str, "source": str,
     "score": float,         # reranked relevance, higher is better
     "path": str,            # which retrieval leg found it
  }]
}
```

### Three guarantees

**The query is normalised for you.** Pass the raw user string. `search()` calls `normalize_sd()` internally, exactly as `embed_text()` does — nobody downstream should normalise twice or forget to.

**`answer_id` is the join key.** It matches the KB `id` column and is stable across Sindhi, English and any future variant rows. Log it, cache on it, evaluate against it.

**Empty results are not an error.** No match returns `"results": []`, never an exception. The band logic treats that as low confidence and refuses honestly.

## 2. The stages

Each stage below lists what it does, why it exists, and what breaks without it.

### 2.1 Normalisation

*retrieval/normalize.py*

- **Does.** Folds the Arabic-script variants a Sindhi keyboard produces: Yeh forms, the Urdu word-final Heh, Urdu-keyboard Kaf slips, typographic quotes, Arabic-Indic digits.
- **Why.** The same word typed on two keyboards is two different byte strings. Without folding, they are two different vectors.
- **Remove it.** Retrieval silently degrades for exactly the users on cheap phones with mixed keyboards — the intended audience.

### 2.2 Dense search

*bge-m3, 1024-d*

- **Does.** Embeds the query and finds the 25 nearest KB questions by meaning, filtered to lang="sd".
- **Why.** Catches paraphrase: a question worded completely differently still lands near its answer.
- **Remove it.** Only exact word matches work. Any rephrasing fails.

### 2.3 Sparse search

*bge-m3 lexical head*

- **Does.** Learned term weights over the same 25-deep shortlist — the same model, one forward pass, two vectors.
- **Why.** Dense embeddings blur rare specifics. A drug name, a body part, an exact Sindhi term survives here when it gets smoothed away there.
- **Remove it.** Rare-term questions drift to topically similar but wrong rows. Sparse alone scores 0.542 Recall@1 — it is not a garnish.

### 2.4 Reciprocal Rank Fusion

*k = 60*

- **Does.** Merges the two ranked lists using only each row's position: score contribution is 1/(k + rank), summed across lists.
- **Why.** Dense cosine and sparse term weights are not on a comparable scale. Rank is the one thing both lists agree on the meaning of.
- **Remove it.** You must hand-tune a blend weight per query type, and it silently rots as the knowledge base grows.

### 2.5 Cross-encoder rerank

*bge-reranker-v2-m3*

- **Does.** Scores every fused candidate as a (query, question) pair, rather than comparing two independently made vectors.
- **Why.** A cross-encoder sees both texts at once and can judge relevance a bi-encoder cannot.
- **Remove it.** You lose the score the confidence bands are calibrated on — and on this knowledge base, that score is now its main job (see section 3).

### 2.6 English rescue leg

*NLLB-600M, conditional*

- **Does.** Only when the Sindhi reranked top score is below tau_high: translate the query to English and search the aligned English knowledge base.
- **Why.** The English rows are better written, so an unclear Sindhi question sometimes matches its English twin when its Sindhi original fails.
- **Remove it.** Of 20 sampled Sindhi-only misses, this rescued 4. Conditional costs nothing over always-on: identical Recall@1, 543 ms faster per query.

## 3. Why, not what

### Why rank fusion instead of blending scores

The obvious approach is a weighted blend, alpha times dense plus one minus alpha times sparse. It requires the two scores to mean comparable things, and they do not: cosine similarity sits in a narrow band near 1, while learned term weights are unbounded and vary with query length. Any alpha that works for a short question fails for a long one. Reciprocal Rank Fusion needs no calibration because it discards magnitude and keeps only order.

### Why the reranker no longer picks the answer

Auditing 58 wrong-but-confident answers found the correct row had frequently been ranked first by fusion and then demoted by reranking. Across the 139 queries where the two disagreed, fusion was right 61 times and the reranker 10 — roughly 6:1 against trusting the override.

That could have been noise, so the 139 were split randomly in half: 30:5 in one half, 31:5 in the other. The ratio holds independently, which makes it a property of this reranker on this knowledge base rather than a threshold fitted to a lucky split. `RERANK_OVERRIDE_MARGIN=2.0` sits deliberately outside the range a normalised score gap can reach, so fusion's pick always wins a disagreement. Recall@1 moved from 0.339 to 0.540.

> Consequence worth stating plainly: the reranker no longer selects any answer. It exists now to produce the score the confidence bands read. Removing it would save 2.3 GB of memory and change no answer — but tau_low is calibrated on its scores, so that swap needs a recalibration run first.

### Why the high band asks instead of asserting

A threshold was wanted that could serve a stored answer as fact. Ten-fold cross-validation says none exists: no signal or combination exceeds roughly 83.6% precision at 24.6% coverage, and precision drops at stricter cutoffs — the signature of a real ceiling, not an unexplored trade-off. Live testing agreed: 4 of 11 menstruation questions returned high-confidence wrong answers, including breastfeeding advice for a question about nausea.

83.6% is unacceptable for asserting and entirely reasonable for suggesting. So the high band returns the matched question for confirmation, and the answer appears once she agrees that is what she asked. A wrong match becomes a visibly wrong question she can reject, instead of misinformation.

### Why float32, after building the int8 version

ONNX int8 quantisation was exported, benchmarked and rejected. Latency passed comfortably — 292 ms p95 against a 1500 ms budget — but Recall@1 fell 2.42 points against a 1.0-point allowance. The optimisation was real; the accuracy cost was not affordable on a health knowledge base.

## 4. Evidence

Measured on 248 individually verified queries.

| Measurement | Value | Reading |
|---|---:|---|
| Recall@1, final pipeline | 0.540 | up from 0.339 before the override guard |
| Recall@20, fused shortlist | 0.726 | the right answer is usually already there |
| Recall@1, KB's own questions | 0.979 | asking the KB a question it already contains |
| Sparse leg alone | 0.542 | why sparse is not optional |
| tau_low | 0.2034 | 90 of 100 out-of-scope queries fall below |
| tau_high precision ceiling | 83.6% | at 24.6% coverage — why the band now asks |

**The gap that defines the next phase: 0.979 against 0.540.** Asked in the knowledge base's own words, retrieval is near-perfect. Asked in a woman's words, it is roughly a coin flip. That 44-point gap is not a model problem — it is a coverage problem in how many ways each question can be asked, and it is exactly what genuine colloquial variants are meant to close.

## 5. Known limits

### 27% of queries have no reachable answer

They never surface the correct row anywhere in the top 20, so no amount of reranking or threshold tuning reaches them. This is a knowledge base coverage gap and needs content, not retrieval work.

### tau_high is one variable doing two jobs

api/pipeline.py reads it as the confidence band threshold; retrieval/pipeline.py reads it as the English-leg cascade gate. Setting it changes both. They should be split before either is tuned.

### Variants are not in the index

The 10,059-row batch reuses each original question's wording verbatim under about 95 prefix templates, so it adds no phrasing diversity. Measured: prefixed questions score 0.969 against 0.979 plain — harmless, but redundant.

### Latency is 3 to 8 seconds

Against a 3-second target, on two shared CPU cores with roughly 8.5 GB of models resident. The architecture is not the constraint; the free hosting tier is.

---

*Generated by `scripts/build_retrieval_doc.py`. Edit the script, not this file.*
