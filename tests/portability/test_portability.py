"""Portability tests (Rule 110-111).

Scans the committed core for machine-specific absolute paths and verifies the
smoke pipeline runs inside a Chinese + spaces path.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

# Patterns that indicate non-portable machine paths leaked into core source.
# (Excluded: docs/examples that quote a path as a demonstrative example.)
ABS_PATH_RE = re.compile(
    r"(?m)"
    r"(?:[A-Za-z]:\\(?:Users|Program Files|Windows|ProgramData)\\)"
    r"|(?:/(?:Users|home)/[A-Za-z0-9._-]+/)"
)
CORE_DIRS = ("src", "skills", "templates", "providers", "schemas", "adapters", "renderers")


def _core_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_no_absolute_machine_paths_in_core() -> None:
    root = _core_root()
    offenders: list[str] = []
    for d in CORE_DIRS:
        for p in (root / d).rglob("*"):
            if p.is_file() and p.suffix in (".py", ".toml", ".yaml", ".yml", ".tex", ".md"):
                try:
                    text = p.read_text(encoding="utf-8")
                except Exception:
                    continue
                # Skip explicit example/doc mentions of config (texlive_root example).
                for line in text.splitlines():
                    if "config.example" in str(p) or "TEXLIVE_HOME=" in line or line.strip().startswith("#"):
                        continue
                    if ABS_PATH_RE.search(line):
                        offenders.append(f"{p.relative_to(root)}: {line.strip()[:120]}")
    assert not offenders, "non-portable absolute paths leaked into core:\n" + "\n".join(offenders[:20])


def test_smoke_runs_in_chinese_spaces_path(tmp_path: Path) -> None:
    """Rule 111: smoke must pass inside a path with spaces and CJK chars."""
    root = tmp_path / "测试 工作区" / "数学建模 smoke"
    root.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        [sys.executable, "-m", "ommw", "smoke-test", "--dest", str(root), "--mode", "dual"],
        capture_output=True, text=True, timeout=180,
    )
    assert r.returncode == 0, f"smoke failed in CJK path:\n{r.stdout}\n{r.stderr}"


def test_doctor_runs() -> None:
    r = subprocess.run([sys.executable, "-m", "ommw", "doctor"], capture_output=True, text=True, timeout=60)
    # doctor may return non-zero on FAIL, but must run and print OVERALL.
    assert "OVERALL" in r.stdout + r.stderr
