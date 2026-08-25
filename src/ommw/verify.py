"""Verification gates.

Three families:
  - research_verify: linkage integrity of the Research Core (claim->result->source).
  - verify_docx: structural QA of a generated DOCX.
  - hallucination checks: numeric and citation anti-hallucination.

Renderer verification (LaTeX compile success, etc.) lives in render/.
"""
from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from . import atomic
from .paths import ProjectPaths
from .schemas import ClaimStatus, SourceVerification


@dataclass
class Finding:
    severity: str  # CRITICAL | HIGH | MEDIUM | LOW
    code: str
    message: str
    location: str = ""


@dataclass
class VerifyReport:
    findings: list[Finding] = field(default_factory=list)
    passed: bool = True

    def add(self, sev: str, code: str, msg: str, loc: str = "") -> None:
        self.findings.append(Finding(sev, code, msg, loc))
        if sev in ("CRITICAL", "HIGH"):
            self.passed = False


# ---------------------------------------------------------------------------
# Research Core linkage verification
# ---------------------------------------------------------------------------

CLAIM_RE = re.compile(r"\b([CRSET]-\d{3,4})\b")


def research_verify(project: ProjectPaths) -> VerifyReport:
    """Cross-check claim/result/source/figure/table ledgers for broken links."""
    rep = VerifyReport()
    results = {r["result_id"]: r for r in atomic.read_jsonl(project.results_path)}
    sources = {s["source_id"]: s for s in atomic.read_jsonl(project.sources_path)}
    claims = atomic.read_jsonl(project.claims_path)

    result_ids = set(results)
    source_ids = set(sources)

    for c in claims:
        cid = c.get("claim_id", "?")
        # Rule 68: no fabricated numbers -> every evidence_id must resolve to a Result.
        for eid in c.get("evidence_ids", []):
            if eid not in result_ids:
                rep.add("CRITICAL", "unresolved-result",
                        f"claim {cid} cites missing result {eid}", cid)
        # Rule 69: no fabricated citations -> every source_id must resolve.
        for sid in c.get("source_ids", []):
            if sid not in source_ids:
                rep.add("CRITICAL", "unresolved-source",
                        f"claim {cid} cites missing source {sid}", cid)
            else:
                src = sources[sid]
                # Rule 70: citation must actually support the claim (content_verified).
                if src.get("verification") == SourceVerification.unverified.value:
                    rep.add("HIGH", "unverified-citation",
                            f"source {sid} used by {cid} is UNVERIFIED", sid)
        # Rule 23: only SUPPORTED/VERIFIED claims may be formal conclusions.
        status = c.get("status", ClaimStatus.proposed.value)
        if c.get("type") == "conclusion" and status not in (
            ClaimStatus.supported.value, ClaimStatus.verified.value
        ):
            rep.add("HIGH", "unsupported-conclusion",
                    f"conclusion claim {cid} has status {status}", cid)

    # Rule 68: scan paper source text for inline numbers lacking a Result ID nearby.
    for kind, base in (("latex", project.latex_dir / "sections"), ("word", project.word_dir / "sections")):
        if not base.exists():
            continue
        for f in base.glob("*.tex" if kind == "latex" else "*.md"):
            scan_for_orphan_numbers(f, results, rep, kind)

    return rep


def scan_for_orphan_numbers(path: Path, results: dict, rep: VerifyReport, kind: str) -> None:
    """Heuristic: numbers in prose that look like results but carry no Result ID.

    This is a soft check (MEDIUM); it surfaces suspicious hand-typed values for
    human review rather than hard-failing on every decimal. A line is flagged
    when it contains a decimal with 3+ fractional digits (e.g. 0.9731428571,
    12.3456) and no R-/C-/S- anchor on that same line.
    """
    text = path.read_text(encoding="utf-8", errors="ignore")
    decimal_re = re.compile(r"\d+\.\d{3,}")
    for line in text.splitlines():
        if not decimal_re.search(line):
            continue
        low = line.lower()
        # An anchor token on the same line makes the number traceable.
        if re.search(r"\b[RCSTF]-\d{3,4}\b", line) or "result" in low:
            continue
        rep.add("MEDIUM", "orphan-number",
                "numeric value with no Result ID on same line", f"{kind}:{path.name}")
        return  # one per file is enough signal


# ---------------------------------------------------------------------------
# DOCX structural QA (Rule 46)
# ---------------------------------------------------------------------------

def verify_docx(path: Path) -> VerifyReport:
    """Structural integrity checks on a .docx (OpenXML zip)."""
    rep = VerifyReport()
    if not path.exists():
        rep.add("CRITICAL", "missing-docx", f"file not found: {path}")
        return rep
    if not zipfile.is_zipfile(path):
        rep.add("CRITICAL", "not-zip", f"not a valid docx (zip): {path}")
        return rep
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            required = ["[Content_Types].xml", "word/document.xml"]
            for r in required:
                if r not in names:
                    rep.add("HIGH", "missing-part", f"docx missing {r}", str(path))
            doc = z.read("word/document.xml").decode("utf-8", errors="ignore") if "word/document.xml" in names else ""
            # Count structural elements (headings = w:pStyle val=Heading*).
            n_h = len(re.findall(r'w:pStyle w:val="Heading', doc))
            n_tbl = doc.count("<w:tbl>")
            n_img = doc.count("<w:drawing>") + doc.count("<w:pict>")
            n_ref = doc.count("REF")
            # Placeholder leak detection (Rule 48).
            for ph in ("TODO", "FIXME", "PLACEHOLDER", "<<", ">>", "R-???"):
                if ph in doc:
                    rep.add("HIGH", "placeholder-leak", f"unresolved token {ph} in docx", str(path))
            if n_h == 0:
                rep.add("MEDIUM", "no-headings", "no heading styles detected", str(path))
            rep.add("LOW", "docx-counts",
                    f"headings~{n_h} tables~{n_tbl} images~{n_img} refs~{n_ref}", str(path))
    except Exception as e:  # pragma: no cover
        rep.add("CRITICAL", "docx-read-error", str(e), str(path))
    return rep
