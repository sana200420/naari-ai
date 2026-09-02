"""Tests for retrieval.translate. Monkeypatches _get_model() so no real
NLLB weights are ever loaded."""

import retrieval.translate as translate_module
from retrieval.translate import translate_batch, translate_sd_to_en


class _FakeTokenizer:
    def __call__(self, texts, return_tensors=None, padding=None, truncation=None):
        return {"input_ids": texts}

    def convert_tokens_to_ids(self, token):
        return f"id_for_{token}"

    def batch_decode(self, generated, skip_special_tokens=None):
        return generated


class _FakeModel:
    def generate(self, input_ids, forced_bos_token_id=None, max_length=None):
        assert forced_bos_token_id == "id_for_eng_Latn"
        return [f"EN[{t}]" for t in input_ids]


def test_translate_sd_to_en_returns_translated_string(monkeypatch):
    monkeypatch.setattr(translate_module, "_get_model", lambda: (_FakeModel(), _FakeTokenizer()))

    result = translate_sd_to_en("سلام")

    assert result == "EN[سلام]"


def test_translate_batch_preserves_order(monkeypatch):
    monkeypatch.setattr(translate_module, "_get_model", lambda: (_FakeModel(), _FakeTokenizer()))

    result = translate_batch(["a", "b", "c"])

    assert result == ["EN[a]", "EN[b]", "EN[c]"]


def test_translate_sd_to_en_skips_the_model_for_empty_text(monkeypatch):
    def _fail():
        raise AssertionError("should not load the model for empty input")

    monkeypatch.setattr(translate_module, "_get_model", _fail)

    assert translate_sd_to_en("") == ""
    assert translate_sd_to_en("   ") == "   "
