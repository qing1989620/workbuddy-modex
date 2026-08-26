"""`ommw doctor`: layered environment diagnostics.

Output is grouped and labeled PASS / WARN / FAIL. A WARN (e.g. missing
LibreOffice for visual DOCX QA) never fails CORE; it marks a capability as
DEGRADED. The capabilities established here are written to the project's
capabilities.json and constrain what the workflow may later claim.
"""
from __future__ import annotations

import dataclasses
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import __version__
from .config import Config, load_config
from .config import (
    detect_libreoffice,
    detect_pandoc,
    detect_texlive_bin,
    detect_workbuddy_skills_dir,
)
from .paths import core_root

STATUS_PASS = "PASS"
STATUS_WARN = "WARN"
STATUS_FAIL = "FAIL"


@dataclass
class Check:
    name: str
    status: str
    detail: str = ""
    capability: str | None = None  # if set, contributes to capabilities.json


@dataclass
class DoctorReport:
    checks: list[Check] = field(default_factory=list)

    def add(self, c: Check) -> None:
        self.checks.append(c)

    @property
    def overall(self) -> str:
        if any(c.status == STATUS_FAIL for c in self.checks if c.name.startswith("CORE") or c.name.startswith("PYTHON")):
            return STATUS_FAIL
        if any(c.status == STATUS_FAIL for c in self.checks):
            return STATUS_FAIL
        if any(c.status == STATUS_WARN for c in self.checks):
            return STATUS_WARN
        return STATUS_PASS

    def capabilities(self) -> dict[str, bool]:
        caps = {
            "python": True,
            "latex": False,
            "word": False,
            "visual_docx": False,
            "web": True,
            "sympy": False,
        }
        for c in self.checks:
            if c.capability and c.status == STATUS_PASS:
                caps[c.capability] = True
        return caps


def _run_ok(args: list[str], timeout: float = 8.0) -> tuple[bool, str]:
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return (r.returncode == 0, (r.stdout + r.stderr).strip()[:200])
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return (False, str(e))


