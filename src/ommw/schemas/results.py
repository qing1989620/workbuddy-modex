"""Result ledger (workspace/state/results.jsonl).

Every important numeric value in the paper references a Result ID rather than
being hand-typed. This is the core anti-hallucination mechanism for numbers.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class Result(BaseModel):
    result_id: str  # e.g. R-013
    name: str
    value: str  # kept as string to preserve exact precision/significance
    unit: str = ""
    precision: str = ""  # e.g. "3 sig figs"; governed by precision-policy.yaml
    source_script: str = ""  # relative path under code/
    source_data_hash: str = ""  # SHA256 of the input data this result came from
    parameters: dict = Field(default_factory=dict)
    seed: int | None = None
    run_id: str = ""  # links to Experiment ledger
    created_at: str = ""
    verified: bool = False  # passed statistical/numerical verification
