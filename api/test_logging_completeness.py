import inspect

def test_log_query_signature_has_all_required_fields():
    from api.logging.logger import log_query

    sig = inspect.signature(log_query)
    required = {"query", "retrieved_ids", "scores", "band", "path", "latency_ms", "provider"}
    actual = set(sig.parameters.keys())
    missing = required - actual
    assert not missing, f"log_query is missing parameters: {missing}"


def test_scores_actually_gets_logged(monkeypatch):
    """scores is accepted as a parameter but must also end up in the row
    that gets sent to Supabase -- accepting it and silently dropping it
    is worse than not accepting it at all."""
    import api.logging.logger as logger_mod

    captured = {}

    class FakeTable:
        def insert(self, row):
            captured.update(row)
            return self
        def execute(self):
            return None

    class FakeClient:
        def table(self, name):
            return FakeTable()

    monkeypatch.setattr(logger_mod, "_get_client", lambda: FakeClient())

    logger_mod.log_query(
        query="test query",
        retrieved_ids=[1, 2, 3],
        scores=[0.9, 0.8, 0.7],
        band="confirm",
        path="verbatim",
        latency_ms=123.4,
        provider="gemini",
    )

    assert "scores" in captured, "scores was accepted but never logged to Supabase"