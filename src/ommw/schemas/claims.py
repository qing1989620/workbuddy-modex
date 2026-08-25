"""Claim ledger (workspace/state/claims.jsonl).

Only claims with status SUPPORTED or VERIFIED may enter the paper's formal
conclusions. Every numeric assertion in the paper must trace to a Result ID
via evidence_ids; every citation must trace to a verified Source ID.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ClaimStatus(str, Enum):
    proposed = "PROPOSED"
    supported = "SUPPORTED"  # backed by results but not yet independently reviewed
    verified = "VERIFIED"  # passed review
    rejected = "REJECTED"


class Claim(BaseModel):
    claim_id: str  # e.g. C-001
    statement: str
    type: str = "factual"  # factual | methodological | comparative | interpretive
    question: str = ""  # which problem sub-question this supports
    evidence_ids: list[str] = Field(default_factory=list)  # Result IDs
    source_ids: list[str] = Field(default_factory=list)  # Source IDs
    model_id: str | None = None
    status: ClaimStatus = ClaimStatus.proposed
    confidence: str = "low"  # low | medium | high
    limitations: str = ""
    # Tracking: which chapter/section uses this claim.
    used_in: list[str] = Field(default_factory=list)
