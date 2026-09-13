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
BAND_CONFIRM = "confirm"

# One definition, because two paths need to *recognise* it, not just emit it.
_REFUSAL = "معاف ڪجو، مون وٽ هن سوال جو جواب ناهي. مهرباني ڪري ليڊي هيلٿ ورڪر سان رابطو ڪريو."

_logger = logging.getLogger("naari.pipeline")

# Three tiers, measured on all 247 gold queries (eval/tau_high_sweep.csv):
#
#   score >= TAU_HIGH     assert the stored answer   26% of traffic, 84% precise
#   TAU_CONFIRM..TAU_HIGH offer it for confirmation   17% of traffic, 49% precise
#   TAU_LOW..TAU_CONFIRM  grounded generation, hedged
#   below TAU_LOW         refuse honestly
#
# TAU_HIGH was 0.75, which asserted 42% of traffic at 70% precision -- 12.6% of
# ALL queries answered incorrectly as verified fact. At 0.95 that falls to 4.0%.
#
# The middle tier exists because its precision is 0.488: a coin flip is the
# worst thing to state as fact and the best thing to ask about. Setting
# TAU_CONFIRM equal to TAU_HIGH collapses the tier and disables confirmation
# entirely, which is how to turn this off without a code change.
TAU_HIGH = float(os.getenv("TAU_HIGH", "0.95"))
TAU_CONFIRM = float(os.getenv("TAU_CONFIRM", "0.75"))

# Superseded by TAU_CONFIRM. Kept only so an existing CONFIRM_HIGH_BAND=false
# in a deployment still disables confirmation rather than being ignored.
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

