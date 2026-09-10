"""
Phase 2 — Main pipeline: stages 00-08
Danger gate short-circuits everything — a danger query never reaches retrieval or LLM.
"""
import logging
import time
import os
import re
from api.safety.danger_gate import run_danger_gate, GateResult
from api.routers.ask import AskRequest, AskResponse

# Three confidence bands
BAND_HIGH = "high"
BAND_MID = "mid"
BAND_LOW = "low"

# One definition, because two paths need to *recognise* it, not just emit it.
_REFUSAL = "معاف ڪجو، مون وٽ هن سوال جو جواب ناهي. مهرباني ڪري ليڊي هيلٿ ورڪر سان رابطو ڪريو."

_logger = logging.getLogger("naari.pipeline")

TAU_HIGH = float(os.getenv("TAU_HIGH", "0.75"))

# The high band used to assert the stored answer as fact. Cross-validation
# (eval/results.md, Diagnostic 4) showed no threshold reaches 0.95 precision --
# the ceiling is 83.6% at 24.6% coverage, and it *drops* at stricter cutoffs,
# which is the signature of a real ceiling rather than an unexplored tradeoff.
# Live, 4 of 11 menstruation questions came back verbatim/high and wrong: a
# woman asking about nausea in her period was told about breastfeeding, stated
# as fact.
#
# 83.6% precision is unacceptable for asserting and perfectly fine for
# suggesting, so the high band now offers the matched question back for
# confirmation. Set CONFIRM_HIGH_BAND=false to restore the old assert-verbatim
# behaviour; it is a flag rather than a rewrite so the change is reversible
# from a Space setting during a demo.
CONFIRM_HIGH_BAND = os.getenv("CONFIRM_HIGH_BAND", "true").strip().lower() not in ("false", "0", "no")

# KB answers are one or two sentences, which reads as curt for a health
# question. Elaboration expands the retrieved text to 5-6 lines.
#
# This is a real change to the safety posture and worth stating plainly: with
# it on, an LLM touches the high-confidence path, which previously served
# stored text untouched. It is constrained to rephrasing and structuring the
# retrieved rows -- forbidden from adding any fact not in them -- and its
# output still goes through output_filter(). On any failure it falls back to
# the verbatim KB text, so a broken LLM degrades to the old behaviour rather
# than to nothing.
ELABORATE_ANSWERS = os.getenv("ELABORATE_ANSWERS", "true").strip().lower() not in ("false", "0", "no")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# Logger — never import at top level to avoid circular imports
def _log(query, retrieved_ids, scores, band, path, latency_ms, provider, session_id=None):
    try:
        from api.logging.logger import log_query
        log_query(query, retrieved_ids, scores, band, path, latency_ms, provider, session_id)
    except Exception:
        pass

TAU_LOW = float(os.getenv("TAU_LOW", "0.2034"))


def run_pipeline(request: AskRequest) -> AskResponse:
    t0 = time.time()
    query = request.query

    # Stage 00: danger gate — runs FIRST, always
    gate: GateResult = run_danger_gate(query)
    if gate.escalate:
        latency = round((time.time() - t0) * 1000, 2)
        _log(query, [], [], BAND_HIGH, "danger", latency, "gate", request.session_id)
        return AskResponse(
            answer=gate.response,
            audio_url=None,
            path="danger",
            confidence_band=BAND_HIGH,
            escalated=True,
            disclaimer=False,
            retrieved_ids=[],
            latency_ms=latency,
        )

    # Stage 01: scope classifier
    if gate.scope_block:
        latency = round((time.time() - t0) * 1000, 2)
        _log(query, [], [], BAND_HIGH, "referral", latency, "scope", request.session_id)
        return AskResponse(
            answer=gate.response,
            audio_url=None,
            path="referral",
            confidence_band=BAND_HIGH,
            escalated=False,
            disclaimer=False,
            retrieved_ids=[],
            latency_ms=latency,
        )

    # Stage 02: retrieval
    from retrieval.pipeline import search as retrieval_search

    retrieval_result = retrieval_search(query)
    chunks = [
        {"id": r["answer_id"], "text": r["answer"], "score": r["score"],
         "question": r.get("question", "")}
        for r in retrieval_result["results"]
    ]
    top_score = chunks[0]["score"] if chunks else 0.0

    # Stage 03: confidence band decision
    if top_score >= TAU_HIGH and chunks:
        band = BAND_HIGH
    elif top_score >= TAU_LOW and chunks:
        band = BAND_MID
    else:
        band = BAND_LOW

    # Stage 04: low band -> refusal
    if band == BAND_LOW:
        latency = round((time.time() - t0) * 1000, 2)
        _log(query, [], [top_score], BAND_LOW, "refusal", latency, "none", request.session_id)
        return AskResponse(
            answer="معاف ڪجو، مون وٽ هن سوال جو جواب ناهي. مهرباني ڪري ليڊي هيلٿ ورڪر سان رابطو ڪريو.",
            audio_url=None,
            path="refusal",
            confidence_band=BAND_LOW,
            escalated=False,
            disclaimer=False,
            retrieved_ids=[],
            latency_ms=latency,
        )

    # Stage 05: high band -> confirm, then serve verbatim
    if band == BAND_HIGH:
        top = chunks[0]
        latency = round((time.time() - t0) * 1000, 2)
        path = "confirm" if (CONFIRM_HIGH_BAND and top.get("question")) else "verbatim"

        answer_text = top["text"]
        if ELABORATE_ANSWERS:
            expanded = output_filter(elaborate(query, chunks))
            # output_filter returns the refusal string when it blocks something.
            # On the high band we hold a verified row, so a blocked expansion
            # falls back to that row rather than refusing outright.
            if expanded and expanded != _REFUSAL:
                answer_text = expanded
                path = "expanded" if path == "verbatim" else path
            latency = round((time.time() - t0) * 1000, 2)

        _log(query, [c["id"] for c in chunks], [top_score], BAND_HIGH, path, latency, "kb", request.session_id)
        return AskResponse(
            answer=answer_text,
            audio_url=top.get("audio_url"),
            path=path,
            confidence_band=BAND_HIGH,
            escalated=False,
            # A confirmed match is a verified KB row, so no disclaimer -- the
            # hedging is carried by the question being shown first.
            disclaimer=False,
            retrieved_ids=[c["id"] for c in chunks],
            latency_ms=latency,
            did_you_mean=top.get("question") if path == "confirm" else None,
            # The answer is already retrieved, so it ships with this response
            # and the frontend reveals it on "yes". A second round-trip would
            # cost another ~4s on a rural connection for data we already hold.
            alternatives=[c["question"] for c in chunks[1:4] if c.get("question")]
            if path == "confirm" else [],
        )

    # Stage 06: mid band -> constrained generation
    answer = generate(query, chunks)

    # Stage 07: output filter
    answer = output_filter(answer)

    latency = round((time.time() - t0) * 1000, 2)
    _log(query, [c["id"] for c in chunks], [top_score], BAND_MID, "generated", latency, "llm", request.session_id)
    return AskResponse(
        answer=answer,
        audio_url=None,
        path="generated",
        confidence_band=BAND_MID,
        escalated=False,
        disclaimer=True,
        retrieved_ids=[c["id"] for c in chunks],
        latency_ms=latency,
    )


