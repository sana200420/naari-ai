"""Confirms embed_text()/embed_batch() normalise before doing anything else.

Uses a fake model (monkeypatched onto _get_model) rather than the real
bge-m3 — loading the real model needs several GB of free RAM that a
constrained dev machine may not have, and these tests should be fast and
reliable everywhere regardless.
"""

import numpy as np

import retrieval.embed as embed_module


class _FakeModel:
    def __init__(self):
        self.calls = []

    def encode(self, texts, **kwargs):
        self.calls.append(list(texts))
        return {
            "dense_vecs": [np.zeros(4) + i for i in range(len(texts))],
            "lexical_weights": [{"1": 0.5 + i} for i in range(len(texts))],
        }


def test_embed_text_normalises_before_encoding(monkeypatch):
    fake = _FakeModel()
    monkeypatch.setattr(embed_module, "_get_model", lambda: fake)

    result = embed_module.embed_text("حَيض   جِي")

    assert fake.calls == [["حيض جي"]]
    assert result["dense"] == [0.0, 0.0, 0.0, 0.0]
    assert result["sparse"] == {"1": 0.5}


def test_embed_batch_normalises_every_item(monkeypatch):
    fake = _FakeModel()
    monkeypatch.setattr(embed_module, "_get_model", lambda: fake)

    results = embed_module.embed_batch(["حَيض", "جِي   دور"])

    assert fake.calls == [["حيض", "جي دور"]]
    assert len(results) == 2
    assert results[0]["dense"] == [0.0, 0.0, 0.0, 0.0]
    assert results[1]["dense"] == [1.0, 1.0, 1.0, 1.0]


def test_model_loaded_lazily_once(monkeypatch):
    load_calls = []

    def fake_load():
        load_calls.append(1)
        return _FakeModel()

    monkeypatch.setattr(embed_module, "_model", None)
    monkeypatch.setattr(embed_module, "_load_model", fake_load)

    embed_module.embed_text("a")
    embed_module.embed_text("b")

    assert len(load_calls) == 1, "model should only be loaded once across multiple calls"
