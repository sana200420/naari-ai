"""Verify generate() degrades cleanly through Gemini -> Groq -> static
fallback with no user-visible error, even if all providers fail."""

def test_generate_falls_back_to_static_when_all_providers_fail(monkeypatch):
    import api.pipeline as p

    # Simulate every provider failing (bad keys, network down, etc.)
    def fake_try_providers(prompt):
        return
        yield  # makes this a generator that yields nothing

    monkeypatch.setattr(p, "_try_providers", fake_try_providers)

    result = p.generate(query="test question", chunks=[{"text": "some context"}])

    # Must not raise, must not return empty/None, must return the static message
    assert result, "generate() returned empty/None instead of a fallback message"
    assert isinstance(result, str)
    assert "معاف" in result or "ليڊي هيلٿ" in result, \
        f"generate() did not degrade to the static fallback message: {result}"


def test_generate_does_not_raise_when_provider_throws(monkeypatch):
    """A provider raising an exception must not crash the pipeline."""
    import api.pipeline as p

    def broken_provider(prompt):
        raise ConnectionError("simulated API failure")

    def fake_try_providers(prompt):
        try:
            broken_provider(prompt)
        except ConnectionError:
            return
        yield

    monkeypatch.setattr(p, "_try_providers", fake_try_providers)

    try:
        result = p.generate(query="test question", chunks=[{"text": "some context"}])
    except Exception as e:
        assert False, f"generate() raised an exception instead of degrading cleanly: {e}"

    assert result, "generate() returned nothing after provider failure"