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

import json
import os

import gradio as gr

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


def ask_api(query: str, language: str = "sindhi") -> str:
    """The structured endpoint the web frontend calls.

    Returns the full AskResponse shape from docs/contracts/retrieval.json --
    answer, path, confidence_band, retrieved_ids, latency_ms and the rest --
    rather than the chat UI's display string, so the frontend can branch on
    the band and show the danger/refusal paths differently from a normal
    answer. Reachable from JS via @gradio/client:
        const app = await Client.connect("Sanapalijo/naari-ai");
        const r = await app.predict("/ask", { query, language: "sindhi" });

    Returns a JSON *string*, not a dict: gradio_client walks structured
    return values looking for file paths to download, and cheerfully tried to
    GET "/gradio_api/file=verbatim" off the `path` field. A string is opaque
    to that traversal, so the caller does one JSON.parse and gets the real
    shape back.
    """
    if not query or not query.strip():
        return json.dumps({"error": "empty query"}, ensure_ascii=False)
    result = run_pipeline(AskRequest(query=query, language=language)).model_dump()
    return json.dumps(result, ensure_ascii=False)


# Everything is built inside a single Blocks context. Re-entering `with demo:`
# on an already-constructed ChatInterface to attach gr.api made launch() stop
# blocking, so `python app.py` fell off the end and exited -- the Space came
# up and then died with RUNTIME_ERROR. Constructing both children in one
# context up front is the canonical shape and avoids that entirely.
with gr.Blocks(title=TITLE) as demo:
    gr.ChatInterface(
        fn=answer,
        title=TITLE,
        description=DESCRIPTION,
        examples=[
            "حيض جي چڪر ڇا آهي؟",
            "حمل دوران الٽي ٿئي ته ڇا ڪجي؟",
            "ٻار کي کير پيارڻ جا فائدا ڇا آهن؟",
        ],
    )
    gr.api(ask_api, api_name="ask")


# Serve via Gradio's own launcher -- the canonical Gradio-SDK Space entrypoint.
# Hugging Face runs `python app.py` and expects it to block serving.
#
# Three other shapes were tried on the Space and all failed; don't re-try them:
#   1. gr.mount_gradio_app onto our FastAPI + uvicorn.run() -> "[Errno 98]
#      address already in use" on 7860.
#   2. Omitting the bind entirely -> the script ran to completion and exited,
#      which the Space reports as RUNTIME_ERROR.
#   3. launch(prevent_thread_lock=True) then demo.app.mount("/api", ...) ->
#      built and ran, but every /api/* request came back as Gradio's HTML;
#      the mount never reached the server actually being proxied. Worked
#      locally, which is exactly why it needed checking on the Space.
#
# The REST contract is instead exposed through gr.api (see ask_api above),
# which is Gradio's supported mechanism for this and needs no FastAPI at all.
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")))