# Provider order, fastest-reliable first. Measured against the live keys:
#
#   Groq    958ms, succeeded
#   Gemini  2.7s,  failed (503 "high demand"; free tier is also 20 req/day)
#
# Gemini was first because ADR 0001 picked it for Sindhi comprehension. But a
# provider that 503s does not produce comprehension -- it produces a 2.7s delay
# before the fallback runs, on every single answer. That was most of the ~7.5s
# the LLM step was costing. Groq's Sindhi output is good enough that the
# quality argument no longer outweighs being three times faster and actually
# available. Set LLM_ORDER=gemini,groq to restore the old precedence.
LLM_ORDER = [p.strip() for p in os.getenv("LLM_ORDER", "groq,gemini").split(",") if p.strip()]

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
    # use_embedding=False matches Sabiha's production call. The embedding path
    # is retired: measured on her latest gate, keywords alone reach 1.00 on both
    # her 100-case set and my independent 52-phrase bank, while enabling the
    # embedding path adds 15.5ms and turns three ordinary questions into
    # emergencies -- a PCOS diet question, a pre-conception planning question,
    # and one about low mood affecting daily life.
    gate: GateResult = run_danger_gate(query, use_embedding=False)
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
    confirm_floor = TAU_CONFIRM if CONFIRM_HIGH_BAND else TAU_HIGH
    if top_score >= TAU_HIGH and chunks:
        band = BAND_HIGH
    elif top_score >= confirm_floor and chunks and chunks[0].get("question"):
        band = BAND_CONFIRM
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
        path = "verbatim"

        answer_text = top["text"]
        if ELABORATE_ANSWERS:
            expanded = output_filter(elaborate(query, chunks))
            # output_filter returns the refusal string when it blocks something.
            # On the high band we hold a verified row, so a blocked expansion
            # falls back to that row rather than refusing outright.
            # Only claim "expanded" if the text actually changed. elaborate()
            # falls back to the stored row when both LLMs fail, and labelling
            # that as expanded hid a silent failure behind a success label --
            # which is how the empty-content Groq bug went unnoticed.
            if expanded and expanded != _REFUSAL and expanded != top["text"]:
                answer_text = expanded
                path = "expanded" if path == "verbatim" else path
            elif expanded == top["text"]:
                _logger.warning("elaboration fell back to the stored answer "
                                "(both LLMs unavailable)")
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
        )

    # Stage 05b: confirm band -> offer the matched question, do not assert
    if band == BAND_CONFIRM:
        top = chunks[0]
        latency = round((time.time() - t0) * 1000, 2)
        _log(query, [c["id"] for c in chunks], [top_score], BAND_CONFIRM,
             "confirm", latency, "kb", request.session_id)
        return AskResponse(
            # The answer ships with this response so "yes" reveals it without a
            # second round-trip -- that would cost several more seconds on a
            # rural connection for data already in hand. Deliberately NOT
            # elaborated: spending an LLM call expanding an answer that is a
            # coin flip to be right is the wrong place for it.
            answer=top["text"],
            audio_url=top.get("audio_url"),
            path="confirm",
            confidence_band=BAND_CONFIRM,
            escalated=False,
            disclaimer=False,
            retrieved_ids=[c["id"] for c in chunks],
            latency_ms=latency,
            did_you_mean=top.get("question"),
            alternatives=[c["question"] for c in chunks[1:4] if c.get("question")],
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


def _as_paragraph(text: str) -> str:
    """Collapse an answer to continuous prose.

    The prompt asks for a paragraph, but models drift back to bullets and line
    breaks, and the chat bubble renders those as a list. Rather than trust the
    instruction, join the lines and strip any leading list markers -- Sindhi
    prose reads badly as fragments, and a bulleted health answer looks like a
    checklist rather than advice.
    """
    import re

    lines = [re.sub(r"^[\s\-\*•\d\.\)]+", "", ln).strip()
             for ln in str(text).splitlines()]
    return " ".join(ln for ln in lines if ln)


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
- Write ONE flowing paragraph of 5 to 6 sentences in simple Sindhi a village
  reader understands. Do NOT use bullet points, numbered lists, dashes, or
  line breaks. It must read as continuous prose.
- Keep any advice to see a health worker, and keep it in the paragraph.

VERIFIED ANSWER:
{primary}

SUPPORTING NOTES (context only, may be unrelated -- ignore if so):
{supporting}

Her question: {query}

Fuller answer in Sindhi:"""

    for out in _try_providers(prompt):
        return _as_paragraph(out)
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
Write ONE flowing paragraph of 5 to 6 sentences in simple Sindhi a village reader understands. No bullet points, no numbered lists, no line breaks.

Context:
{context}

Question: {query}

Answer in Sindhi:"""

    for answer in _try_providers(prompt):
        return _as_paragraph(answer)

    return "معاف ڪجو، في الحال جواب ڏيڻ ممڪن ناهي. مهرباني ڪري ليڊي هيلٿ ورڪر سان رابطو ڪريو."


def _try_providers(prompt: str):
    """Yield the first provider response that comes back, in LLM_ORDER.

    A generator so the caller can `for x in ...: return x` and stop at the
    first success without a sentinel dance.
    """
    providers = {"groq": _try_groq, "gemini": _try_gemini}
    for name in LLM_ORDER:
        fn = providers.get(name)
        if fn is None:
            _logger.warning("LLM_ORDER names unknown provider %r, skipping", name)
            continue
        out = fn(prompt)
        if out:
            yield out
            return


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
        # gpt-oss-120b is a REASONING model: it writes an internal monologue
        # into `reasoning` before `content`, and both come out of the same
        # token budget. At 512 it spent the lot thinking and returned an empty
        # string with finish_reason="length" -- which read as "Groq failed"
        # and silently fell through to the static answer. Low effort plus a
        # real budget leaves room for the reply itself.
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=2048,
            reasoning_effort="low",
        )
        text = (response.choices[0].message.content or "").strip()
        if not text:
            _logger.warning("groq returned empty content (finish_reason=%s); "
                            "the model likely spent its budget reasoning",
                            response.choices[0].finish_reason)
            return None
        return text
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
