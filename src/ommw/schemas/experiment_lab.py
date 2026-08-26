"""Experiment Lab schemas (Rule 33-36).

Every experiment is PLANNED before running (experiment.yaml), then executed,
and the executed artifacts (result.json / metrics.csv / predictions.csv) are the
source of truth — never chat text. All legal runs are kept; cherry-picking is
forbidden (Rule 36).
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ExperimentStatus(str, Enum):
    planned = "PLANNED"
    running = "RUNNING"
    completed = "COMPLETED"
    failed = "FAILED"
    stale = "STALE"  # upstream data/code changed
    excluded = "EXCLUDED"  # excluded from portfolio; reason recorded


class ExperimentPlan(BaseModel):
    """Pre-registration: written BEFORE running (Rule 33)."""

    experiment_id: str  # E-001
    research_question: str = ""
    hypothesis: str = ""
    dataset: str = ""
    data_hash: str = ""
    model: str = ""
    parameters: dict = Field(default_factory=dict)
    seed: int | None = None
    baseline: str = ""
    metric: str = ""
    split: str = ""  # time-based | cv | group | spatial | none
    expected_artifacts: list[str] = Field(default_factory=list)
    success_condition: str = ""
    status: ExperimentStatus = ExperimentStatus.planned
    # For portfolio bookkeeping: which experiment family it belongs to.
    family: str = ""  # eda | baseline | comparison | sensitivity | robustness | tuning | ablation | scenario


class ExperimentArtifacts(BaseModel):
    """What the runner must persist to disk (Rule 34)."""

    experiment_id: str
    result_json: str = ""  # relative path
    metrics_csv: str = ""
    predictions_csv: str = ""
    figures: list[str] = Field(default_factory=list)
    tables: list[str] = Field(default_factory=list)
    logs: list[str] = Field(default_factory=list)
