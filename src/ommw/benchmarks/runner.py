"""Benchmark framework (Rule 101-106).

Benchmarks are NOT award predictors. They check the system's internal
capabilities: problem decomposition, data audit, model routing, baseline
selection, experiment planning, result validation, citation accuracy,
competition compliance, and negative-case detection.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class BenchmarkCase:
    case_id: str
    family: str  # forecasting | optimization | evaluation | network | simulation | classification | ode | multiobjective | spatial | mixed
    description: str
    run: Callable[[], dict]  # returns {"passed": bool, "detail": str}
    expected: str = "pass"


@dataclass
class BenchmarkResult:
    case_id: str
    family: str
    passed: bool
    detail: str = ""
    duration_s: float = 0.0


@dataclass
class BenchmarkReport:
    results: list[BenchmarkResult] = field(default_factory=list)

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def overall(self) -> bool:
        return bool(self.results) and all(r.passed for r in self.results)

    def table(self) -> str:
        lines = ["| case | family | status | detail |", "|---|---|---|---|"]
        for r in self.results:
            lines.append(f"| {r.case_id} | {r.family} | {'PASS' if r.passed else 'FAIL'} | {r.detail[:80]} |")
        lines.append(f"\nTOTAL: {self.passed_count}/{len(self.results)} passed")
        lines.append(f"OVERALL: {'PASS' if self.overall else 'FAIL'}")
        return "\n".join(lines)


def run_benchmark(cases: list[BenchmarkCase]) -> BenchmarkReport:
    rep = BenchmarkReport()
    for case in cases:
        t0 = time.time()
        try:
            out = case.run()
            passed = bool(out.get("passed"))
            detail = str(out.get("detail", ""))
        except Exception as e:
            passed = False
            detail = f"exception: {type(e).__name__}: {e}"
        rep.results.append(BenchmarkResult(
            case_id=case.case_id, family=case.family, passed=passed,
            detail=detail, duration_s=round(time.time() - t0, 3),
        ))
    return rep
