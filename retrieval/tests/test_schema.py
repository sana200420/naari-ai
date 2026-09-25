"""Proves the Phase 0 'done when': every KB row carries a review_tier value
(defaulting to B), and the schema validator enforces it."""

import csv

from retrieval.schema import DEFAULT_KB_PATH, VALID_TIERS, validate_kb_schema


def test_real_kb_file_passes_validation():
    assert validate_kb_schema() == []


def test_every_row_has_a_review_tier():
    with open(DEFAULT_KB_PATH, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2021   # 2000 + 9 fever rows + 12 PCOS rows, ids 2001-2021
    for row in rows:
        assert row["review_tier"] in VALID_TIERS


def test_tier_a_matches_the_clinical_review_sign_off():
    # Was test_all_rows_currently_default_to_b, asserting every row was B --
    # that stopped being true 2026-09-25 when Dr Arshia's (FCPS) review of
    # docs/clinical_review/ promoted 36 rows to A. This is the update that
    # test's own comment asked for, not a workaround: A-tier ids must be
    # exactly the ones with decision=="Approve" in the tracking CSV (minus
    # R023, reviewed against a stale packet copy -- see docs/status.md),
    # and every review_tier value must still be a valid tier. No row should
    # ever become C by silent default.
    import csv as csv_mod
    from pathlib import Path

    with open(DEFAULT_KB_PATH, encoding="utf-8", newline="") as f:
        rows = list(csv_mod.DictReader(f))
    assert all(row["review_tier"] in VALID_TIERS for row in rows)
    assert not any(row["review_tier"] == "C" for row in rows), (
        "a row became Tier C -- that blocks serving entirely and must be "
        "a deliberate clinical decision, never a silent default"
    )

    tracking = Path(__file__).resolve().parents[2] / "docs/clinical_review/clinical_review_tracking.csv"
    with open(tracking, encoding="utf-8-sig", newline="") as f:  # the CSV has a BOM
        tracking_rows = list(csv_mod.DictReader(f))
    expected_a = {r["source_id"] for r in tracking_rows
                 if r["decision"] == "Approve" and r["review_id"] != "R023"}

    actual_a = {row["id"] for row in rows if row["review_tier"] == "A"}
    assert actual_a == expected_a, (
        f"Tier A in the KB doesn't match the clinical review sign-off. "
        f"In KB but not approved: {actual_a - expected_a}. "
        f"Approved but not promoted: {expected_a - actual_a}."
    )


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
