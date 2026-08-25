"""Project-level metadata (workspace/state/project.yaml)."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class OutputMode(str, Enum):
    latex = "latex"
    word = "word"
    dual = "dual"


class Rigor(str, Enum):
    quick = "quick"
    strict = "strict"
    competition = "competition"
    research = "research"


class ProjectYaml(BaseModel):
    """Top-level project descriptor. Bound to a workflow major version."""

    title: str = ""
    competition: str = "generic"  # competition profile name under templates/competition/
    output_mode: OutputMode = OutputMode.latex
    rigor: Rigor = Rigor.strict
    schema_version: int = 1
    workflow_version: str = "0.1.0"
    created_at: str = ""
    language: str = "zh"  # zh | en | bilingual
    time_budget_minutes: int | None = None  # competition mode only

    # Human-facing problem statement (the agent also decomposes it).
    problem_statement: str = ""

    # Cross-format parity requires a shared chapter contract.
    chapters: list[str] = Field(
        default_factory=lambda: [
            "abstract",
            "introduction",
            "problem-restatement",
            "assumptions",
            "notation",
            "models",
            "experiments",
            "results",
            "robustness",
            "conclusions",
        ]
    )
