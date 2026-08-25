"""Experiment ledger (workspace/state/experiments.jsonl)."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ExperimentStatus(str, Enum):
    running = "RUNNING"
    completed = "COMPLETED"
    failed = "FAILED"
    stale = "STALE"  # upstream data/code changed


class Experiment(BaseModel):
    run_id: str  # e.g. E-001
    question: str = ""
    model: str = ""
    dataset_hash: str = ""
    code_hash: str = ""
    environment: str = ""  # python version, key package versions
    parameters: dict = Field(default_factory=dict)
    seed: int | None = None
    metrics: dict = Field(default_factory=dict)
    artifacts: list[str] = Field(default_factory=list)  # relative paths
    status: ExperimentStatus = ExperimentStatus.running
    timestamp: str = ""
