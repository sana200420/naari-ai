"""
Tests for Phase 3 tier enforcement.
Tier A: serve normally
Tier B: serve with disclaimer flag = True
Tier C: block, return refusal
"""
import pytest
from api.phase3_tier import enforce_tier, TIER_A, TIER_B, TIER_C, TIER_B_DISCLAIMER, TIER_C_REFUSAL


def test_tier_a_serves_normally():
    answer, disclaimer, blocked = enforce_tier(TIER_A, "test answer", False)
    assert answer == "test answer"
    assert disclaimer is False
    assert blocked is False


def test_tier_b_sets_disclaimer():
    answer, disclaimer, blocked = enforce_tier(TIER_B, "test answer", False)
    assert answer == "test answer"
    assert disclaimer is True
    assert blocked is False


def test_tier_c_blocks():
    answer, disclaimer, blocked = enforce_tier(TIER_C, "test answer", False)
    assert blocked is True
    assert answer == TIER_C_REFUSAL


def test_tier_c_never_serves_original():
    answer, _, blocked = enforce_tier(TIER_C, "sensitive content", False)
    assert blocked is True
    assert answer != "sensitive content"


def test_missing_tier_serves_normally():
    answer, disclaimer, blocked = enforce_tier(None, "test answer", False)
    assert blocked is False
