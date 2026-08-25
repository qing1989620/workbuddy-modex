"""Assumption ledger (workspace/state/assumptions.yaml)."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class AssumptionStatus(str, Enum):
    proposed = "PROPOSED"
    accepted = "ACCEPTED"
    rejected = "REJECTED"


class Assumption(BaseModel):
    assumption_id: str  # e.g. A-001
    statement: str
    reason: str = ""
    evidence: str = ""
    impact: str = ""  # what changes if this assumption is wrong
    sensitivity_required: bool = False
    status: AssumptionStatus = AssumptionStatus.proposed
