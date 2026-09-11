"""
eval/tune_embedding_threshold.py

Sets api.safety.danger_gate.EMBEDDING_THRESHOLD by measurement instead of
guesswork. The constant was previously hardcoded to 0.75 with no recorded
justification.

Method (same shape as Lever 5's confidence-gate tuning, applied here to the
danger gate's embedding fallback):

1. Run every row of eval/danger_sign_eval_100.csv (all should escalate)
   through the embedder and record the best cosine-similarity score against
   the reference phrase list, keyed by whether the KEYWORD path alone would
   already have caught it (in which case the embedding score doesn't matter
   for that row -- the keyword path fires first) vs rows that need the
   embedding path to fire.
2. Run every row of eval/negative_set_100.csv (none should escalate) the
   same way -- these are the negative set.
3. Pick the lowest threshold such that:
      - recall on the danger rows that DEPEND on the embedding path stays
        as high as possible, and
      - the false-positive rate on the negative set stays at or below
        eval/run_negative_set_eval.py's MAX_ACCEPTABLE_FALSE_POSITIVE_RATE.
   Report the full precision/coverage curve so the choice is visible, not
   just the final number -- this becomes a report figure, same as Lever 5.

Requires sentence-transformers and network access to Hugging Face Hub to
download paraphrase-multilingual-MiniLM-L12-v2 the first time. Run this
locally / in Colab, not in the CI sandbox -- CI does not have Hub access
and the danger-gate eval scripts are written to fall back to keyword-only
gracefully when the model can't load.

Usage:
    python eval/tune_embedding_threshold.py
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DANGER_CSV = Path(__file__).resolve().parent / "danger_sign_eval_100.csv"
NEGATIVE_CSV = Path(__file__).resolve().parent / "negative_set_100.csv"


def _load_questions(path: str, column: str = "question") -> list[str]:
    with open(path, encoding="utf-8-sig") as f:
        return [row[column] for row in csv.DictReader(f)]


def main():
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print(
            "sentence-transformers is not installed / the model could not "
            "be downloaded in this environment. This script must be run "
            "somewhere with Hugging Face Hub access (e.g. locally, or "
            "Colab) -- see the module docstring.",
            file=sys.stderr,
        )
        sys.exit(1)

    from api.safety.danger_gate import (
        DANGER_CATEGORIES,
        _build_embedding_reference,
        run_danger_gate,
    )

    print("Loading embedder...")
    embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    reference_phrases = _build_embedding_reference()
    reference_embeddings = embedder.encode(reference_phrases, normalize_embeddings=True)

    danger_questions = _load_questions(DANGER_CSV)
    negative_questions = _load_questions(NEGATIVE_CSV)

    # Only score danger rows the keyword path does NOT already catch --
    # those are the ones whose fate actually depends on the threshold.
    embedding_dependent_danger_rows = [
        q for q in danger_questions
        if not run_danger_gate(q, use_embedding=False).escalate
    ]
    print(
        f"{len(embedding_dependent_danger_rows)} / {len(danger_questions)} "
        f"danger rows depend on the embedding path (keyword path misses them)."
    )

    def best_scores(questions):
        if not questions:
            return np.array([])
        embs = embedder.encode(questions, normalize_embeddings=True)
        sims = embs @ reference_embeddings.T
        return sims.max(axis=1)

    danger_scores = best_scores(embedding_dependent_danger_rows)
    negative_scores = best_scores(negative_questions)

    print("\nthreshold | danger recall (embedding-dependent rows) | negative false-positive rate")
    candidates = [round(0.5 + 0.02 * i, 2) for i in range(26)]  # 0.50 .. 1.00
    best = None
    for t in candidates:
        recall = float((danger_scores >= t).mean()) if len(danger_scores) else 1.0
        fp_rate = float((negative_scores >= t).mean()) if len(negative_scores) else 0.0
        print(f"  {t:.2f}    |  {recall:.3f}                                    |  {fp_rate:.3f}")
        if fp_rate <= 0.05:
            if best is None or recall > best[1]:
                best = (t, recall, fp_rate)

    print()
    if best is None:
        print(
            "No threshold in the scanned range keeps the negative-set false "
            "positive rate <= 0.05. The reference phrase list is probably "
            "too close to ordinary health-question vocabulary -- consider "
            "trimming overly generic reference phrases rather than lowering "
            "the threshold further."
        )
        sys.exit(1)

    t, recall, fp_rate = best
    print(
        f"Recommended EMBEDDING_THRESHOLD = {t:.2f} "
        f"(embedding-dependent recall {recall:.3f}, negative-set FP rate {fp_rate:.3f})."
    )
    print(
        "Update the constant in api/safety/danger_gate.py to this value, "
        "with this printout pasted into the commit message or an ADR entry "
        "so the number has a recorded justification."
    )


if __name__ == "__main__":
    main()
