"""Runtime adapters. Each adapter installs a THIN wrapper that points at the
repo's master skill, so business logic never has two drifting copies (Rule 17)."""
from __future__ import annotations

from .workbuddy import WorkbuddyAdapter

__all__ = ["WorkbuddyAdapter"]
