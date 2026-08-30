"""Proves the Phase 0 'done when': every KB row carries a review_tier value
(defaulting to B), and the schema validator enforces it."""

import csv

from retrieval.schema import DEFAULT_KB_PATH, VALID_TIERS, validate_kb_schema


def test_real_kb_file_passes_validation():
    assert validate_kb_schema() == []


def test_every_row_has_a_review_tier():
    with open(DEFAULT_KB_PATH, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2000
    for row in rows:
        assert row["review_tier"] in VALID_TIERS


def test_all_rows_currently_default_to_b():
    # true today: nothing has been clinically reviewed yet. This test is
    # expected to start failing once a reviewer promotes real rows to A —
    # that's the point; update it then, don't just delete it.
    with open(DEFAULT_KB_PATH, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert all(row["review_tier"] == "B" for row in rows)


def test_validator_catches_a_bad_tier(tmp_path):
    bad_file = tmp_path / "bad.csv"
    bad_file.write_text(
        "id,category,sub_category,question,answer,source,review_tier\n"
        "1,cat,sub,q,a,src,Z\n",
        encoding="utf-8",
    )
    violations = validate_kb_schema(bad_file)
    assert any("review_tier" in v for v in violations)


def test_validator_catches_a_blank_field(tmp_path):
    bad_file = tmp_path / "bad.csv"
    bad_file.write_text(
        "id,category,sub_category,question,answer,source,review_tier\n"
        "1,cat,sub,,a,src,B\n",
        encoding="utf-8",
    )
    violations = validate_kb_schema(bad_file)
    assert any("blank 'question'" in v for v in violations)
