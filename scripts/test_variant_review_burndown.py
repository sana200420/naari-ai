"""Tests for variant_review_burndown.py's build() -- the per-category
counting logic, against synthetic data rather than the real 4,000-row file
so this doesn't depend on it being in any particular state.
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import variant_review_burndown as burndown  # noqa: E402


def _fake_df(rows):
    return pd.DataFrame(rows)


def test_build_counts_each_status_correctly():
    df = _fake_df([
        {"category": "حيض جي صحت ۽ مدت", "human_review_status": "approved"},
        {"category": "حيض جي صحت ۽ مدت", "human_review_status": "not_reviewed"},
        {"category": "حيض جي صحت ۽ مدت", "human_review_status": "fix"},
        {"category": "حيض جي صحت ۽ مدت", "human_review_status": "drop"},
    ])
    with patch.object(burndown.pd, "read_csv", return_value=df):
        out = burndown.build()

    row = out.iloc[0]
    assert row.total_variants == 4
    assert row.approved == 1
    assert row.fix == 1
    assert row["drop"] == 1
    assert row.not_reviewed == 1
    assert row.reviewed == 3          # everything except not_reviewed
    assert row.percent_complete == 75.0


def test_build_assigns_the_right_owner_per_category():
    df = _fake_df([
        {"category": cat, "human_review_status": "not_reviewed"}
        for cat in burndown.OWNER_OF_CATEGORY
    ])
    with patch.object(burndown.pd, "read_csv", return_value=df):
        out = burndown.build()

    got = dict(zip(out.category, out.owner))
    assert got == burndown.OWNER_OF_CATEGORY


def test_build_zero_percent_when_nothing_reviewed():
    """The real starting state as of 2026-09-25 -- nobody has reviewed
    anything yet, including the category whose smoke-test-batch approval
    (PR #32, a different file) does not count here."""
    df = _fake_df([
        {"category": "حيض جي صحت ۽ مدت", "human_review_status": "not_reviewed"},
        {"category": "حيض جي صحت ۽ مدت", "human_review_status": "not_reviewed"},
    ])
    with patch.object(burndown.pd, "read_csv", return_value=df):
        out = burndown.build()
    assert out.iloc[0].percent_complete == 0.0


def test_build_raises_on_unmapped_category():
    df = _fake_df([{"category": "some new category nobody mapped",
                    "human_review_status": "not_reviewed"}])
    with patch.object(burndown.pd, "read_csv", return_value=df):
        with pytest.raises(SystemExit):
            burndown.build()


def test_build_warns_but_does_not_crash_on_unknown_status(capsys):
    df = _fake_df([{"category": "حيض جي صحت ۽ مدت",
                    "human_review_status": "typo_status"}])
    with patch.object(burndown.pd, "read_csv", return_value=df):
        out = burndown.build()
    assert "unrecognised" in capsys.readouterr().err
    # an unrecognised status counts toward total but not toward "reviewed"
    # (only not_reviewed is subtracted) -- surfaced via the warning above,
    # not silently absorbed into either bucket.
    assert out.iloc[0].total_variants == 1
