"""Experiment Planner (Rule 35).

Selects the NECESSARY experiment portfolio for a problem — not everything.
Simple problems: baseline + 1-2 strong candidates. Complex problems: more.
The portfolio is derived from problem characteristics.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from ..schemas.experiment_lab import ExperimentPlan, ExperimentStatus


@dataclass
class ProblemCharacteristics:
    problem_type: str = "generic"  # prediction|classification|optimization|evaluation|network|simulation|ode|timeseries|spatial|multiobjective
    has_data: bool = False
    stochastic: bool = False  # model family uses randomness
    time_series: bool = False
    has_baseline: bool = True
    complexity: str = "medium"  # low | medium | high
    time_budget_minutes: int | None = None
    n_models: int = 2


def plan_experiments(chars: ProblemCharacteristics, *, base_id: int = 1) -> list[ExperimentPlan]:
    """Return the experiment portfolio for the problem.

    Always includes: baseline + candidate comparison.
    Conditionally includes: eda (if data), multi-seed (if stochastic),
    sensitivity/robustness (if medium/high complexity), time-split validation
    (if time series), scenario (if optimization/simulation).
    """
    plans: list[ExperimentPlan] = []
    i = base_id

    def add(model: str, family: str, metric: str, split: str = "", extra: dict | None = None) -> None:
        nonlocal i
        plans.append(ExperimentPlan(
            experiment_id=f"E-{i:03d}", research_question=chars.problem_type,
            model=model, metric=metric, split=split,
            baseline="yes" if family == "baseline" else "",
            family=family, seed=42 if chars.stochastic else None,
            parameters=extra or {}, status=ExperimentStatus.planned,
            success_condition="metric recorded and validated",
        ))
        i += 1

    # EDA first when data exists.
    if chars.has_data:
        add("eda-profiling", "eda", "missing/outlier summary")

    # Baseline is mandatory (Rule 28).
    add("baseline", "baseline", "primary-metric")

    # Candidate comparisons (n_models - 1 additional candidates).
    for k in range(max(0, chars.n_models - 1)):
        add(f"candidate-{k + 1}", "comparison", "primary-metric")

    # Stochastic -> multi-seed robustness.
    if chars.stochastic:
        add("multi-seed", "robustness", "mean/std/best/worst", extra={"seeds": 5})

    # Medium/high complexity -> sensitivity + robustness.
    if chars.complexity in ("medium", "high"):
        add("parameter-sensitivity", "sensitivity", "metric-vs-param")
        add("robustness", "robustness", "perturbation/noise")

    # Time series -> time-based split validation (Rule 64).
    if chars.time_series:
        add("time-split-validation", "validation", "primary-metric", split="time-based")

    # Optimization/simulation -> scenario analysis.
    if chars.problem_type in ("optimization", "simulation", "multiobjective"):
        add("scenario-analysis", "scenario", "objective-scenarios")

    return plans


def portfolio_for_problem(problem_type: str, *, n_models: int = 2,
                          has_data: bool = True, stochastic: bool = False,
                          time_series: bool = False, complexity: str = "medium") -> list[ExperimentPlan]:
    """Convenience: build characteristics from a problem type keyword."""
    chars = ProblemCharacteristics(
        problem_type=problem_type, has_data=has_data, stochastic=stochastic,
        time_series=time_series, complexity=complexity, n_models=n_models,
    )
    return plan_experiments(chars)


def estimate_runtime_ok(plans: list[ExperimentPlan], time_budget_minutes: int | None) -> tuple[bool, str]:
    """Deadline-aware check (Rule 121-122): flag if the portfolio is too heavy."""
    if not time_budget_minutes:
        return True, "no deadline"
    # Rough: each experiment ~ 5-15 min of wall time in a competition setting.
    est = len(plans) * 10
    if est > time_budget_minutes * 0.5:
        return False, (f"portfolio estimated ~{est} min exceeds half of budget "
                       f"{time_budget_minutes} min; trim to baseline+comparison+robustness")
    return True, f"~{est} min estimated, within budget"
