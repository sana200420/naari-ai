"""Sindhi -> English query translation for Lever 4 (cross-lingual dual index).

NLLB-200-distilled-600M, loaded once (module-level singleton) and lazily —
mirrors retrieval/embed.py's pattern. Target deployment (docs/ROADMAP.md:
HF Spaces free CPU tier) is CPU, ~200ms/query per docs/PLAYBOOKS.md — but
that figure assumes the ONNX int8 conversion Phase 2 hasn't done yet.
Unoptimized float32 HF `generate()` (autoregressive, beam search) is slow
on CPU, so this auto-uses CUDA when available (e.g. during Colab
verification runs) and falls back to CPU otherwise. Confirmed live: moving
this model to GPU took a ~50s-per-query CPU bottleneck down to
sub-second. Tests in retrieval/tests/test_translate.py monkeypatch
_get_model() so they never actually load the model.
"""

import threading

SRC_LANG = "snd_Arab"
TGT_LANG = "eng_Latn"
MODEL_NAME = "facebook/nllb-200-distilled-600M"

_model = None
_tokenizer = None
_device = "cpu"
_model_lock = threading.Lock()


def _load_model():
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, src_lang=SRC_LANG)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(device)
    return model, tokenizer, device


def _get_model():
    global _model, _tokenizer, _device
    if _model is None:
        with _model_lock:
            if _model is None:
                _model, _tokenizer, _device = _load_model()
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
    if _device != "cpu":
        inputs = inputs.to(_device)
    generated = model.generate(
        **inputs,
        forced_bos_token_id=tokenizer.convert_tokens_to_ids(TGT_LANG),
        max_length=256,
    )
    return tokenizer.batch_decode(generated, skip_special_tokens=True)
