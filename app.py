"""Hugging Face Spaces entrypoint (Gradio SDK).

The Docker SDK is a paid option on this account, so the Space runs under the
free Gradio SDK instead. That only changes how the process is *started* --
the service itself is unchanged: this mounts the existing FastAPI app, so
`/ask`, `/health` and `/ready` keep the exact shape
`docs/contracts/retrieval.json` and Tooba's frontend already depend on, and
Gradio's chat UI is served alongside it at `/`.

Free Gradio Spaces get CPU basic: 2 vCPU and 16GB RAM. The model set --
bge-m3, bge-reranker-v2-m3, NLLB-600M, and the danger gate's MiniLM -- peaks
around 8.5GB resident on CPU, so it fits here where Railway's 512MB free tier
never could.

Startup warmup still runs in api/main.py's background thread: the port opens
immediately, `/ready` reports when the models have finished loading.
"""

import os

import gradio as gr

from api.main import app as fastapi_app
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

# Mount Gradio *onto* the FastAPI app rather than the other way round, so the
# API routes stay at their existing paths and the UI takes "/".
app = gr.mount_gradio_app(fastapi_app, demo, path="/")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "7860")))
