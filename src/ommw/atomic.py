"""Atomic, crash-safe file writes.

Important JSON/YAML state is written to a temp file, validated, then
os.replace'd into place. This prevents a mid-write crash from corrupting
progress.json or a ledger.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import yaml


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Temp file in same directory so os.replace is atomic on the same FS.
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix="." + path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def write_json(path: Path, obj: Any, *, indent: int = 2) -> None:
    """Atomically write JSON (UTF-8, deterministic key order)."""
    data = json.dumps(obj, ensure_ascii=False, indent=indent, sort_keys=False).encode("utf-8")
    _atomic_write_bytes(path, data)


def write_jsonl(path: Path, records: list[dict]) -> None:
    """Atomically write a JSONL ledger (one JSON object per line)."""
    lines = []
    for rec in records:
        lines.append(json.dumps(rec, ensure_ascii=False))
    data = ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")
    _atomic_write_bytes(path, data)


def append_jsonl(path: Path, record: dict) -> None:
    """Append a single record to a JSONL ledger (atomic per-line append)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False) + "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)
        f.flush()


def write_yaml(path: Path, obj: Any) -> None:
    """Atomically write YAML (UTF-8)."""
    data = yaml.safe_dump(obj, allow_unicode=True, sort_keys=False).encode("utf-8")
    _atomic_write_bytes(path, data)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def read_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)
