"""LaTeX renderer (Rule 36-39).

Per-chapter incremental build (Rule 37): the orchestrator writes one section at
a time; here we provide a deterministic compile that:
  - builds a temporary PATH from the detected TeX Live bin (NO global mutation),
  - runs latexmk with the configured engine (xelatex default for CJK),
  - captures the .log, parses fatal errors / undefined refs / undefined citations,
  - returns a structured LatexResult.

Compile-or-not-done: a paper is not "PDF ready" unless compile succeeds with
zero undefined-citation warnings (Rule 109).
"""
from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from ..config import Config, detect_texlive_bin
from ..paths import ProjectPaths


@dataclass
class LatexResult:
    ok: bool
    pdf: Path | None = None
    log: Path | None = None
    errors: list[str] = field(default_factory=list)
    undefined_refs: list[str] = field(default_factory=list)
    undefined_citations: list[str] = field(default_factory=list)
    degraded: list[str] = field(default_factory=list)


class LatexRenderer:
    def __init__(self, project: ProjectPaths, cfg: Config) -> None:
        self.project = project
        self.cfg = cfg
        self.texbin = detect_texlive_bin(cfg)

    def _env(self) -> dict[str, str] | None:
        if not self.texbin:
            return None
        env = os.environ.copy()
        # Prepend tex bin to PATH for this subprocess only (Rule 39).
        sep = ";" if os.name == "nt" else ":"
        env["PATH"] = str(self.texbin) + sep + env.get("PATH", "")
        return env

    def compile_main(self) -> LatexResult:
        """Compile paper/latex/main.tex -> output/main.pdf."""
        main = self.project.latex_dir / "main.tex"
        out = self.project.latex_dir / "output"
        out.mkdir(parents=True, exist_ok=True)
        res = LatexResult(ok=False)
        if not main.exists():
            res.errors.append("main.tex not found")
            return res
        env = self._env()
        if env is None:
            res.errors.append("TeX Live not found (LATEX FAIL)")
            res.degraded.append("latex-unavailable")
            return res

        engine = self.cfg.latex.engine or "xelatex"
        latexmk = str(self.texbin / ("latexmk.exe" if os.name == "nt" else "latexmk"))
        cmd = [
            latexmk,
            "-" + engine,
            "-interaction=nonstopmode",
            "-file-line-error",
            "-outdir=" + str(out),
            str(main),
        ]
        try:
            proc = subprocess.run(cmd, cwd=str(self.project.latex_dir), env=env,
                                  capture_output=True, text=True, errors="replace",
                                  timeout=300)
        except subprocess.TimeoutExpired:
            res.errors.append("compile timeout (300s)")
            return res

        log = out / "main.log"
        res.log = log if log.exists() else None
        pdf = out / "main.pdf"
        res.pdf = pdf if pdf.exists() else None

        # Parse log for errors / undefined references (Rule 109).
        log_text = log.read_text(encoding="utf-8", errors="ignore") if log.exists() else proc.stdout
        res.errors = re.findall(r"^(?:./.+?\.\w+:)?\s*! .*?$", log_text, re.MULTILINE)[:50]
        res.undefined_refs = sorted(set(re.findall(r"LaTeX Warning: Reference `([^']+)'", log_text)))
        res.undefined_citations = sorted(set(re.findall(r"Citation `([^']+)' undefined", log_text)))
        res.ok = (res.pdf is not None and not res.errors and not res.undefined_citations)
        return res

    def compile_section(self, name: str) -> LatexResult:
        """Incremental: compile a single section via a temporary main that
        \\input{}s only it. Used by the chapter lifecycle gate (Rule 37)."""
        sec = self.project.latex_dir / "sections" / f"{name}.tex"
        if not sec.exists():
            return LatexResult(ok=False, errors=[f"section {name} not found"])
        tmp_main = self.project.build_dir / f"_section_{name}.tex"
        tmp_main.parent.mkdir(parents=True, exist_ok=True)
        tmp_main.write_text(
            r"\documentclass{article}" "\n"
            r"\begin{document}" "\n"
            rf"\input{{sections/{name}}}" "\n"
            r"\end{document}" "\n",
            encoding="utf-8",
        )
        # Reuse compile_main by pointing a temp project; simpler: just compile tmp.
        env = self._env()
        if env is None:
            return LatexResult(ok=False, errors=["TeX Live not found"], degraded=["latex-unavailable"])
        engine = self.cfg.latex.engine or "xelatex"
        latexmk = str(self.texbin / ("latexmk.exe" if os.name == "nt" else "latexmk"))
        out = self.project.build_dir / f"_section_{name}"
        cmd = [latexmk, "-" + engine, "-interaction=nonstopmode",
               "-outdir=" + str(out), str(tmp_main)]
        try:
            subprocess.run(cmd, cwd=str(self.project.latex_dir), env=env,
                           capture_output=True, text=True, errors="replace",
                           timeout=120)
        except subprocess.TimeoutExpired:
            return LatexResult(ok=False, errors=["section compile timeout"])
        pdf = out / f"_section_{name}.pdf"
        ok = pdf.exists()
        return LatexResult(ok=ok, pdf=pdf if ok else None)
