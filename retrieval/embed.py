"""The only public way to embed text.

embed_text()/embed_batch() call normalize_sd() unconditionally before doing
anything else. Nobody downstream should be able to embed raw text, even by
accident — if you find yourself calling a model's `.encode()` directly
instead of importing this, stop and use this instead.

The model is bge-m3, loaded once (module-level singleton) and lazily — the
first call pays the load cost, every call after is fast. Needs several GB of
free RAM; on a constrained machine, prefer running this on Colab or
whatever the deployed service's environment is instead of locally. Tests in
retrieval/tests/test_embed.py monkeypatch _get_model() so they never
actually load the model.
"""

import threading

from retrieval.normalize import normalize_sd

_model = None
_model_lock = threading.Lock()


def _load_model():
    from FlagEmbedding import BGEM3FlagModel

    return BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)


def _get_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = _load_model()
    return _model


def embed_text(text: str) -> dict:
    """Embed a single string. Always normalises first.

    Returns {"dense": list[float] (1024-d), "sparse": dict[str, float]}.
    """
    return embed_batch([text])[0]


def embed_batch(texts: list[str]) -> list[dict]:
    """Embed a batch of strings. Always normalises every one first."""
    normalized = [normalize_sd(t) for t in texts]
    model = _get_model()
    out = model.encode(normalized, return_dense=True, return_sparse=True, return_colbert_vecs=False)
    return [
        {"dense": dense.tolist(), "sparse": sparse}
        for dense, sparse in zip(out["dense_vecs"], out["lexical_weights"])
    ]
