import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import ask, health, audio

app = FastAPI(
    title="NaariAI API",
    description="Sindhi Women's Health Voice Assistant Backend",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
)

app.include_router(health.router)
app.include_router(audio.router)
app.include_router(ask.router)

# Model loading takes ~230s cold (eval/results.md, Item 1). Left lazy, that
# cost lands on whichever real user sends the first query. Done synchronously
# at startup, it blocks the port from opening and the platform health check
# times out and marks the boot failed. So: warm in a background thread, serve
# /health immediately, and expose readiness separately at /ready.
_warm = {"ready": False, "error": None, "started": False}


_warm_lock = threading.Lock()


def _warmup() -> None:
    try:
        from retrieval.pipeline import warmup

        warmup()
        _warm["ready"] = True
    except Exception as exc:  # a failed warmup must not kill the process --
        _warm["error"] = f"{type(exc).__name__}: {exc}"  # lazy loading still works


def ensure_warm() -> None:
    """Start warmup once, from whichever entrypoint gets there first.

    On a Gradio-SDK Space, Hugging Face may serve the Gradio Blocks directly
    rather than the FastAPI app, in which case the startup event below never
    fires and the first real query would pay the full ~230s cold load. app.py
    calls this at module scope so warmup happens either way; the flag makes
    the second caller a no-op instead of loading every model a second time.
    """
    with _warm_lock:
        if _warm["started"]:
            return
        _warm["started"] = True
    threading.Thread(target=_warmup, daemon=True).start()


@app.on_event("startup")
def _start_warmup() -> None:
    ensure_warm()


@app.get("/ready")
def ready():
    """Distinguishes 'process is up' (/health) from 'models are loaded'.
    Poll this before a demo -- a query sent while ready is false still works,
    it just pays the remaining cold-start cost."""
    return {"ready": _warm["ready"], "started": _warm["started"], "warmup_error": _warm["error"]}
