"""Benchmarks (Layer 10): internal capability checks, NOT award predictors."""
from __future__ import annotations

from .negative_cases import NEGATIVE_CASES
from .runner import BenchmarkCase, BenchmarkReport, run_benchmark
from .smoke_projects import all_smoke_projects

__all__ = [
    "BenchmarkCase",
    "BenchmarkReport",
    "NEGATIVE_CASES",
    "all_smoke_projects",
    "run_benchmark",
]


def full_suite() -> list[BenchmarkCase]:
    return NEGATIVE_CASES + all_smoke_projects()
