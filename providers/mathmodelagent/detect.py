"""Detect a local MathModelAgent installation.

Performs NO network access and imports NO upstream code. It only checks for
marker files at a configured path. Used by `ommw doctor`.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Detection:
    found: bool
    path: str = ""
    markers_seen: list[str] = None  # type: ignore[assignment]


def detect(path: str) -> Detection:
    if not path:
        return Detection(found=False)
    p = Path(path).expanduser()
    if not p.exists():
        return Detection(found=False)
    markers = [m for m in ("README.md", "main.py", "agents", "src") if (p / m).exists()]
    return Detection(found=bool(markers), path=str(p), markers_seen=markers)
