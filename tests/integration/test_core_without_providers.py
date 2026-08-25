"""Integration: OMMW core works without any external provider (Rule 172)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_core_works_without_mathmodelagent(tmp_path: Path) -> None:
    """Doctor + smoke must succeed with MathModelAgent disabled/absent."""
    r = subprocess.run(
        [sys.executable, "-m", "ommw", "smoke-test", "--dest", str(tmp_path / "s"), "--mode", "dual"],
        capture_output=True, text=True, timeout=180,
        env=__import__("os").environ.copy(),
    )
    assert r.returncode == 0, r.stderr
    assert "OVERALL: PASS" in r.stdout


def test_provider_list(tmp_path: Path) -> None:
    r = subprocess.run(
        [sys.executable, "-m", "ommw", "provider", "list"],
        capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0
    assert "mathmodelagent" in r.stdout
    assert "EXTERNAL_OPTIONAL" in r.stdout
