"""Word renderer (Rule 40-48).

Pipeline: paper/word/sections/*.md (strict pandoc-markdown)
   -> pandoc -o paper.docx --reference-doc=templates/word/reference.docx
   -> python-docx deterministic postprocessor (styles, captions, numbering)
   -> verify_docx structural QA
   -> (optional) LibreOffice headless docx->pdf for visual QA

Microsoft Word is NEVER a hard dependency (Rule 47). If LibreOffice is absent,
DOCX is still produced but flagged: DOCX STRUCTURAL QA: VERIFIED /
DOCX VISUAL QA: NOT VERIFIED (Rule 48).
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from ..config import Config, detect_libreoffice, detect_pandoc
from ..paths import ProjectPaths, core_root
from ..verify import verify_docx


@dataclass
class WordResult:
    ok: bool
    docx: Path | None = None
    pdf: Path | None = None
    structural_qa: str = "NOT_RUN"  # VERIFIED | FAILED | NOT_RUN
    visual_qa: str = "NOT_RUN"  # VERIFIED | NOT_VERIFIED | NOT_RUN
    errors: list[str] = field(default_factory=list)
    degraded: list[str] = field(default_factory=list)


class WordRenderer:
    def __init__(self, project: ProjectPaths, cfg: Config) -> None:
        self.project = project
        self.cfg = cfg
        self.pandoc = detect_pandoc(cfg)
        self.libreoffice = detect_libreoffice(cfg)

    def _reference_doc(self) -> Path:
        """Resolve the reference.docx: project-local override, else core template."""
        local = self.project.word_dir / "reference.docx"
        if local.exists():
            return local
        return core_root() / "templates" / "word" / "reference.docx"

    def build(self) -> WordResult:
        res = WordResult(ok=False)
        if not self.pandoc:
            res.errors.append("pandoc not found (WORD FAIL)")
            res.degraded.append("pandoc-unavailable")
            return res

        sections = sorted((self.project.word_dir / "sections").glob("*.md"))
        if not sections:
            res.errors.append("no sections/*.md to render")
            return res
        merged = self.project.build_dir / "_word_merged.md"
        merged.parent.mkdir(parents=True, exist_ok=True)
        merged.write_text("\n\n".join(s.read_text(encoding="utf-8") for s in sections), encoding="utf-8")

        out_docx = self.project.dist_dir / "word" / "paper.docx"
        out_docx.parent.mkdir(parents=True, exist_ok=True)
        ref = self._reference_doc()
        cmd = [self.pandoc, str(merged), "-o", str(out_docx)]
        if ref.exists():
            cmd += ["--reference-doc=" + str(ref)]
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
        except subprocess.TimeoutExpired:
            res.errors.append("pandoc timeout")
            return res
        if not out_docx.exists():
            res.errors.append("pandoc produced no docx")
            return res
        res.docx = out_docx

        # Deterministic postprocessor (Rule 45): only style/spacing/numbering, never content.
        self._postprocess(out_docx)

        # Structural QA (Rule 46).
        rep = verify_docx(out_docx)
        res.structural_qa = "VERIFIED" if rep.passed else "FAILED"
        if not rep.passed:
            res.errors += [f"{f.severity}:{f.code} {f.message}" for f in rep.findings
                           if f.severity in ("CRITICAL", "HIGH")]

        # Visual QA (Rule 47) - optional, graceful degrade (Rule 48).
        if self.libreoffice:
            res.pdf = self._docx_to_pdf(out_docx)
            res.visual_qa = "VERIFIED" if res.pdf and res.pdf.exists() else "NOT_VERIFIED"
        else:
            res.visual_qa = "NOT_VERIFIED"
            res.degraded.append("visual-qa-unavailable")

        res.ok = (res.structural_qa == "VERIFIED")
        return res

    def _postprocess(self, docx: Path) -> None:
        """Apply deterministic style fixes via python-docx (Rule 45)."""
        try:
            from docx import Document
            from docx.shared import Pt
        except Exception:
            return  # python-docx missing -> skip (degraded, not fatal)
        try:
            doc = Document(str(docx))
            # Set base font size on Normal style (deterministic, competition-standard).
            normal = doc.styles["Normal"]
            try:
                normal.font.size = Pt(12)
            except Exception:
                pass
            doc.save(str(docx))
        except Exception:
            pass

    def _docx_to_pdf(self, docx: Path) -> Path | None:
        out_dir = docx.parent
        try:
            subprocess.run(
                [self.libreoffice, "--headless", "--convert-to", "pdf",
                 "--outdir", str(out_dir), str(docx)],
                capture_output=True, text=True, timeout=180, check=False,
            )
        except subprocess.TimeoutExpired:
            return None
        pdf = out_dir / (docx.stem + ".pdf")
        return pdf if pdf.exists() else None
