"""Generate the retrieval design document in both formats from one source.

The content lives here as structured data, and both outputs are generated from
it, so docs/how_retrieval_works.md and the Word version cannot drift apart --
which is what happens the moment someone edits one and forgets the other.

Outputs:
    docs/how_retrieval_works.md          versioned, reviewable in a PR
    docs/How_Retrieval_Works.docx        for the FYP report

Every figure here is traceable to eval/results.md. Update that first, then
this, then re-run.

    python scripts/build_retrieval_doc.py
"""

import os
import sys

MD_OUT = os.path.join("docs", "how_retrieval_works.md")
DOCX_OUT = os.path.join("docs", "How_Retrieval_Works.docx")

TITLE = "How Retrieval Works"
SUBTITLE = "Naari AI — retrieval core"

INTRO = [
    ("p", "What happens between a woman typing a question in Sindhi and an answer "
          "coming back: each stage, why it exists, and what breaks without it."),
    ("p", "**Who this is for.** Sections 1 and 2 are for the team — section 1 is the "
          "contract the API depends on, and section 2 says which stage owns which "
          "failure, so a bug lands with the right person. Sections 3 and 4 are for the "
          "report and viva — the design rationale for each choice over its obvious "
          "alternative, with the measured evidence behind it."),
    ("p", "Owner: Sana (retrieval core). Contract: `docs/contracts/retrieval.json`. "
          "All figures: `eval/results.md`."),
]

CONTRACT = [
    ("h2", "1. The contract"),
    ("p", "Everything in this document sits behind a single call. The API never "
          "touches Qdrant, an embedding model, or a reranker directly — it calls "
          "this, and gets back the same shape every time."),
    ("code",
     "from retrieval.pipeline import search\n"
     "\n"
     'result = search("حيض جي چڪر ڇا آهي؟")\n'
     "\n"
     "{\n"
     '  "query_normalised": str,   # after normalize_sd(), for logs\n'
     '  "latency_ms": int,\n'
     '  "results": [{\n'
     '     "answer_id": int,       # the KB id, stable across languages\n'
     '     "question": str,        # the KB question that matched\n'
     '     "answer": str,          # the Sindhi answer text\n'
     '     "category": str, "sub_category": str, "source": str,\n'
     '     "score": float,         # reranked relevance, higher is better\n'
     '     "path": str,            # which retrieval leg found it\n'
     "  }]\n"
     "}"),
    ("h3", "Three guarantees"),
    ("p", "**The query is normalised for you.** Pass the raw user string. `search()` "
          "calls `normalize_sd()` internally, exactly as `embed_text()` does — nobody "
          "downstream should normalise twice or forget to."),
    ("p", "**`answer_id` is the join key.** It matches the KB `id` column and is stable "
          "across Sindhi, English and any future variant rows. Log it, cache on it, "
          "evaluate against it."),
    ("p", "**Empty results are not an error.** No match returns `\"results\": []`, never "
          "an exception. The band logic treats that as low confidence and refuses "
          "honestly."),
]

