"""log_feedback must never raise, and must reject bad votes before it
ever tries to reach Supabase."""
from unittest.mock import MagicMock

from api.logging import logger as logger_module
from api.logging.logger import log_feedback


def test_rejects_invalid_vote():
    assert log_feedback("سوال", "جواب", "maybe") is False


def test_rejects_empty_vote():
    assert log_feedback("سوال", "جواب", "") is False


def test_accepts_up_and_down(monkeypatch):
    fake_client = MagicMock()
    monkeypatch.setattr(logger_module, "_get_client", lambda: fake_client)

    assert log_feedback("سوال", "جواب", "up") is True
    assert log_feedback("سوال", "جواب", "DOWN") is True  # case-insensitive
    assert fake_client.table.call_count == 2
    fake_client.table.assert_called_with("feedback_logs")


def test_returns_false_when_no_client():
    # _get_client() returns None when SUPABASE_URL/KEY aren't set --
    # this must fall back quietly, never raise.
    result = log_feedback("سوال", "جواب", "up")
    assert result is False


def test_never_raises_on_insert_failure(monkeypatch):
    fake_client = MagicMock()
    fake_client.table.side_effect = Exception("network down")
    monkeypatch.setattr(logger_module, "_get_client", lambda: fake_client)

    assert log_feedback("سوال", "جواب", "up") is False


    