"""Hugging Face Spaces entrypoint (Gradio SDK, ZeroGPU hardware, CPU-resident).

Hardware, because it is not obvious: a free HF account cannot host a Gradio
Space on `cpu-basic` -- that needs PRO (verified: the API returns 402 Payment
Required). The one free path is `zero-a10g`, so the Space sits there with a
single no-op `@spaces.GPU` function to satisfy ZeroGPU's "at least one
decorated function" requirement, and every bit of real work stays outside it.
Nothing ever requests a GPU, so no ZeroGPU quota is burned. This is the
documented pattern for CPU-bound Spaces on a free account.

Consequence worth knowing: `import spaces` patches `torch.cuda.*` in this
process so `torch.cuda.is_available()` answers True with no GPU attached.
`retrieval/device.py` deliberately ignores that and pins everything to CPU --
see its docstring.

This mounts the existing FastAPI app rather than replacing it, so `/ask`,
`/health` and `/ready` keep the exact shape `docs/contracts/retrieval.json`
and Tooba's frontend already depend on, with Gradio's chat UI at `/`.

Startup warmup still runs in api/main.py's background thread: the port opens
immediately, `/ready` reports when the models have finished loading.
"""

import spaces  # must precede anything that touches torch/CUDA

import os
import threading

import gradio as gr

from api.main import app as fastapi_app
from api.main import ensure_warm
from api.pipeline import run_pipeline
from api.routers.ask import AskRequest

TITLE = "نارِي اي آءِ — Naari AI"
DESCRIPTION = (
    "سنڌي ۾ عورتن جي صحت بابت سوال پڇو. جواب هڪ تصديق ٿيل ڄاڻ جي ذخيري مان ايندا آهن.\n\n"
    "*Ask a women's health question in Sindhi. Answers come from a verified "
    "knowledge base, not free-form generation.*"
)

# Shown under the chat so a demo audience can see which path answered, rather
# than having to trust an opaque bubble. Mirrors the AskResponse fields.
_PATH_LABEL = {
    "danger": "🚨 خطري جي نشاني — فوري طبي مدد (danger gate)",
    "referral": "↗️ دائري کان ٻاهر (out of scope)",
    "refusal": "🚫 ڀروسي لائق جواب ناهي (low confidence)",
    "verbatim": "✅ ڄاڻ جي ذخيري مان لفظ به لفظ (verbatim)",
    "generated": "✍️ ذخيري جي بنياد تي ٺاهيل (grounded generation)",
}


# Kick the model load off now, regardless of which server ends up running:
# on a Gradio-SDK Space, Hugging Face may serve the Blocks directly and never
# fire FastAPI's startup event. ensure_warm() is idempotent.
ensure_warm()


@spaces.GPU(duration=1)
def _noop():
    """ZeroGPU refuses to start without at least one decorated function.
    Never called, never wired to an event -- the whole pipeline runs on CPU
    in the main process, so no GPU is ever requested and no quota is spent."""


def answer(message: str, history) -> str:
    if not message or not message.strip():
        return "مهرباني ڪري سوال لکو."
    try:
        response = run_pipeline(AskRequest(query=message, language="sindhi"))
    except Exception as exc:
        # Never surface a stack trace to someone asking a health question.
        return f"معاف ڪجو، هڪ خرابي ٿي آهي. ({type(exc).__name__})"

    label = _PATH_LABEL.get(response.path, response.path)
    footer = f"\n\n---\n<sub>{label} · {response.latency_ms:.0f}ms</sub>"
    if response.disclaimer:
        footer = (
            "\n\n---\n<sub>⚠️ هي طبي مشورو ناهي. ڪنهن به شڪ ۾ ليڊي هيلٿ ورڪر سان "
            f"رابطو ڪريو.<br>{label} · {response.latency_ms:.0f}ms</sub>"
        )
    return response.answer + footer


demo = gr.ChatInterface(
    fn=answer,
    title=TITLE,
    description=DESCRIPTION,
    examples=[
        "حيض جي چڪر ڇا آهي؟",
        "حمل دوران الٽي ٿئي ته ڇا ڪجي؟",
        "ٻار کي کير پيارڻ جا فائدا ڇا آهن؟",
    ],
)

# Serve via Gradio's own launcher -- the canonical Gradio-SDK Space entrypoint.
#
# Hugging Face runs `python app.py` and expects it to block serving. Two other
# shapes were tried on the Space and both failed, so don't re-try them:
# mounting Gradio onto our FastAPI and serving with uvicorn.run() died with
# "[Errno 98] address already in use" on 7860 (HF is already serving that
# port), and omitting the bind entirely let the script run to completion and
# exit, which the Space reports as RUNTIME_ERROR.
#
# Gradio's own FastAPI instance only exists after launch(), so the REST API is
# mounted onto it immediately afterwards with prevent_thread_lock=True, then
# this thread blocks forever. That puts the docs/contracts/retrieval.json
# endpoints under /api -- /api/ask, /api/health, /api/ready -- alongside the
# chat UI at /, so Tooba's frontend has a real endpoint to call instead of
# having to speak Gradio's two-step queue protocol.
#
# The sub-app's own startup events do not fire when it is mounted after the
# server is already running, which is why warmup is kicked off by
# ensure_warm() at module scope above rather than relying on FastAPI's
# startup hook.
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
        prevent_thread_lock=True,
    )
    demo.app.mount("/api", fastapi_app)
    threading.Event().wait()
