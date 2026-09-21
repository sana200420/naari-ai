import pandas as pd


def test_out_of_scope_queries_are_distinct():
    df = pd.read_csv("eval/out_of_scope_eval.csv")
    assert df["query"].is_unique, "out_of_scope_eval.csv has duplicate query text"


def test_out_of_scope_scope_types_balanced():
    df = pd.read_csv("eval/out_of_scope_eval.csv")
    counts = df["scope_type"].value_counts()
    assert len(counts) == 5
    assert (counts == 20).all(), f"scope_type counts not balanced: {counts.to_dict()}"


def test_gold_eval_answer_ids_exist_in_corpus():
    gold = pd.read_csv("eval/gold_eval.csv")
    corpus = pd.read_csv("data/processed/final_corpus.csv")
    valid_ids = set(corpus["answer_id"])
    bad = set(gold["correct_answer_id"]) - valid_ids
    assert not bad, f"gold_eval.csv references answer_ids not in the corpus: {bad}"
