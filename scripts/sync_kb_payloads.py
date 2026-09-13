"""Push edited KB answer text into the live Qdrant payloads.

Only the *questions* are embedded (see retrieval/scripts/embed_and_index.ipynb,
which encodes `normalised_questions`); the answer is carried in the point
payload. So an answer-only edit -- like the rural-availability substitutions in
scripts/localise_nutrition_answers.py -- needs a payload update, not a re-embed.
No GPU, no model load, one network round-trip per batch.

Editing a *question* is a different matter and this script will refuse: that
changes what the point means and requires re-running the embedding notebook.

    python scripts/sync_kb_payloads.py --dry-run
    python scripts/sync_kb_payloads.py --apply
"""

import argparse
import os
import sys

import pandas as pd
from dotenv import load_dotenv

SD_KB = os.path.join("knowledge_base", "Womens_Health_KB - 2000_final.csv")
LANG = "sd"
BATCH = 128


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--allow-question-drift", action="store_true",
                    help="also update rows whose QUESTION changed. The stored "
                         "vector still encodes the old wording, so retrieval is "
                         "unchanged -- only the displayed text is corrected. "
                         "Use when the edit is a spelling or terminology fix "
                         "that must not wait for a re-embed.")
    args = ap.parse_args()

    load_dotenv()
    from qdrant_client import QdrantClient, models

    from retrieval.search import COLLECTION

    kb = pd.read_csv(SD_KB)
    client = QdrantClient(url=os.environ["QDRANT_URL"], api_key=os.environ["QDRANT_API_KEY"])

    # Pull the live payloads for this language so we only touch what differs.
    live, offset = {}, None
    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION,
            scroll_filter=models.Filter(must=[
                models.FieldCondition(key="lang", match=models.MatchValue(value=LANG))]),
            limit=512, offset=offset, with_payload=["answer_id", "question", "answer"],
            with_vectors=False)
        for p in points:
            live[p.payload["answer_id"]] = p
        if offset is None:
            break
    print(f"live points with lang={LANG}: {len(live)}")

    changed, question_drift, missing = [], [], []
    for _, row in kb.iterrows():
        aid = int(row["id"])
        p = live.get(aid)
        if p is None:
            missing.append(aid)
            continue
        q_drift = str(p.payload.get("question", "")).strip() != str(row["question"]).strip()
        a_drift = str(p.payload.get("answer", "")).strip() != str(row["answer"]).strip()
        if q_drift and not args.allow_question_drift:
            question_drift.append(aid)
            continue
        payload = {}
        if a_drift:
            payload["answer"] = str(row["answer"])
        if q_drift:
            # Displayed text only. The embedding is not touched, so retrieval
            # behaves exactly as before until the notebook is re-run.
            payload["question"] = str(row["question"])
            question_drift.append(aid)
        if payload:
            changed.append((p.id, payload))

    label = "updated too" if args.allow_question_drift else "skipped"
    print(f"points to update               : {len(changed)}")
    print(f"questions differing ({label:12}): {len(question_drift)}")
    print(f"ids absent from the collection : {len(missing)}")
    if question_drift:
        if args.allow_question_drift:
            print("  -- their payload text is corrected, but the stored VECTOR still")
            print("     encodes the old wording. Re-run the embedding notebook to")
            print(f"     finish the job for: {question_drift[:10]}")
        else:
            print("  -- a changed question needs a re-embed, not a payload update;")
            print(f"     re-run the embedding notebook for: {question_drift[:10]}")
    for pid, payload in changed[:5]:
        print(f"  point {pid}: {list(payload)} {str(list(payload.values())[0])[:52]}")

    if not args.apply:
        print("\ndry run -- nothing written. Re-run with --apply.")
        return 0

    for i in range(0, len(changed), BATCH):
        for pid, payload in changed[i:i + BATCH]:
            client.set_payload(collection_name=COLLECTION,
                               payload=payload, points=[pid], wait=False)
        print(f"  updated {min(i + BATCH, len(changed))}/{len(changed)}")
    print(f"done -- {len(changed)} payloads updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
