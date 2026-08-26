"""Pydantic state schemas for the Research Core.

These models are the single source of truth for machine-readable project state.
LLM prose and rendered papers are NEVER the source of truth; they are derived
from these ledgers. All models use Pydantic v2 for validation.

Ledgers are stored as JSONL (append-friendly) or YAML (human-editable).
"""
from __future__ import annotations

from .ai_usage import AIUsageRecord, AIUsageSummary
from .assumptions import Assumption, AssumptionStatus
from .claims import Claim, ClaimStatus
from .competition_profile import CompetitionMode, CompetitionProfile
from .experiment_lab import ExperimentArtifacts, ExperimentPlan
from .experiments import Experiment, ExperimentStatus
from .figures import FigureRecord
from .model_discovery import InnovationRecord, ModelCandidate
from .notation import NotationEntry
from .progress import Progress, Stage
from .project import OutputMode, ProjectYaml, Rigor
from .results import Result
from .sources import Source, SourceVerification
from .tables import TableRecord

__all__ = [
    "AIUsageRecord",
    "AIUsageSummary",
    "Assumption",
    "AssumptionStatus",
    "Claim",
    "ClaimStatus",
    "CompetitionMode",
    "CompetitionProfile",
    "Experiment",
    "ExperimentArtifacts",
    "ExperimentPlan",
    "ExperimentStatus",
    "FigureRecord",
    "InnovationRecord",
    "ModelCandidate",
    "NotationEntry",
    "OutputMode",
    "Progress",
    "ProjectYaml",
    "Result",
    "Rigor",
    "Source",
    "SourceVerification",
    "Stage",
    "TableRecord",
]
