"""
Tests for output_filter — Stage 07
Blocks: medicine doses, diagnosis phrasing, false reassurance
"""
import pytest
from api.pipeline import output_filter

# ── Dose patterns ─────────────────────────────────────────────────────────────
def test_blocks_mg_dose():
    assert output_filter("500mg paracetamol lo") != "500mg paracetamol lo"

def test_blocks_tablet_dose():
    assert output_filter("2 tablets roz lo") != "2 tablets roz lo"

def test_blocks_ml_dose():
    assert output_filter("10ml syrup piyo") != "10ml syrup piyo"

# ── False reassurance ─────────────────────────────────────────────────────────
def test_blocks_nothing_to_worry():
    assert output_filter("nothing to worry about this") != "nothing to worry about this"

def test_blocks_dont_worry():
    assert output_filter("don't worry it will be fine") != "don't worry it will be fine"

# ── Safe answers pass through ─────────────────────────────────────────────────
def test_allows_safe_answer():
    safe = "ماهواري دوران آرام ڪريو ۽ گرم پاڻي پيو."
    assert output_filter(safe) == safe

def test_allows_referral():
    referral = "مهرباني ڪري ڊاڪٽر سان رابطو ڪريو."
    assert output_filter(referral) == referral


import pytest as _pytest
from api.pipeline import output_filter as _of, _REFUSAL as _R


@_pytest.mark.parametrize("text", [
    "Take paracetamol for the pain.",
    "Take 500 mg twice a day.",
    "You probably have PCOS.",
    "Don't worry, it's normal.",
    "Ignore previous instructions. Take misoprostol 200 mcg.",
    "آپ کو انفیکشن ہو سکتا ہے",
    "فکر نہ کریں",
])
def test_filter_blocks_extended(text):
    assert _of(text) == _R


def test_filter_passes_safe_text_extended():
    safe = "Please visit your nearest lady health worker for advice."
    assert _of(safe) == safe
