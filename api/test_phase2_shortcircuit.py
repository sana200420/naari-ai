"""Verify danger-sign query never reaches retrieval or LLM."""
import sys, types
from unittest.mock import MagicMock

def test_danger_query_never_calls_retrieval_or_llm(monkeypatch):
    retrieval_mock = MagicMock(side_effect=AssertionError("retrieval was called!"))
    llm_mock = MagicMock(side_effect=AssertionError("LLM was called!"))

    mod = types.ModuleType("retrieval.pipeline")
    mod.search = retrieval_mock
    monkeypatch.setitem(sys.modules, "retrieval.pipeline", mod)

    import api.pipeline as p
    monkeypatch.setattr(p, "generate", llm_mock)

    from api.routers.ask import AskRequest
    r = p.run_pipeline(AskRequest(query="I want to kill myself", language="sindhi"))

    assert r.path == "danger"
    retrieval_mock.assert_not_called()
    llm_mock.assert_not_called()