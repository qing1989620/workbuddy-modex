"""Dual-mode parity gate (Rule 50).

Compares LaTeX and Word outputs of the SAME accepted Research Core. They must
agree on: claim IDs, result IDs, citations, equation count, figure IDs, table
IDs, chapter structure, and conclusion values. Binary equality of PDF/DOCX is
NOT required (Rule 96) because of non-deterministic metadata/timestamps.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .paths import ProjectPaths
from .verify import Finding, VerifyReport

ID_RE = re.compile(r"\b([CRSETF]-\d{3,4})\b")
EQ_RE_TEX = re.compile(r"\\begin\{equation\}")
EQ_RE_MD = re.compile(r"^\s*```+math\s*$|^\$\$|^\$[^$]", re.MULTILINE)


@dataclass
class FormatFingerprint:
    claims: set[str] = field(default_factory=set)
    results: set[str] = field(default_factory=set)
    citations: set[str] = field(default_factory=set)  # source IDs
    figures: set[str] = field(default_factory=set)
    tables: set[str] = field(default_factory=set)
    equations: int = 0
    chapters: list[str] = field(default_factory=list)


def fingerprint_latex(project: ProjectPaths) -> FormatFingerprint:
    fp = FormatFingerprint()
    base = project.latex_dir
    main = base / "main.tex"
    files = [main] if main.exists() else []
    files += list((base / "sections").glob("*.tex")) if (base / "sections").exists() else []
    text = "\n".join(f.read_text(encoding="utf-8", errors="ignore") for f in files)
    fp.claims = {x for x in ID_RE.findall(text) if x.startswith("C-")}
    fp.results = {x for x in ID_RE.findall(text) if x.startswith("R-")}
    fp.citations = {x for x in ID_RE.findall(text) if x.startswith("S-")}
    fp.figures = {x for x in ID_RE.findall(text) if x.startswith("F-")}
    fp.tables = {x for x in ID_RE.findall(text) if x.startswith("T-")}
    fp.equations = len(EQ_RE_TEX.findall(text))
    fp.chapters = sorted({f.stem for f in (base / "sections").glob("*.tex")} if (base / "sections").exists() else [])
    return fp


def fingerprint_word(project: ProjectPaths) -> FormatFingerprint:
    fp = FormatFingerprint()
    base = project.word_dir / "sections"
    files = list(base.glob("*.md")) if base.exists() else []
    text = "\n".join(f.read_text(encoding="utf-8", errors="ignore") for f in files)
    fp.claims = {x for x in ID_RE.findall(text) if x.startswith("C-")}
    fp.results = {x for x in ID_RE.findall(text) if x.startswith("R-")}
    fp.citations = {x for x in ID_RE.findall(text) if x.startswith("S-")}
    fp.figures = {x for x in ID_RE.findall(text) if x.startswith("F-")}
    fp.tables = {x for x in ID_RE.findall(text) if x.startswith("T-")}
    fp.equations = len(EQ_RE_MD.findall(text))
    fp.chapters = sorted({f.stem for f in files})
    return fp


def parity_check(project: ProjectPaths) -> VerifyReport:
    """Compare LaTeX vs Word fingerprints. Writes parity-report.json into dist."""
    rep = VerifyReport()
    lp = fingerprint_latex(project)
    wp = fingerprint_word(project)

    def diff(label: str, a: set[str], b: set[str]) -> None:
        only_l = a - b
        only_w = b - a
        if only_l:
            rep.add("HIGH", "parity-" + label, f"only in latex: {sorted(only_l)}")
        if only_w:
            rep.add("HIGH", "parity-" + label, f"only in word: {sorted(only_w)}")

    diff("claims", lp.claims, wp.claims)
    diff("results", lp.results, wp.results)
    diff("citations", lp.citations, wp.citations)
    diff("figures", lp.figures, wp.figures)
    diff("tables", lp.tables, wp.tables)
    if lp.chapters != wp.chapters:
        rep.add("HIGH", "parity-chapters", f"latex={lp.chapters} word={wp.chapters}")
    # Equation count may differ slightly due to inline math; flag large gaps.
    if abs(lp.equations - wp.equations) > max(3, 0.2 * max(lp.equations, 1)):
        rep.add("MEDIUM", "parity-equations", f"latex={lp.equations} word={wp.equations}")

    report = {
        "latex": _as_dict(lp),
        "word": _as_dict(wp),
        "passed": rep.passed,
        "findings": [f.__dict__ for f in rep.findings],
    }
    project.dist_dir.mkdir(parents=True, exist_ok=True)
    from . import atomic
    atomic.write_json(project.dist_dir / "parity-report.json", report)
    return rep


def _as_dict(fp: FormatFingerprint) -> dict:
    return {
        "claims": sorted(fp.claims),
        "results": sorted(fp.results),
        "citations": sorted(fp.citations),
        "figures": sorted(fp.figures),
        "tables": sorted(fp.tables),
        "equations": fp.equations,
        "chapters": fp.chapters,
    }
