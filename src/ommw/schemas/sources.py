"""Source ledger (workspace/state/sources.jsonl).

Distinguishes metadata verification (the paper exists) from claim verification
(the paper actually supports the sentence citing it). A DOI existing is NOT
sufficient.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class SourceVerification(str, Enum):
    unverified = "UNVERIFIED"
    metadata_verified = "METADATA_VERIFIED"
    claim_verified = "CLAIM_VERIFIED"
    unverified_offline = "UNVERIFIED_OFFLINE"  # offline mode, cache miss


class Source(BaseModel):
    source_id: str  # e.g. S-001
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    venue: str = ""
    doi: str = ""
    url: str = ""
    retrieved_at: str = ""
    metadata_verified: bool = False
    content_verified: bool = False  # did a human/agent confirm it supports the claim?
    verification: SourceVerification = SourceVerification.unverified
    claims_supported: list[str] = Field(default_factory=list)  # Claim IDs
    cache_path: str = ""  # local metadata cache file (if any)
