"""End-to-end smoke via the CLI."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_smoke_dual(tmp_path: Path) -> None:
    r = subprocess.run(
        [sys.executable, "-m", "ommw", "smoke-test", "--dest", str(tmp_path / "s"), "--mode", "dual"],
        capture_output=True, text=True, timeout=180,
    )
    assert r.returncode == 0, f"smoke failed:\n{r.stdout}\n{r.stderr}"
    assert "OVERALL: PASS" in r.stdout
    assert "negative-case detection: ALL CAUGHT" in r.stdout


def test_init_and_status(tmp_path: Path) -> None:
    proj = tmp_path / "myproj"
    r = subprocess.run(
        [sys.executable, "-m", "ommw", "init", str(proj), "--mode", "latex"],
        capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 0, r.stderr
    assert (proj / "state" / "project.yaml").exists()
    r2 = subprocess.run(
        [sys.executable, "-m", "ommw", "status", "--project", str(proj)],
        capture_output=True, text=True, timeout=60,
    )
    assert r2.returncode == 0, r2.stderr
    assert "RECEIVED" in r2.stdout or "current_stage" in r2.stdout