STAGES = [
    ("Normalisation", "retrieval/normalize.py",
     "Folds the Arabic-script variants a Sindhi keyboard produces: Yeh forms, the "
     "Urdu word-final Heh, Urdu-keyboard Kaf slips, typographic quotes, Arabic-Indic "
     "digits.",
     "The same word typed on two keyboards is two different byte strings. Without "
     "folding, they are two different vectors.",
     "Retrieval silently degrades for exactly the users on cheap phones with mixed "
     "keyboards — the intended audience."),
    ("Dense search", "bge-m3, 1024-d",
     "Embeds the query and finds the 25 nearest KB questions by meaning, filtered to "
     "lang=\"sd\".",
     "Catches paraphrase: a question worded completely differently still lands near "
     "its answer.",
     "Only exact word matches work. Any rephrasing fails."),
    ("Sparse search", "bge-m3 lexical head",
     "Learned term weights over the same 25-deep shortlist — the same model, one "
     "forward pass, two vectors.",
     "Dense embeddings blur rare specifics. A drug name, a body part, an exact Sindhi "
     "term survives here when it gets smoothed away there.",
     "Rare-term questions drift to topically similar but wrong rows. Sparse alone "
     "scores 0.542 Recall@1 — it is not a garnish."),
    ("Reciprocal Rank Fusion", "k = 60",
     "Merges the two ranked lists using only each row's position: score contribution "
     "is 1/(k + rank), summed across lists.",
     "Dense cosine and sparse term weights are not on a comparable scale. Rank is the "
     "one thing both lists agree on the meaning of.",
     "You must hand-tune a blend weight per query type, and it silently rots as the "
     "knowledge base grows."),
    ("Cross-encoder rerank", "bge-reranker-v2-m3",
     "Scores every fused candidate as a (query, question) pair, rather than comparing "
     "two independently made vectors.",
     "A cross-encoder sees both texts at once and can judge relevance a bi-encoder "
     "cannot.",
     "You lose the score the confidence bands are calibrated on — and on this "
     "knowledge base, that score is now its main job (see section 3)."),
    ("English rescue leg", "NLLB-600M, conditional",
     "Only when the Sindhi reranked top score is below tau_high: translate the query "
     "to English and search the aligned English knowledge base.",
     "The English rows are better written, so an unclear Sindhi question sometimes "
     "matches its English twin when its Sindhi original fails.",
     "Of 20 sampled Sindhi-only misses, this rescued 4. Conditional costs nothing over "
     "always-on: identical Recall@1, 543 ms faster per query."),
]

WHY = [
    ("h2", "3. Why, not what"),
    ("h3", "Why rank fusion instead of blending scores"),
    ("p", "The obvious approach is a weighted blend, alpha times dense plus one minus "
          "alpha times sparse. It requires the two scores to mean comparable things, "
          "and they do not: cosine similarity sits in a narrow band near 1, while "
          "learned term weights are unbounded and vary with query length. Any alpha "
          "that works for a short question fails for a long one. Reciprocal Rank "
          "Fusion needs no calibration because it discards magnitude and keeps only "
          "order."),
    ("h3", "Why the reranker no longer picks the answer"),
    ("p", "Auditing 58 wrong-but-confident answers found the correct row had "
          "frequently been ranked first by fusion and then demoted by reranking. "
          "Across the 139 queries where the two disagreed, fusion was right 61 times "
          "and the reranker 10 — roughly 6:1 against trusting the override."),
    ("p", "That could have been noise, so the 139 were split randomly in half: 30:5 in "
          "one half, 31:5 in the other. The ratio holds independently, which makes it "
          "a property of this reranker on this knowledge base rather than a threshold "
          "fitted to a lucky split. `RERANK_OVERRIDE_MARGIN=2.0` sits deliberately "
          "outside the range a normalised score gap can reach, so fusion's pick always "
          "wins a disagreement. Recall@1 moved from 0.339 to 0.540."),
    ("note", "Consequence worth stating plainly: the reranker no longer selects any "
             "answer. It exists now to produce the score the confidence bands read. "
             "Removing it would save 2.3 GB of memory and change no answer — but "
             "tau_low is calibrated on its scores, so that swap needs a recalibration "
             "run first."),
    ("h3", "Why the high band asks instead of asserting"),
    ("p", "A threshold was wanted that could serve a stored answer as fact. Ten-fold "
          "cross-validation says none exists: no signal or combination exceeds roughly "
          "83.6% precision at 24.6% coverage, and precision drops at stricter cutoffs "
          "— the signature of a real ceiling, not an unexplored trade-off. Live "
          "testing agreed: 4 of 11 menstruation questions returned high-confidence "
          "wrong answers, including breastfeeding advice for a question about nausea."),
    ("p", "83.6% is unacceptable for asserting and entirely reasonable for suggesting. "
          "So the high band returns the matched question for confirmation, and the "
          "answer appears once she agrees that is what she asked. A wrong match "
          "becomes a visibly wrong question she can reject, instead of misinformation."),
    ("h3", "Why float32, after building the int8 version"),
    ("p", "ONNX int8 quantisation was exported, benchmarked and rejected. Latency "
          "passed comfortably — 292 ms p95 against a 1500 ms budget — but Recall@1 "
          "fell 2.42 points against a 1.0-point allowance. The optimisation was real; "
          "the accuracy cost was not affordable on a health knowledge base."),
]

