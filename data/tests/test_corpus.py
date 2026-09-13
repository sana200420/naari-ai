import pandas as pd
import os

def test_corpus_exists():
    assert os.path.exists("data/processed/final_corpus.csv")

def test_corpus_schema():
    df = pd.read_csv("data/processed/final_corpus.csv")
    required = ["answer_id", "category", "subcategory", "question", "answer", "sources"]
    for c in required:
        assert c in df.columns, f"Missing column: {c}"

def test_no_duplicate_answer_ids():
    df = pd.read_csv("data/processed/final_corpus.csv")
    assert df["answer_id"].is_unique

def test_no_null_questions_or_answers():
    df = pd.read_csv("data/processed/final_corpus.csv")
    assert df["question"].notna().all()
    assert df["answer"].notna().all()
