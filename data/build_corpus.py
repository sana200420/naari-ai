"""Reproducible corpus build.
Usage: python data/build_corpus.py <input_csv> <output_csv> <report_md>
Never edits the input file. Never invents or alters answer text.
"""
import sys
import pandas as pd

REQUIRED = ["answer_id", "category", "subcategory", "question", "answer", "sources"]

def build(input_csv, output_csv, report_md):
    df = pd.read_csv(input_csv)
    rename_map = {}
    aliases = {"id": "answer_id", "sub_category": "subcategory", "source": "sources"}
    for old, new in aliases.items():
        if old in df.columns and new not in df.columns:
            rename_map[old] = new
    df = df.rename(columns=rename_map)

    missing_cols = [c for c in REQUIRED if c not in df.columns]
    if missing_cols:
        raise RuntimeError(f"Missing required columns, cannot build corpus: {missing_cols}")

    original_count = len(df)

    invalid_mask = df["question"].isna() | (df["question"].astype(str).str.strip() == "") \
                 | df["answer"].isna()   | (df["answer"].astype(str).str.strip() == "")
    invalid_rows = df[invalid_mask]
    df_valid = df[~invalid_mask].copy()

    exact_dupes = df_valid.duplicated().sum()
    df_valid = df_valid.drop_duplicates()

    dup_ids = df_valid["answer_id"].duplicated().sum()
    dup_questions_mask = df_valid["question"].duplicated(keep=False)
    dup_question_count = df_valid["question"].duplicated().sum()

    df_valid.to_csv(output_csv, index=False)

    final_count = len(df_valid)
    with open(report_md, "w", encoding="utf-8") as f:
        f.write("# Corpus Validation Report\n\n")
        f.write(f"- Original row count: {original_count}\n")
        f.write(f"- Invalid rows (null/empty question or answer, excluded): {len(invalid_rows)}\n")
        f.write(f"- Exact duplicate rows (removed): {exact_dupes}\n")
        f.write(f"- Duplicate answer_id (NOT removed, needs manual review): {dup_ids}\n")
        f.write(f"- Duplicate questions (NOT removed, flagged for review): {dup_question_count}\n")
        f.write(f"- Final row count: {final_count}\n")
        f.write(f"- Schema validation: PASSED ({REQUIRED})\n\n")
        if len(invalid_rows):
            f.write("## Invalid rows excluded (answer_id list)\n")
            f.write(str(invalid_rows["answer_id"].tolist()) + "\n\n")
        if dup_question_count:
            f.write("## Duplicate question rows flagged (answer_id list)\n")
            f.write(str(df_valid[dup_questions_mask]["answer_id"].tolist()) + "\n")

    print(f"Corpus built: {final_count} rows -> {output_csv}")
    print(f"Report written to {report_md}")

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], sys.argv[3])
