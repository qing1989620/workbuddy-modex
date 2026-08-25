"""Notation registry (workspace/state/notation.yaml). Every symbol is unique."""
from __future__ import annotations

from pydantic import BaseModel


class NotationEntry(BaseModel):
    symbol: str
    definition: str
    unit: str = ""
    domain: str = ""  # e.g. R+, Z, [0,1]
    question: str = ""  # which sub-question introduced it
    first_used: str = ""  # chapter/section
