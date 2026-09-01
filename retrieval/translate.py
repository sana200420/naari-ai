"""Sindhi -> English query translation for Lever 4 (cross-lingual dual index).

NLLB-200-distilled-600M, loaded once (module-level singleton) and lazily —
mirrors retrieval/embed.py's pattern. Runs locally on CPU (~200ms/query per
docs/PLAYBOOKS.md), no external API. Tests in
retrieval/tests/test_translate.py monkeypatch _get_model() so they never
actually load the model.
"""

import threading

SRC_LANG = "snd_Arab"
TGT_LANG = "eng_Latn"
MODEL_NAME = "facebook/nllb-200-distilled-600M"

_model = None
_tokenizer = None
_model_lock = threading.Lock()


def _load_model():
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, src_lang=SRC_LANG)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    return model, tokenizer


def _get_model():
    global _model, _tokenizer
    if _model is None:
        with _model_lock:
            if _model is None:
                _model, _tokenizer = _load_model()
    return _model, _tokenizer


def translate_sd_to_en(text: str) -> str:
    """Translate a single Sindhi string to English. Returns the source text
    unchanged if it's empty (nothing to translate, avoids a wasted model call)."""
    if not text.strip():
        return text
    return translate_batch([text])[0]


def translate_batch(texts: list[str]) -> list[str]:
    model, tokenizer = _get_model()
    inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True)
    generated = model.generate(
        **inputs,
        forced_bos_token_id=tokenizer.convert_tokens_to_ids(TGT_LANG),
        max_length=256,
    )
    return tokenizer.batch_decode(generated, skip_special_tokens=True)