def run() -> DoctorReport:
    cfg = load_config()
    rep = DoctorReport()

    # --- CORE ---
    rep.add(Check("CORE:repo-root", STATUS_PASS, str(core_root())))
    rep.add(Check("CORE:version", STATUS_PASS, f"ommw {__version__}"))
    missing = _missing_core_files()
    rep.add(Check(
        "CORE:legal-files",
        STATUS_FAIL if missing else STATUS_PASS,
        "missing: " + ", ".join(missing) if missing else "LICENSE/NOTICE/THIRD_PARTY present",
    ))

    # --- PYTHON ---
    rep.add(Check("CORE:python", STATUS_PASS, sys.version.replace("\n", " ")))
    pydantic_ok = _can_import("pydantic")
    typer_ok = _can_import("typer")
    docx_ok = _can_import("docx")
    rep.add(Check("PYTHON:pydantic", STATUS_PASS if pydantic_ok else STATUS_FAIL,
                  "ok" if pydantic_ok else "missing; run uv sync"))
    rep.add(Check("PYTHON:typer", STATUS_PASS if typer_ok else STATUS_FAIL,
                  "ok" if typer_ok else "missing"))
    rep.add(Check("PYTHON:python-docx", STATUS_PASS if docx_ok else STATUS_WARN,
                  "ok" if docx_ok else "Word structural QA unavailable", capability="word"))
    sympy_ok = _can_import("sympy")
    rep.add(Check("PYTHON:sympy", STATUS_PASS if sympy_ok else STATUS_WARN,
                  "ok" if sympy_ok else "not installed", capability="sympy"))

    # --- AGENT (WorkBuddy) ---
    wb = detect_workbuddy_skills_dir(cfg)
    if wb:
        rep.add(Check("AGENT:workbuddy-skills", STATUS_PASS, str(wb), capability="workbuddy"))
    else:
        rep.add(Check("AGENT:workbuddy-skills", STATUS_WARN, "not detected"))

    # --- LATEX ---
    texbin = detect_texlive_bin(cfg)
    if texbin:
        ok, det = _run_ok([str(texbin / ("latexmk.exe" if os.name == "nt" else "latexmk")), "--version"])
        rep.add(Check("LATEX:latexmk", STATUS_PASS if ok else STATUS_FAIL, det, capability="latex"))
        engine = cfg.latex.engine or "xelatex"
        exe = engine + (".exe" if os.name == "nt" else "")
        ok2, det2 = _run_ok([str(texbin / exe), "--version"])
        rep.add(Check(f"LATEX:{engine}", STATUS_PASS if ok2 else STATUS_WARN, det2))
    else:
        rep.add(Check("LATEX:texlive", STATUS_FAIL, "TeX Live not found", capability="latex"))

    # --- WORD ---
    pandoc = detect_pandoc(cfg)
    if pandoc:
        ok, det = _run_ok([pandoc, "--version"])
        rep.add(Check("WORD:pandoc", STATUS_PASS if ok else STATUS_FAIL, det, capability="word"))
    else:
        rep.add(Check("WORD:pandoc", STATUS_WARN, "not on PATH; Word mode needs pandoc", capability=None))

    lo = detect_libreoffice(cfg)
    if lo:
        ok, det = _run_ok([lo, "--version"])
        rep.add(Check("WORD:libreoffice", STATUS_PASS if ok else STATUS_WARN, det, capability="visual_docx"))
    else:
        rep.add(Check("WORD:libreoffice", STATUS_WARN, "not found; DOCX visual QA unavailable", capability=None))

    # --- NETWORK ---
    net_ok, _ = _run_ok([sys.executable, "-c", "import urllib.request,sys;urllib.request.urlopen('https://api.crossref.org/works?rows=0',timeout=5);print('ok')"], timeout=10)
    rep.add(Check("NETWORK:crossref", STATUS_PASS if net_ok else STATUS_WARN,
                  "reachable" if net_ok else "unreachable (offline citation mode only)"))

    # --- PROVIDERS ---
    mma = cfg.provider("mathmodelagent")
    if mma.enabled:
        if mma.path and Path(mma.path).exists():
            rep.add(Check("PROVIDERS:mathmodelagent", STATUS_PASS, f"enabled at {mma.path}"))
        else:
            rep.add(Check("PROVIDERS:mathmodelagent", STATUS_WARN, "enabled but path missing"))
    else:
        rep.add(Check("PROVIDERS:mathmodelagent", STATUS_PASS, "disabled (external, optional)"))
    ss = cfg.provider("scientific_skills")
    rep.add(Check("PROVIDERS:scientific-skills", STATUS_PASS if ss.enabled else STATUS_PASS,
                  "enabled" if ss.enabled else "disabled (fetch-on-demand)"))

    # --- v1.0: RESEARCH OS components (Rule 130) ---
    root = core_root()
    comp = root / "src" / "ommw" / "competition"
    rep.add(Check("RESEARCH:competition-kernel",
                  STATUS_PASS if (comp / "compliance.py").exists() else STATUS_FAIL,
                  "ok" if (comp / "compliance.py").exists() else "missing competition module"))
    exp = root / "src" / "ommw" / "experiment_lab"
    rep.add(Check("RESEARCH:experiment-lab",
                  STATUS_PASS if (exp / "planner.py").exists() else STATUS_FAIL,
                  "ok" if (exp / "planner.py").exists() else "missing experiment lab"))
    val = root / "src" / "ommw" / "validation"
    rep.add(Check("RESEARCH:result-validation",
                  STATUS_PASS if (val / "validator.py").exists() else STATUS_FAIL,
                  "ok" if (val / "validator.py").exists() else "missing validation engine"))
    ben = root / "src" / "ommw" / "benchmarks"
    rep.add(Check("RESEARCH:benchmarks",
                  STATUS_PASS if (ben / "negative_cases.py").exists() else STATUS_WARN,
                  "ok" if (ben / "negative_cases.py").exists() else "missing benchmark suite"))
    # Templates (competition profiles).
    tpl = root / "templates" / "competition"
    if tpl.exists() and any(tpl.glob("*/profile.toml")):
        rep.add(Check("TEMPLATES:competition", STATUS_PASS,
                      ", ".join(sorted(p.parent.name for p in tpl.glob("*/profile.toml")))))
    else:
        rep.add(Check("TEMPLATES:competition", STATUS_WARN, "no competition profiles"))
    # Schemas.
    sch = root / "schemas"
    n_sch = len(list(sch.glob("*.schema.json"))) if sch.exists() else 0
    rep.add(Check("SCHEMAS:json", STATUS_PASS if n_sch >= 4 else STATUS_WARN, f"{n_sch} json schemas"))
    return rep


def _missing_core_files() -> list[str]:
    root = core_root()
    expected = ["LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md", "pyproject.toml"]
    return [f for f in expected if not (root / f).exists()]


def _can_import(mod: str) -> bool:
    try:
        __import__(mod)
        return True
    except Exception:
        return False


def format_report(rep: DoctorReport) -> str:
    lines: list[str] = []
    width = max(len(c.name) for c in rep.checks) + 2
    by_group: dict[str, list[Check]] = {}
    for c in rep.checks:
        grp = c.name.split(":", 1)[0]
        by_group.setdefault(grp, []).append(c)
    for grp, checks in by_group.items():
        for c in checks:
            lines.append(f"{c.name:<{width}} {c.status:<5} {c.detail}")
    lines.append("")
    lines.append(f"OVERALL: {rep.overall}")
    return "\n".join(lines)
