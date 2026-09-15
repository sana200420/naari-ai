"""
Tests for rate limiting behavior.
"""
from api.phase3_cache import cache_get, cache_set, _cache_key


def test_cache_key_is_consistent():
    key1 = _cache_key("same question")
    key2 = _cache_key("same question")
    assert key1 == key2


def test_different_questions_have_different_keys():
    key1 = _cache_key("question one")
    key2 = _cache_key("question two")
    assert key1 != key2


def test_cache_stores_and_retrieves():
    cache_set("rate test question", {"answer": "test", "path": "verbatim"})
    result = cache_get("rate test question")
    assert result is not None
    assert result["answer"] == "test"


def test_cache_miss_returns_none():
    result = cache_get("question that was never asked xyz123")
    assert result is None