def elaborate(query: str, chunks: list) -> str:
    """Expand a retrieved KB answer into a fuller reply, adding no new facts.

    The high band has a verified row in hand, so the job here is presentation,
    not research: say the same thing in 5-6 lines a woman can act on. The
    prompt names that boundary repeatedly because it is the only thing keeping
    this path as safe as the verbatim one it replaces.
    """
    primary = chunks[0]["text"]
    supporting = "\n".join(c["text"] for c in chunks[1:3])
    prompt = f"""You are NaariAI, a Sindhi women's health assistant.

Rewrite the VERIFIED ANSWER below so it is fuller and easier to act on.

Rules, all mandatory:
- Use ONLY the facts in the verified answer and supporting notes. Add nothing.
- Do NOT introduce any symptom, cause, treatment, medicine, dose or timeframe
  that is not already written below.
- Do NOT diagnose. Do NOT say symptoms are normal or nothing to worry about.
- Write 5 to 6 short lines in simple Sindhi a village reader understands.
- Keep any advice to see a health worker, and keep it prominent.

VERIFIED ANSWER:
{primary}

SUPPORTING NOTES (context only, may be unrelated -- ignore if so):
{supporting}

Her question: {query}

Fuller answer in Sindhi:"""

    for attempt in (_try_gemini, _try_groq):
        out = attempt(prompt)
        if out:
            return out
    # Both LLMs down: the stored answer is short but correct, which beats a
    # refusal on a path where we have a verified row.
    return primary


def generate(query: str, chunks: list) -> str:
    """Stage 06: constrained generation — Gemini -> Groq -> static fallback."""
    context = "\n".join(c["text"] for c in chunks)
    prompt = f"""You are NaariAI, a Sindhi women's health assistant.
Answer ONLY using the context below. If the context does not contain the answer, say you don't know.
Do NOT use your own knowledge. Do NOT diagnose. Do NOT name medicines or doses.
Do NOT reassure the user that symptoms are normal or nothing to worry about.
Write 5 to 6 short lines in simple Sindhi a village reader understands.

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
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        _logger.warning("gemini: GEMINI_API_KEY not set, skipping")
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as exc:
        _logger.warning("gemini failed: %s: %s", type(exc).__name__, exc)
        return None


def _try_groq(prompt: str) -> str:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        _logger.warning("groq: GROQ_API_KEY not set, skipping")
        return None
    try:
        from groq import Groq
        client = Groq(api_key=key)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=512,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        _logger.warning("groq failed: %s: %s", type(exc).__name__, exc)
        return None


def output_filter(text: str) -> str:
    """Stage 07: block medicine names, doses, diagnosis phrasing."""
    REFUSAL = _REFUSAL

    if re.search(r"\d+\s*(mg|ml|mcg|tablet|tablets|cap|capsule|dose)", text, re.IGNORECASE):
        return REFUSAL

    bad_phrases = [
        "nothing to worry", "don't worry", "it's normal", "just relax",
        "no need to worry", "probably nothing", "should be fine"
    ]
    for phrase in bad_phrases:
        if phrase.lower() in text.lower():
            return REFUSAL

    return text
