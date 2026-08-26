"""Model discovery + innovation schemas (Rule 25-27, 47-48)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ModelCandidate(BaseModel):
    """One row of the model candidate matrix (Rule 26)."""

    model: str
    family: str = ""  # regression | ml | time-series | optimization | simulation | ...
    theoretical_fit: str = ""
    data_requirement: str = ""
    assumptions: list[str] = Field(default_factory=list)
    interpretability: str = ""  # high | medium | low + note
    computational_cost: str = ""  # low | medium | high + note
    expected_strength: str = ""
    expected_weakness: str = ""
    validation_strategy: str = ""
    reason_to_test: str = ""
    reason_rejected: str = ""  # filled when screened out


class InnovationRecord(BaseModel):
    """Innovation must come from real differences, never from language (Rule 47-48)."""

    innovation_id: str  # IN-001
    baseline: str = ""  # what is the reference/standard approach
    difference: str = ""  # new constraint/objective/representation/adaptation/data/validation/...
    reason: str = ""
    evidence: str = ""  # result/experiment supporting it
    measured_benefit: str = ""  # quantitative or explicit qualitative
    limitation: str = ""
    # Anti-false-novelty: claims like "first in the world" require supporting sources.
    novelty_claim: str = ""  # e.g. "none | problem-specific | literature-backed | verified"
