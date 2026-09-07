"""
Phase 2 — Main pipeline: stages 00-08
Danger gate short-circuits everything — a danger query never reaches retrieval or LLM.
"""
import time
import os
import re
from api.safety.danger_gate import run_danger_gate, GateResult
from api.routers.ask import AskRequest, AskResponse

# Three confidence bands
BAND_HIGH = "high"
BAND_MID = "mid"
BAND_LOW = "low"

TAU_HIGH = float(os.getenv("TAU_HIGH", "0.75"))
TAU_LOW = float(os.getenv("TAU_LOW", "0.40"))


def run_pipeline(request: AskRequest) -> AskResponse:
    t0 = time.time()
    query = request.query

    # Stage 00: danger gate — runs FIRST, always
    gate: GateResult = run_danger_gate(query)
    if gate.escalate:
        return AskResponse(
            answer=gate.response,
            audio_url=None,
            path="danger",
            confidence_band=BAND_HIGH,
            escalated=True,
            disclaimer=False,
            retrieved_ids=[],
            latency_ms=round((time.time() - t0) * 1000, 2),
        )

    # Stage 01: scope classifier
    if gate.scope_block:
        return AskResponse(
            answer=gate.response,
            audio_url=None,
            path="referral",
            confidence_band=BAND_HIGH,
            escalated=False,
            disclaimer=False,
            retrieved_ids=[],
            latency_ms=round((time.time() - t0) * 1000, 2),
        )

    # Stage 02: retrieval (stub — Sana replaces with real KB retrieval)
    chunks = []
    top_score = 0.0

    # Stage 03: confidence band decision
    if top_score >= TAU_HIGH and chunks:
        band = BAND_HIGH
    elif top_score >= TAU_LOW and chunks:
        band = BAND_MID
    else:
        band = BAND_LOW

    # Stage 04: low band -> refusal
    if band == BAND_LOW:
        return AskResponse(
            answer="معاف ڪجو، مون وٽ هن سوال جو جواب ناهي. مهرباني ڪري ليڊي هيلٿ ورڪر سان رابطو ڪريو.",
            audio_url=None,
            path="refusal",
            confidence_band=BAND_LOW,
            escalated=False,
            disclaimer=False,
            retrieved_ids=[],
            latency_ms=round((time.time() - t0) * 1000, 2),
        )

    # Stage 05: high band -> verbatim
    if band == BAND_HIGH:
        top = chunks[0]
        return AskResponse(
            answer=top["text"],
            audio_url=top.get("audio_url"),
            path="verbatim",
            confidence_band=BAND_HIGH,
            escalated=False,
            disclaimer=False,
            retrieved_ids=[c["id"] for c in chunks],
            latency_ms=round((time.time() - t0) * 1000, 2),
        )

    # Stage 06: mid band -> constrained generation
    answer = generate(query, chunks)

    # Stage 07: output filter
    answer = output_filter(answer)

    return AskResponse(
        answer=answer,
        audio_url=None,
        path="generated",
        confidence_band=BAND_MID,
        escalated=False,
        disclaimer=True,
        retrieved_ids=[c["id"] for c in chunks],
        latency_ms=round((time.time() - t0) * 1000, 2),
    )


def generate(query: str, chunks: list) -> str:
    """Stage 06: constrained generation — Gemini -> Groq -> static fallback."""
    context = "\n".join(c["text"] for c in chunks)
    prompt = f"""You are NaariAI, a Sindhi women's health assistant.
Answer ONLY using the context below. If the context does not contain the answer, say you don't know.
Do NOT use your own knowledge. Do NOT diagnose. Do NOT name medicines or doses.
Do NOT reassure the user that symptoms are normal or nothing to worry about.

Context:
{context}

Question: {query}

Answer in Sindhi:"""

    answer = _try_gemini(prompt)
    if answer:
        return answer

    answer = _try_groq(prompt)
    if answer:
        return answer

    return "معاف ڪجو، في الحال جواب ڏيڻ ممڪن ناهي. مهرباني ڪري ليڊي هيلٿ ورڪر سان رابطو ڪريو."


def _try_gemini(prompt: str) -> str:
    """Try Gemini 2.5 Flash — returns None on any failure."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return None


def _try_groq(prompt: str) -> str:
    """Try Groq Llama — returns None on any failure."""
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return None
    try:
        from groq import Groq
        client = Groq(api_key=key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None


def output_filter(text: str) -> str:
    """Stage 07: block medicine names, doses, diagnosis phrasing."""
    REFUSAL = "معاف ڪجو، مون وٽ هن سوال جو جواب ناهي. مهرباني ڪري ليڊي هيلٿ ورڪر سان رابطو ڪريو."

    # Dose patterns — mg, ml, tablet, capsule
    if re.search(r"\d+\s*(mg|ml|mcg|tablet|tablets|cap|capsule|dose)", text, re.IGNORECASE):
        return REFUSAL

    # False reassurance phrases
    bad_phrases = [
        "nothing to worry", "don't worry", "it's normal", "just relax",
        "no need to worry", "probably nothing", "should be fine"
    ]
    for phrase in bad_phrases:
        if phrase.lower() in text.lower():
            return REFUSAL

    return text
