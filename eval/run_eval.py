"""Evaluation harness for the Sindhi Health RAG system.
Runnable from Colab or GitHub Actions.

Expected retrieval predictions input format (CSV):
    query_id, retrieved_answer_ids   (retrieved_answer_ids = ';'-separated, ranked)

If predictions are not supplied, metrics that need them are reported as
"not available" rather than fabricated.
"""
import argparse
import os
import pandas as pd


def recall_at_k(gold_df, preds_df, k):
    merged = gold_df.merge(preds_df, on="query_id", how="left")
    hits = 0
    for row in merged.itertuples():
        if pd.isna(getattr(row, "retrieved_answer_ids", None)):
            continue
        retrieved = [int(x) for x in str(row.retrieved_answer_ids).split(";") if x][:k]
        if row.correct_answer_id in retrieved:
            hits += 1
    return hits / len(merged) if len(merged) else None


def mrr(gold_df, preds_df):
    merged = gold_df.merge(preds_df, on="query_id", how="left")
    total = 0.0
    for row in merged.itertuples():
        if pd.isna(getattr(row, "retrieved_answer_ids", None)):
            continue
        retrieved = [int(x) for x in str(row.retrieved_answer_ids).split(";") if x]
        if row.correct_answer_id in retrieved:
            rank = retrieved.index(row.correct_answer_id) + 1
            total += 1.0 / rank
    return total / len(merged) if len(merged) else None


def run(gold_path, preds_path=None, danger_path=None, danger_preds_path=None,
        oos_path=None, oos_preds_path=None):
    results = {}
    gold_df = pd.read_csv(gold_path)
    results["gold_eval_size"] = len(gold_df)

    if preds_path:
        preds_df = pd.read_csv(preds_path)
        results["recall@1"] = recall_at_k(gold_df, preds_df, 1)
        results["recall@5"] = recall_at_k(gold_df, preds_df, 5)
        results["recall@10"] = recall_at_k(gold_df, preds_df, 10)
        results["mrr"] = mrr(gold_df, preds_df)
        results["hit_rate"] = recall_at_k(gold_df, preds_df, 10**9)
    else:
        for m in ["recall@1", "recall@5", "recall@10", "mrr", "hit_rate"]:
            results[m] = "NOT AVAILABLE (no retrieval predictions supplied)"

    if danger_path:
        danger_df = pd.read_csv(danger_path)
        results["danger_eval_size"] = len(danger_df)
        if danger_preds_path:
            dpreds = pd.read_csv(danger_preds_path)
            merged = danger_df.merge(dpreds, on="query_id", how="left")
            detected = (merged["predicted_action"] == "danger_sign_escalation").sum()
            results["danger_detection_rate"] = detected / len(merged) if len(merged) else None
            results["danger_false_negatives"] = len(merged) - detected
        else:
            results["danger_detection_rate"] = "NOT AVAILABLE (no safety predictions supplied)"

    if oos_path:
        oos_df = pd.read_csv(oos_path)
        results["oos_eval_size"] = len(oos_df)
        if oos_preds_path:
            opreds = pd.read_csv(oos_preds_path)
            merged = oos_df.merge(opreds, on="query_id", how="left")
            detected = (merged["predicted_action"] == "out_of_scope_referral").sum()
            results["oos_detection_rate"] = detected / len(merged) if len(merged) else None
        else:
            results["oos_detection_rate"] = "NOT AVAILABLE (no scope predictions supplied)"

    return results


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--gold", default="eval/gold_eval.csv")
    p.add_argument("--preds", default=None)
    p.add_argument("--danger", default="eval/danger_sign_eval.csv")
    p.add_argument("--danger_preds", default=None)
    p.add_argument("--oos", default="eval/out_of_scope_eval.csv")
    p.add_argument("--oos_preds", default=None)
    args = p.parse_args()
    danger_path = args.danger if args.danger and os.path.exists(args.danger) else None
    oos_path = args.oos if args.oos and os.path.exists(args.oos) else None
    r = run(args.gold, args.preds, danger_path, args.danger_preds, oos_path, args.oos_preds)
    for k, v in r.items():
        print(f"{k}: {v}")
