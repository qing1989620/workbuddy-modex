"""AI Usage Ledger (Rule 7). Every AI-assisted step is recorded so the paper's
AI-usage declaration is generated from the actual log — never fabricated.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class AIUsageRecord(BaseModel):
    record_id: str = ""  # AU-001; auto-assigned on append if empty
    tool: str  # e.g. "workbuddy-agent", "sympy", "latexmk", "llm-ommw"
    model: str = ""
    version: str = ""
    timestamp: str = ""
    task: str = ""  # e.g. "Q2-optimization-formulation"
    purpose: str = ""  # what was being accomplished
    input_category: str = ""  # problem_text | raw_data | processed_data | code | paper_text | ...
    output_category: str = ""  # analysis | code | figure | table | text | result | review
    human_review: bool = False  # did a human verify this output
    verification_method: str = ""  # executed-test | cross-check | manual | none
    accepted: bool = False  # used in final output
    modified: bool = False  # human/agent modified before acceptance
    final_usage: str = "report"  # whether to disclose in the AI declaration


class AIUsageSummary(BaseModel):
    total_records: int = 0
    accepted: int = 0
    human_reviewed: int = 0
    tools: list[str] = Field(default_factory=list)
    generated_at: str = ""