EVIDENCE_ROWS = [
    ("Recall@1, final pipeline", "0.540", "up from 0.339 before the override guard"),
    ("Recall@20, fused shortlist", "0.726", "the right answer is usually already there"),
    ("Recall@1, KB's own questions", "0.979", "asking the KB a question it already contains"),
    ("Sparse leg alone", "0.542", "why sparse is not optional"),
    ("tau_low", "0.2034", "90 of 100 out-of-scope queries fall below"),
    ("tau_high precision ceiling", "83.6%", "at 24.6% coverage — why the band now asks"),
]

LIMITS = [
    ("27% of queries have no reachable answer",
     "They never surface the correct row anywhere in the top 20, so no amount of "
     "reranking or threshold tuning reaches them. This is a knowledge base coverage "
     "gap and needs content, not retrieval work."),
    ("tau_high is one variable doing two jobs",
     "api/pipeline.py reads it as the confidence band threshold; retrieval/pipeline.py "
     "reads it as the English-leg cascade gate. Setting it changes both. They should "
     "be split before either is tuned."),
    ("Variants are not in the index",
     "The 10,059-row batch reuses each original question's wording verbatim under "
     "about 95 prefix templates, so it adds no phrasing diversity. Measured: prefixed "
     "questions score 0.969 against 0.979 plain — harmless, but redundant."),
    ("Latency is 3 to 8 seconds",
     "Against a 3-second target, on two shared CPU cores with roughly 8.5 GB of models "
     "resident. The architecture is not the constraint; the free hosting tier is."),
]


# ---------------------------------------------------------------- markdown --

def build_markdown() -> str:
    L = [f"# {TITLE}", "", f"*{SUBTITLE}*", ""]
    for kind, text in INTRO:
        L += [text, ""]
    L += ["---", ""]

    for kind, text in CONTRACT:
        if kind == "h2":
            L += [f"## {text}", ""]
        elif kind == "h3":
            L += [f"### {text}", ""]
        elif kind == "code":
            L += ["```python", text, "```", ""]
        else:
            L += [text, ""]

    L += ["## 2. The stages", "",
          "Each stage below lists what it does, why it exists, and what breaks "
          "without it.", ""]
    for i, (name, impl, does, why, breaks) in enumerate(STAGES, 1):
        L += [f"### 2.{i} {name}", "",
              f"*{impl}*", "",
              f"- **Does.** {does}",
              f"- **Why.** {why}",
              f"- **Remove it.** {breaks}", ""]

    for kind, text in WHY:
        if kind == "h2":
            L += [f"## {text}", ""]
        elif kind == "h3":
            L += [f"### {text}", ""]
        elif kind == "note":
            L += [f"> {text}", ""]
        else:
            L += [text, ""]

    L += ["## 4. Evidence", "",
          "Measured on 248 individually verified queries.", "",
          "| Measurement | Value | Reading |", "|---|---:|---|"]
    for k, v, r in EVIDENCE_ROWS:
        L.append(f"| {k} | {v} | {r} |")
    L += ["",
          "**The gap that defines the next phase: 0.979 against 0.540.** Asked in the "
          "knowledge base's own words, retrieval is near-perfect. Asked in a woman's "
          "words, it is roughly a coin flip. That 44-point gap is not a model problem "
          "— it is a coverage problem in how many ways each question can be asked, and "
          "it is exactly what genuine colloquial variants are meant to close.", ""]

    L += ["## 5. Known limits", ""]
    for head, body in LIMITS:
        L += [f"### {head}", "", body, ""]

    L += ["---", "",
          "*Generated by `scripts/build_retrieval_doc.py`. Edit the script, not this "
          "file.*", ""]
    return "\n".join(L)


