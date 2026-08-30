"""The only public way to embed text.

`embed_text` is the sole entry point for turning text into a vector, and it
calls `normalize_sd` unconditionally before doing anything else. Nobody
downstream should be able to embed raw text, even by accident — if you find
yourself calling a model's `.encode()` directly instead of importing this
function, stop and use this instead.

The actual model (bge-m3) is not wired up yet — that lands with the Qdrant
collection setup, later in Phase 1. This stub exists now so the
normalise-before-embed contract is fixed from day one and nothing built on
top of it can bypass normalisation.
"""

from retrieval.normalize import normalize_sd


def embed_text(text: str):
    """Embed a single string. Always normalises first.

    Raises NotImplementedError until the bge-m3 model is loaded.
    """
    normalized = normalize_sd(text)
    raise NotImplementedError(
        "bge-m3 embedding model is not wired up yet (Phase 1, next task). "
        f"Text was normalised successfully first: {normalized!r}"
    )
