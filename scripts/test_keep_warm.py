"""Tests for keep_warm.ping() -- the check .github/workflows/keep_warm.yml
runs on a schedule and keep_warm_once.py turns into a CI exit code.

No live network calls: everything here mocks requests.get and the gradio
Client, both to keep the suite fast/offline and because a real ping
against the live Space belongs in an uptime check, not a unit test.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import keep_warm  # noqa: E402


def _fake_response(status_code=200):
    r = MagicMock()
    r.status_code = status_code
    return r


def test_ping_true_when_container_up_and_ask_succeeds():
    with patch.object(keep_warm, "requests") as mock_requests, \
         patch.object(keep_warm, "_get_client") as mock_get_client:
        mock_requests.get.return_value = _fake_response(200)
        mock_get_client.return_value.predict.return_value = '{"answer": "..."}'

        assert keep_warm.ping() is True


def test_ping_false_when_container_unreachable():
    with patch.object(keep_warm, "requests") as mock_requests:
        mock_requests.get.side_effect = Exception("connection refused")

        assert keep_warm.ping() is False


def test_ping_false_on_non_200_root_page():
    """A non-200 must not be treated as "up" -- this is the check that
    exists specifically to catch that case rather than assume success."""
    with patch.object(keep_warm, "requests") as mock_requests:
        mock_requests.get.return_value = _fake_response(503)

        assert keep_warm.ping() is False


def test_ping_false_when_container_up_but_ask_broken():
    """The scenario keep_warm.py's docstring calls out by name: the
    container can be up (root page 200) while /ask itself is broken --
    checking only the root page would report a false "OK"."""
    with patch.object(keep_warm, "requests") as mock_requests, \
         patch.object(keep_warm, "_get_client") as mock_get_client:
        mock_requests.get.return_value = _fake_response(200)
        mock_get_client.return_value.predict.side_effect = Exception("pipeline error")

        assert keep_warm.ping() is False


# keep_warm_once.py itself is two lines -- `sys.exit(0 if ping() else 1)`
# under an `if __name__ == "__main__"` guard -- and not separately unit
# tested here. Exercising a __main__ guard needs either a subprocess or a
# runpy trick disproportionate to two lines whose only real logic (ping())
# is already covered above; reviewable by reading it.