# -------------------------------------------------------------------- docx --

def _md_bold_runs(para, text):
    """Render **bold** spans and `code` spans inside a docx paragraph."""
    import re
    for part in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text):
        if part.startswith("**") and part.endswith("**"):
            para.add_run(part[2:-2]).bold = True
        elif part.startswith("`") and part.endswith("`"):
            r = para.add_run(part[1:-1])
            r.font.name = "Consolas"
        elif part:
            para.add_run(part)


def build_docx(path: str) -> None:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt, RGBColor

    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)

    h = doc.add_heading(TITLE, level=0)
    sub = doc.add_paragraph(SUBTITLE)
    sub.alignment = WD_ALIGN_PARAGRAPH.LEFT
    sub.runs[0].italic = True

    for _kind, text in INTRO:
        _md_bold_runs(doc.add_paragraph(), text)

    for kind, text in CONTRACT:
        if kind == "h2":
            doc.add_heading(text, level=1)
        elif kind == "h3":
            doc.add_heading(text, level=2)
        elif kind == "code":
            p = doc.add_paragraph()
            r = p.add_run(text)
            r.font.name = "Consolas"
            r.font.size = Pt(9)
        else:
            _md_bold_runs(doc.add_paragraph(), text)

    doc.add_heading("2. The stages", level=1)
    doc.add_paragraph("Each stage below lists what it does, why it exists, and what "
                      "breaks without it.")
    for i, (name, impl, does, why, breaks) in enumerate(STAGES, 1):
        doc.add_heading(f"2.{i} {name}", level=2)
        p = doc.add_paragraph()
        p.add_run(impl).italic = True
        for label, body in (("Does. ", does), ("Why. ", why), ("Remove it. ", breaks)):
            b = doc.add_paragraph(style="List Bullet")
            b.add_run(label).bold = True
            b.add_run(body)

    for kind, text in WHY:
        if kind == "h2":
            doc.add_heading(text, level=1)
        elif kind == "h3":
            doc.add_heading(text, level=2)
        elif kind == "note":
            p = doc.add_paragraph()
            r = p.add_run(text)
            r.italic = True
            r.font.color.rgb = RGBColor(0x4A, 0x19, 0x42)
        else:
            _md_bold_runs(doc.add_paragraph(), text)

    doc.add_heading("4. Evidence", level=1)
    doc.add_paragraph("Measured on 248 individually verified queries.")
    table = doc.add_table(rows=1, cols=3)
    table.style = "Light Grid Accent 1"
    hdr = table.rows[0].cells
    for cell, label in zip(hdr, ("Measurement", "Value", "Reading")):
        cell.text = label
        cell.paragraphs[0].runs[0].bold = True
    for k, v, r in EVIDENCE_ROWS:
        cells = table.add_row().cells
        cells[0].text, cells[1].text, cells[2].text = k, v, r
    p = doc.add_paragraph()
    _md_bold_runs(p, "**The gap that defines the next phase: 0.979 against 0.540.** "
                     "Asked in the knowledge base's own words, retrieval is "
                     "near-perfect. Asked in a woman's words, it is roughly a coin "
                     "flip. That 44-point gap is not a model problem — it is a "
                     "coverage problem in how many ways each question can be asked.")

    doc.add_heading("5. Known limits", level=1)
    for head, body in LIMITS:
        doc.add_heading(head, level=2)
        doc.add_paragraph(body)

    doc.save(path)


def main() -> int:
    os.makedirs("docs", exist_ok=True)
    md = build_markdown()
    with open(MD_OUT, "w", encoding="utf-8") as fh:
        fh.write(md)
    print(f"wrote {MD_OUT}  ({len(md.splitlines())} lines)")
    build_docx(DOCX_OUT)
    print(f"wrote {DOCX_OUT}  ({os.path.getsize(DOCX_OUT)/1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
