"""Tests for demo_rehearsal.py's _ask_once/run_once -- the checks that
decide whether a run counts as "clean."

No live network calls, same reasoning as test_keep_warm.py: everything
here mocks the gradio Client.
"""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scripts.demo_rehearsal as demo_rehearsal  # noqa: E402


def _fake_client(predict_return=None, predict_side_effect=None):
    client = MagicMock()
    if predict_side_effect is not None:
        client.predict.side_effect = predict_side_effect
    else:
        client.predict.return_value = predict_return
    return client


def test_ask_once_ok_when_answer_present():
    payload = json.dumps({"answer": "some real answer", "path": "verbatim"})
    with patch.object(demo_rehearsal, "_get_client",
                      return_value=_fake_client(predict_return=payload)):
        r = demo_rehearsal._ask_once("space/id", "query")
    assert r["ok"] is True
    assert r["path"] == "verbatim"
    assert r["error"] is None


def test_ask_once_not_ok_when_answer_empty():
    """The exact bug this rewrite fixes: a call that "succeeds" (no
    exception, valid JSON) but carries no real answer must not count as
    clean -- this is what a 404 response being silently accepted looked
    like from the caller's side before this rewrite."""
    payload = json.dumps({"answer": "", "path": None})
    with patch.object(demo_rehearsal, "_get_client",
                      return_value=_fake_client(predict_return=payload)):
        r = demo_rehearsal._ask_once("space/id", "query")
    assert r["ok"] is False


def test_ask_once_not_ok_when_client_raises():
    with patch.object(demo_rehearsal, "_get_client",
                      return_value=_fake_client(predict_side_effect=Exception("boom"))):
        r = demo_rehearsal._ask_once("space/id", "query")
    assert r["ok"] is False
    assert "boom" in r["error"]


def test_ask_once_flags_cold_start_by_latency(monkeypatch):
    payload = json.dumps({"answer": "answer", "path": "verbatim"})
    client = _fake_client(predict_return=payload)

    times = iter([0.0, 6.0])  # 6000ms > COLD_START_THRESHOLD_MS
    monkeypatch.setattr(demo_rehearsal.time, "time", lambda: next(times))

    with patch.object(demo_rehearsal, "_get_client", return_value=client):
        r = demo_rehearsal._ask_once("space/id", "query")
    assert r["is_cold_start"] is True
    assert r["ok"] is True  # slow but real -- these are independent signals


def test_run_once_not_clean_if_any_question_fails(monkeypatch):
    """One bad question in the demo script must mark the whole run
    not-clean, even if every other question is fine."""
    monkeypatch.setattr(demo_rehearsal, "DEMO_QUESTIONS", ["q1", "q2"])
    monkeypatch.setattr(demo_rehearsal, "time",
                        MagicMock(time=lambda: 0.0, sleep=lambda s: None))

    responses = iter([
        {"query": "q1", "ok": True, "path": "verbatim", "latency_ms": 10,
         "is_429": False, "is_cold_start": False, "error": None},
        {"query": "q2", "ok": False, "path": None, "latency_ms": 10,
         "is_429": False, "is_cold_start": False, "error": "some failure"},
    ])
    with patch.object(demo_rehearsal, "_ask_once", lambda space, q: next(responses)):
        run = demo_rehearsal.run_once("space/id", run_number=1)

    assert run["clean"] is False
    assert run["count_error"] == 1
