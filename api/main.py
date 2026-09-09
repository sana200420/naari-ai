import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import ask, health

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
app.include_router(ask.router)

# Model loading takes ~230s cold (eval/results.md, Item 1). Left lazy, that
# cost lands on whichever real user sends the first query. Done synchronously
# at startup, it blocks the port from opening and the platform health check
# times out and marks the boot failed. So: warm in a background thread, serve
# /health immediately, and expose readiness separately at /ready.
_warm = {"ready": False, "error": None}


def _warmup() -> None:
    try:
        from retrieval.pipeline import warmup

        warmup()
        _warm["ready"] = True
    except Exception as exc:  # a failed warmup must not kill the process --
        _warm["error"] = f"{type(exc).__name__}: {exc}"  # lazy loading still works


@app.on_event("startup")
def _start_warmup() -> None:
    threading.Thread(target=_warmup, daemon=True).start()


@app.get("/ready")
def ready():
    """Distinguishes 'process is up' (/health) from 'models are loaded'.
    Poll this before a demo -- a query sent while ready is false still works,
    it just pays the remaining cold-start cost."""
    return {"ready": _warm["ready"], "warmup_error": _warm["error"]}
