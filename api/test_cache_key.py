"""The response cache must key on the same normaliser retrieval embeds through.

This module imported `normalise` from api.safety.danger_gate, a function that
has never existed in any version of that file. Nothing caught it because
nothing called cache_get: the Space serves Gradio, which bypassed
routers/ask.py. Wiring the cache into the Gradio path turned a dormant
ImportError into a total /ask outage, with the only trace in the Space logs.
"""
from api.phase3_cache import _cache_key, cache_get, cache_set


def test_cache_key_does_not_raise():
    assert len(_cache_key("حيض جي چڪر ڇا آهي؟")) == 64


def test_key_matches_the_retrieval_normaliser():
    # If these ever diverge, the cache can return another question's answer.
    import hashlib

    from retrieval.normalize import normalize_sd

    q = "ماهواري دوران پيڊ ڪيتري دير بعد تبديل ڪرڻ گهرجي؟"
    assert _cache_key(q) == hashlib.sha256(normalize_sd(q).encode()).hexdigest()


def test_round_trip():
    cache_set("سوال", {"answer": "جواب", "path": "verbatim"})
    assert cache_get("سوال")["answer"] == "جواب"
