"""Paper Production Kernel -- content quality gates (v0.2).

Every gate returns the same ``VerifyReport`` used by the Research Core, so
findings flow into ``final-audit`` / ``judge`` automatically.

Gate inventory (upgrade spec §12-§52):
  - abstract_gate              ABSTRACT_GATE   (hard; missing = CRITICAL)
  - placeholder_gate           no section may ship as a stub
  - formula_sufficiency_gate   FORMULA_SUFFICIENCY_GATE
  - visual_evidence_gate       VISUAL_EVIDENCE_GATE
  - figure_text_coupling_gate  FIGURE_TEXT_COUPLING_GATE
  - experiment_sufficiency_gate EXPERIMENT_SUFFICIENCY_GATE
  - narrative_continuity_gate  NARRATIVE_CONTINUITY_GATE
  - symbol_consistency_gate    SYMBOL_CONSISTENCY_CHECK
  - result_consistency_gate    RESULT_CONSISTENCY_CHECK
  - latex_layout_gate          LATEX_LAYOUT_AUDIT (log-based)

Honesty rule: gates detect structure and linkage only. Mathematical
correctness, model appropriateness and discussion quality remain the job of
the independent reviewer agents -- no script pretends to "understand math".
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .. import atomic
from ..paths import ProjectPaths
from ..verify import VerifyReport
from .density import (
    RE_LABEL,
    RE_REF,
    analyze_latex_dir,
    classify_chapter,
    strip_comments,
)

# thresholds are conservative defaults; PaperContract may override per chapter
ABSTRACT_MIN_WORDS_ZH = 160      # CJK chars ~ a real competition abstract
ABSTRACT_MIN_WORDS_EN = 120
MODEL_CH_MIN_EQUATIONS = 2       # below this + >150 words -> warning
WORDS_PER_EQ_ANOMALY = 800


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# ABSTRACT GATE (spec §12) -- CRITICAL if missing/empty. Non-bypassable.
# ---------------------------------------------------------------------------

def abstract_gate(pp: ProjectPaths) -> VerifyReport:
    rep = VerifyReport()
    text = ""
    src = ""
    abs_file = pp.latex_dir / "sections" / "abstract.tex"
    main = _read(pp.latex_dir / "main.tex")
    latex_empty = True
    if abs_file.exists():
        text = strip_comments(_read(abs_file))
        src = str(abs_file)
        latex_empty = not text.strip()
    elif "\\begin{abstract}" in main:
        text = strip_comments(main)
        src = "main.tex"
        latex_empty = not text.strip()
    # Word fallback: the paper counts as having an abstract if ANY output
    # format carries one; a latex-side gap is still surfaced so dual-mode
    # drift is visible instead of silent.
    if latex_empty:
        wabs = pp.word_dir / "sections" / "abstract.md"
        if wabs.exists() and _read(wabs).strip():
            rep.add("MEDIUM", "ABSTRACT_NOT_IN_LATEX_SOURCES",
                    "abstract exists only in Word sources; a LaTeX build would "
                    "ship without it", str(abs_file))
            text, src, latex_empty = _read(wabs), str(wabs), False

    clean = text.strip()
    words = len(re.findall(r"[A-Za-z]+|[^\sA-Za-z]", re.sub(r"\\[a-zA-Z]+|\{|\}", " ", clean)))
    has_keywords = bool(re.search(r"keywords|关键词|關鍵詞", clean, re.IGNORECASE))
    numbers = re.findall(r"\d+(?:\.\d+)?%?", re.sub(r"\\[a-zA-Z]+\{?|[{}]", "", clean))

    if not clean or (words < 25 and len(numbers) == 0):
        rep.add("CRITICAL", "ABSTRACT_MISSING",
                "paper has no usable abstract (empty or placeholder)", src or str(abs_file))
        return rep
    min_words = ABSTRACT_MIN_WORDS_ZH if re.search(r"[\u4e00-\u9fff]", clean) else ABSTRACT_MIN_WORDS_EN
    if words < min_words * 0.6:
        rep.add("HIGH", "ABSTRACT_TOO_SHORT",
                f"abstract only ~{words} words (<60% of target {min_words})", src)
    if not numbers:
        rep.add("HIGH", "ABSTRACT_NO_QUANTITATIVE_RESULT",
                "abstract contains no quantitative result", src)
    if not has_keywords:
        rep.add("MEDIUM", "ABSTRACT_NO_KEYWORDS", "no Keywords block found", src)
    generic = [p for p in ("建立数学模型进行求解", "建立模型并求解") if p in clean]
    if generic:
        rep.add("MEDIUM", "ABSTRACT_GENERIC_MODEL_PHRASE",
                f'generic phrase without naming the actual model: "{generic[0]}"', src)
    return rep


# ---------------------------------------------------------------------------
# PLACEHOLDER GATE -- the demo4 failure: stub sections passed silently.
# ---------------------------------------------------------------------------

def placeholder_gate(pp: ProjectPaths) -> VerifyReport:
    rep = VerifyReport()
    analysis = analyze_latex_dir(pp.latex_dir)
    for s in analysis["sections"]:
        role = classify_chapter(s.file)
        if s.is_placeholder and role in ("model", "experiment", "abstract"):
            sev = "CRITICAL" if role in ("model", "abstract") else "HIGH"
            rep.add(sev, "PLACEHOLDER_SECTION",
                    f"{s.file} is still a stub (no real content)", f"latex:{s.file}")
        elif s.is_placeholder:
            rep.add("MEDIUM", "THIN_SECTION",
                    f"{s.file} looks like a stub (<25 effective words)", f"latex:{s.file}")
    totals = analysis["totals"]
    n_model = sum(1 for s in analysis["sections"] if classify_chapter(s.file) == "model")
    if n_model and totals["words"] < n_model * 250:
        rep.add("CRITICAL", "PAPER_CONTENT_INSUFFICIENT",
                f"whole paper only {totals['words']} effective words for {n_model} "
                "model chapters -- this cannot be a complete modeling paper", "latex")
    return rep


# ---------------------------------------------------------------------------
# FORMULA SUFFICIENCY GATE (spec §16-§18). Structural requirement + anomaly
# detection; JUSTIFIED_LOW_FORMULA_DENSITY honored via contract flag.
# ---------------------------------------------------------------------------

def formula_sufficiency_gate(pp: ProjectPaths, contract: dict | None = None) -> VerifyReport:
    rep = VerifyReport()
    contract = contract or {}
    justified = set((contract.get("justified_low_formula_density") or []))
    analysis = analyze_latex_dir(pp.latex_dir)
    for s in analysis["sections"]:
        if classify_chapter(s.file) != "model":
            continue
        ch = Path(s.file).stem
        req = int((contract.get("min_display_equations") or {}).get(ch, MODEL_CH_MIN_EQUATIONS))
        if ch in justified:
            continue  # audited exception; reviewer signed off
        if s.display_equations + s.inline_math == 0 and s.words > 100:
            rep.add("HIGH", "FORMULA_DENSITY_WARNING",
                    f"{ch}: algorithm/model described in prose only, zero math", f"latex:{s.file}")
        elif s.display_equations < req and s.words > 150:
            rep.add("HIGH", "FORMULA_DENSITY_WARNING",
                    f"{ch}: {s.display_equations} display equations "
                    f"(< required {req}) for {s.words} words of prose", f"latex:{s.file}")
        if s.effective_equations and s.words / max(s.effective_equations, 1) > WORDS_PER_EQ_ANOMALY:
            rep.add("MEDIUM", "FORMULA_DENSITY_ANOMALY",
                    f"{ch}: {s.words} words per equation -- wall-of-text risk", f"latex:{s.file}")
        if s.display_equations > 40 and s.words < 200:
            rep.add("MEDIUM", "FORMULA_INFLATION_SUSPECTED",
                    f"{ch}: equation dump with almost no prose (garbage-formula risk)",
                    f"latex:{s.file}")
    return rep


# ---------------------------------------------------------------------------
# VISUAL EVIDENCE GATE (spec §20-§23): every core question needs visual proof.
# ---------------------------------------------------------------------------

def visual_evidence_gate(pp: ProjectPaths, contract: dict | None = None) -> VerifyReport:
    rep = VerifyReport()
    contract = contract or {}
    justified = set(contract.get("justified_no_visual") or [])
    figures = atomic.read_jsonl(pp.figures_index)
    tables = atomic.read_jsonl(pp.tables_index)
    analysis = analyze_latex_dir(pp.latex_dir)
    model_files = [s for s in analysis["sections"] if classify_chapter(s.file) == "model"]
    if not model_files:
        rep.add("HIGH", "NO_MODEL_CHAPTERS", "no core question chapters detected", "latex")
        return rep
    for s in model_files:
        ch = Path(s.file).stem
        assets = s.figures + s.tikz + s.tables + s.algorithms
        reg_hits_fig = sum(1 for f in figures if ch[:4].lower() in str(f.get("section", "")).lower())
        if assets == 0 and reg_hits_fig == 0 and ch not in justified:
            rep.add("HIGH", "VISUAL_EVIDENCE_INSUFFICIENT",
                    f"{ch}: no figure/table/algorithm asset in a core question chapter",
                    f"latex:{s.file}")
    total_assets = analysis["totals"]["visual_assets"] + analysis["totals"]["tables"]
    if total_assets == 0:
        rep.add("CRITICAL", "PAPER_WITHOUT_VISUALS",
                "the entire paper contains zero figures/tables/tikz", "latex")
    return rep


# ---------------------------------------------------------------------------
# FIGURE-TEXT COUPLING GATE (spec §25-§26): a figure never referenced or never
# discussed equals no figure. Table coupling included.
# ---------------------------------------------------------------------------

def figure_text_coupling_gate(pp: ProjectPaths) -> VerifyReport:
    rep = VerifyReport()
    sections_dir = pp.latex_dir / "sections"
    files = sorted(sections_dir.glob("*.tex")) if sections_dir.exists() else []
    all_text = "\n".join(strip_comments(_read(f)) for f in files)
    fig_labels, tab_labels, eq_labels = set(), set(), set()
    for m in RE_LABEL.finditer(all_text):
        lbl = m.group(1)
        if lbl.startswith(("fig:", "figure:")):
            fig_labels.add(lbl)
        elif lbl.startswith(("tab:", "table:")):
            tab_labels.add(lbl)
        elif lbl.startswith(("eq:", "equation:", "chap:", "sec:")):
            eq_labels.add(lbl)
    refs = {m.group(2) for m in RE_REF.finditer(all_text)}
    for lbl in sorted(fig_labels):
        if lbl not in refs:
            rep.add("HIGH", "FIGURE_NOT_REFERENCED",
                    f"figure \\label{{{lbl}}} is never \\ref'd in the text", "latex")
    for lbl in sorted(tab_labels):
        if lbl not in refs:
            rep.add("HIGH", "TABLE_NOT_REFERENCED",
                    f"table \\label{{{lbl}}} is never \\ref'd in the text", "latex")
    # includegraphics without any caption nearby => uncaptioned asset
    for f in files:
        txt = strip_comments(_read(f))
        for para in re.split(r"\n\s*\n", txt):
            if "\\includegraphics" in para and "\\caption" not in para and "\\subcaption" not in para:
                rep.add("MEDIUM", "FIGURE_NO_CAPTION",
                        "includegraphics paragraph without caption", f"latex:{f.name}")
                break
    # registered-but-orphan figure files (registry says used, tex never includes)
    reg = atomic.read_jsonl(pp.figures_index)
    for rec in reg:
        out = str(rec.get("output", ""))
        name = Path(out).name if out else ""
        stem = Path(out).stem if out else ""
        if out and name and name not in all_text and stem not in all_text:
            rep.add("HIGH", "ORPHAN_FIGURE_ASSET",
                    f"registered figure {rec.get('figure_id')} ({name}) never appears in LaTeX sources",
                    "figures.jsonl")
    return rep


# ---------------------------------------------------------------------------
# EXPERIMENT SUFFICIENCY GATE (spec §27-§28): claims need experiment evidence.
# ---------------------------------------------------------------------------

_RE_IMPROVEMENT_CLAIM = re.compile(
    r"(提高|提升|降低|减少|improve[sd]?|reduce[sd]?|outperform[sd]?)[^。.\n]{0,30}?"
    r"(\d+(?:\.\d+)?)\s*\\?(?:%|％|个百分点)", re.IGNORECASE)


def experiment_sufficiency_gate(pp: ProjectPaths, contract: dict | None = None) -> VerifyReport:
    rep = VerifyReport()
    contract = contract or {}
    experiments = atomic.read_jsonl(pp.experiments_path)
    results = {r.get("result_id"): r for r in atomic.read_jsonl(pp.results_path)}
    claims = atomic.read_jsonl(pp.claims_path)

    needs_exp = contract.get("requires_experiments", True)
    if needs_exp and not experiments:
        # Only critical when the paper actually reports numbers/claims.
        if claims or atomic.read_jsonl(pp.results_path):
            rep.add("CRITICAL", "EXPERIMENT_EVIDENCE_MISSING",
                    "paper reports results/claims but experiments ledger is EMPTY "
                    "(fabricated-experiment risk)", "state/experiments.jsonl")
        else:
            rep.add("HIGH", "NO_EXPERIMENTS",
                    "no experiments recorded at all", "state/experiments.jsonl")

    # comparative claims must carry result evidence
    for c in claims:
        if c.get("type") in ("comparative", "causal") and not c.get("evidence_ids"):
            rep.add("HIGH", "UNSUPPORTED_CLAIM",
                    f"{c.get('claim_id')} makes a comparative claim with zero evidence ids",
                    c.get("claim_id", "?"))

    # percentage-improvement sentences must be anchored to a Result ID
    sections_dir = pp.latex_dir / "sections"
    files = sorted(sections_dir.glob("*.tex")) if sections_dir.exists() else []
    known_vals = {str(r.get("value", "")) for r in results.values()}
    for f in files:
        for line in strip_comments(_read(f)).splitlines():
            m = _RE_IMPROVEMENT_CLAIM.search(line)
            if not m:
                continue
            anchored = re.search(r"\b[R]-\d{3,4}\b", line)
            val_in_ledger = m.group(2) in known_vals or f"{m.group(2)}" in {
                v.rstrip("%") for v in known_vals}
            if not anchored and not val_in_ledger:
                rep.add("HIGH", "UNSUPPORTED_CLAIM",
                        f'improvement claim "{m.group(0)[:40]}..." has no Result-ID anchor '
                        "and the number is absent from the results ledger",
                        f"latex:{f.name}")
    return rep


# ---------------------------------------------------------------------------
# NARRATIVE CONTINUITY GATE (spec §30-§31): questions must connect.
# ---------------------------------------------------------------------------

def narrative_continuity_gate(pp: ProjectPaths) -> VerifyReport:
    rep = VerifyReport()
    nb = pp.state_dir / "paper-narrative.md"
    if not nb.exists():
        rep.add("MEDIUM", "NARRATIVE_BACKBONE_MISSING",
                "state/paper-narrative.md not written before drafting (story drift risk)",
                str(nb))
    dep_map_path = pp.state_dir / "question-dependency-map.yaml"
    dep_map = atomic.read_yaml(dep_map_path) if dep_map_path.exists() else None
    sections_dir = pp.latex_dir / "sections"
    files = sorted(sections_dir.glob("*.tex")) if sections_dir.exists() else []
    texts = {f.stem.lower(): strip_comments(_read(f)) for f in files}

    def _chapter_tokens(stem: str) -> set[str]:
        t = texts.get(stem.lower(), "")
        toks = set()
        for m in re.finditer(r"\b[RFCT]-\d{3,4}\b", t):
            toks.add(m.group(0))
        for m in RE_REF.finditer(t):
            toks.add(m.group(2))
        # a \\label DEFINED here also couples this chapter to every chapter
        # that references it (definition->use is the strongest evidence of
        # continuity; refs alone would miss the defining side).
        for m in RE_LABEL.finditer(t):
            toks.add(m.group(1))
        return toks

    stems = list(texts)
    if dep_map and isinstance(dep_map.get("dependencies"), list):
        for dep in dep_map["dependencies"]:
            frm, to = str(dep.get("from", "")), str(dep.get("to", ""))
            if not frm or not to:
                continue
            src_stem = next((s for s in stems if frm.lower() in s), None)
            dst_stem = next((s for s in stems if to.lower() in s), None)
            if not src_stem or not dst_stem:
                continue
            shared = _chapter_tokens(src_stem) & _chapter_tokens(dst_stem)
            explicit = re.search(rf"{frm[-1]}.{{0,80}}(?:结果|模型|结论)|Q{frm[-1]}", texts[dst_stem])
            if not shared and not explicit:
                rep.add("HIGH", "NARRATIVE_CONTINUITY_WARNING",
                        f"{to} declares dependency on {frm} but shares no result/ref/"
                        "symbol with it in the paper", f"latex:{dst_stem}")
    else:
        n_model = sum(1 for s in stems if classify_chapter(s + ".tex") == "model")
        if n_model >= 2:
            rep.add("LOW", "QUESTION_DEPENDENCY_MAP_MISSING",
                    "no state/question-dependency-map.yaml; cross-question coupling unchecked",
                    "state")
    return rep


# ---------------------------------------------------------------------------
# SYMBOL CONSISTENCY (spec §19)
# ---------------------------------------------------------------------------

def symbol_consistency_gate(pp: ProjectPaths) -> VerifyReport:
    rep = VerifyReport()
    notation = atomic.read_yaml(pp.notation_path) or {}
    entries = notation.get("entries", []) if isinstance(notation, dict) else []
    if len(entries) >= 6:
        pass  # enough symbols to warrant a notation table; presence checked below
    elif entries:
        rep.add("LOW", "SYMBOL_TABLE_SMALL",
                f"only {len(entries)} symbols registered; consider a full notation table "
                "if the paper defines more", "notation.yaml")
    all_tex = ""
    sections_dir = pp.latex_dir / "sections"
    if sections_dir.exists():
        all_tex = "\n".join(strip_comments(_read(f)) for f in sorted(sections_dir.glob("*.tex")))
    for e in entries:
        sym = str(e.get("symbol", "")).strip()
        if not sym:
            continue
        candidates = {sym, sym.replace("_", ""), sym.replace("_", "_{")} | {
            "\\" + sym} if not sym.startswith("\\") else {sym}
        hits = any(c and c in all_tex for c in candidates)
        if not hits:
            rep.add("LOW", "SYMBOL_UNUSED_IN_PAPER",
                    f"notation entry '{sym}' never appears in LaTeX body", "notation.yaml")
    # notation table present?
    has_table = bool(re.search(r"notation|符号说明", all_tex, re.IGNORECASE))
    if len(entries) >= 8 and not has_table:
        rep.add("MEDIUM", "NOTATION_TABLE_MISSING",
                f"{len(entries)} symbols defined but no symbols/notation section found", "latex")
    return rep


# ---------------------------------------------------------------------------
# RESULT CONSISTENCY (spec §51-§52): paper numbers must come from the ledger.
# ---------------------------------------------------------------------------

def result_consistency_gate(pp: ProjectPaths) -> VerifyReport:
    rep = VerifyReport()
    results = atomic.read_jsonl(pp.results_path)
    sections_dir = pp.latex_dir / "sections"
    files = sorted(sections_dir.glob("*.tex")) if sections_dir.exists() else []
    all_tex = "\n".join(strip_comments(_read(f)) for f in files)
    for r in results:
        rid = r.get("result_id", "?")
        val = str(r.get("value", "")).strip()
        if not val:
            continue
        # value should appear verbatim OR via its R-id anchor somewhere
        appears = (val in all_tex) or (rid in all_tex)
        if not appears:
            rep.add("LOW", "RESULT_NOT_IN_PAPER",
                    f"result {rid}={val} never surfaces in the LaTeX paper", "results.jsonl")
    # hand-typed long decimals already covered by research_verify orphan-number.
    return rep


# ---------------------------------------------------------------------------
# LATEX LAYOUT AUDIT (spec §46-§48): log-based deterministic checks.
# ---------------------------------------------------------------------------

def latex_layout_gate(pp: ProjectPaths) -> VerifyReport:
    rep = VerifyReport()
    log = pp.latex_dir / "output" / "main.log"
    pdf = pp.latex_dir / "output" / "main.pdf"
    if pdf.exists():
        pages = _pdf_page_count(pdf)
        if pages:
            rep.add("LOW", "PDF_PAGES", f"{pages} pages", str(pdf))
    else:
        rep.add("MEDIUM", "PDF_NOT_BUILT", "main.pdf not present; layout audit limited", str(pdf))
        return rep
    if not log.exists():
        rep.add("MEDIUM", "LOG_NOT_FOUND", "compile log missing; overfull checks skipped", str(log))
        return rep
    text = log.read_text(encoding="utf-8", errors="ignore")
    # NOTE: TeX logs print fractional points ("195.03pt"); parse as float --
    # an isdigit()-based conversion silently zeroed every fractional value.
    overfull = [float(v) for v in
                re.findall(r"Overfull \\hbox \((\d+(?:\.\d+)?)pt", text)]
    bad = [pt for pt in overfull if pt > 15]
    if bad:
        rep.add("HIGH", "LAYOUT_OVERFULL",
                f"{len(bad)} overfull hbox(es) >15pt (max {max(bad):.1f}pt): content sticks into margin",
                str(log))
    undef = len(re.findall(r"undefined references?|Reference .* undefined", text, re.IGNORECASE))
    if undef:
        rep.add("CRITICAL", "UNDEFINED_REFERENCES",
                f"{undef} undefined reference warning(s) in compile log", str(log))
    multi = len(re.findall(r"multiply defined", text, re.IGNORECASE))
    if multi:
        rep.add("HIGH", "MULTIPLY_DEFINED_LABELS",
                f"{multi} multiply-defined label warning(s)", str(log))
    miss_font = len(re.findall(r"Missing character", text))
    if miss_font:
        rep.add("HIGH", "MISSING_GLYPHS",
                f"{miss_font} 'Missing character' events -- glyphs silently dropped", str(log))
    underfull_v = len(re.findall(r"Underfull \\vbox", text))
    if underfull_v >= 5:
        rep.add("MEDIUM", "LAYOUT_UNDERFULL_VBOX",
                f"{underfull_v} underfull vbox warnings: stretched white gaps likely", str(log))
    return rep


def _pdf_page_count(pdf: Path) -> int:
    """Count pages in a PDF without external deps (best effort)."""
    data = pdf.read_bytes()
    n = data.count(b"/Type /Page") - data.count(b"/Type /Pages")
    if n <= 0:
        m = re.findall(rb"/Count (\d+)", data)
        n = max((int(x) for x in m), default=0)
    return n


# ---------------------------------------------------------------------------
# Aggregate runner
# ---------------------------------------------------------------------------

def run_all_paper_gates(pp: ProjectPaths, contract: dict | None = None) -> dict[str, VerifyReport]:
    """Run every content gate; returns {gate_name: report}."""
    return {
        "abstract": abstract_gate(pp),
        "placeholder": placeholder_gate(pp),
        "formula_sufficiency": formula_sufficiency_gate(pp, contract),
        "visual_evidence": visual_evidence_gate(pp, contract),
        "figure_text_coupling": figure_text_coupling_gate(pp),
        "experiment_sufficiency": experiment_sufficiency_gate(pp, contract),
        "narrative_continuity": narrative_continuity_gate(pp),
        "symbol_consistency": symbol_consistency_gate(pp),
        "result_consistency": result_consistency_gate(pp),
        "latex_layout": latex_layout_gate(pp),
    }


CRITICAL_CODES = {
    "ABSTRACT_MISSING", "PLACEHOLDER_SECTION", "PAPER_CONTENT_INSUFFICIENT",
    "PAPER_WITHOUT_VISUALS", "EXPERIMENT_EVIDENCE_MISSING",
    "UNDEFINED_REFERENCES", "MISSING_GLYPHS",
}


def gate_status(rep: VerifyReport) -> str:
    """PASS / WARN / FAIL from a VerifyReport."""
    if not rep.passed:
        return "FAIL"
    return "WARN" if rep.findings else "PASS"


def has_critical(reports: dict[str, VerifyReport]) -> list[tuple[str, str]]:
    """Return [(gate, code)] of critical failures (override any score, §62)."""
    out = []
    for gname, rep in reports.items():
        for f in rep.findings:
            if f.severity == "CRITICAL" or f.code in CRITICAL_CODES:
                out.append((gname, f.code))
    return out


def write_audit_bundle(pp: ProjectPaths, reports: dict[str, VerifyReport],
                       density: dict, outdir: Path) -> Path:
    """Persist audits/chapter-density-report.json + audits/paper-gate-report.json."""
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "chapter-density-report.json").write_text(
        json.dumps(density, ensure_ascii=False, indent=2), encoding="utf-8")
    gate_dump = {
        g: {"status": gate_status(r),
            "critical": has_critical({g: r}),
            "findings": [dict(severity=f.severity, code=f.code,
                              message=f.message, location=f.location)
                         for f in r.findings]}
        for g, r in reports.items()
    }
    (outdir / "paper-gate-report.json").write_text(
        json.dumps(gate_dump, ensure_ascii=False, indent=2), encoding="utf-8")
    return outdir
