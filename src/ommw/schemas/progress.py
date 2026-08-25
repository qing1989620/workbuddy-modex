"""Progress / Problem State Machine (workspace/state/progress.json).

Drives resume capability: `ommw status` reads this and continues from the
last completed gate. Writes are atomic (see atomic.py).
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Stage(str, Enum):
    received = "RECEIVED"
    discovery = "DISCOVERY"
    competition_profile = "COMPETITION_PROFILE"
    problem_decomposition = "PROBLEM_DECOMPOSITION"
    data_audit = "DATA_AUDIT"
    literature_research = "LITERATURE_RESEARCH"
    assumptions = "ASSUMPTIONS"
    model_candidates = "MODEL_CANDIDATES"
    baseline = "BASELINE"
    model_screening = "MODEL_SCREENING"
    formulation = "FORMULATION"
    implementation = "IMPLEMENTATION"
    experiment = "EXPERIMENT"
    validation = "VALIDATION"
    robustness = "ROBUSTNESS"
    interpretation = "INTERPRETATION"
    paper_blueprint = "PAPER_BLUEPRINT"
    chapter_loop = "CHAPTER_LOOP"
    global_audit = "GLOBAL_AUDIT"
    render = "RENDER"
    output_qa = "OUTPUT_QA"
    final_verify = "FINAL_VERIFY"

    @classmethod
    def ordered(cls) -> list["Stage"]:
        return list(Stage)


class ChapterLifecycle(str, Enum):
    planned = "PLANNED"
    evidence_ready = "EVIDENCE_READY"
    drafted = "DRAFTED"
    math_reviewed = "MATH_REVIEWED"
    scientific_reviewed = "SCIENTIFIC_REVIEWED"
    judge_reviewed = "JUDGE_REVIEWED"
    revised = "REVISED"
    content_accepted = "CONTENT_ACCEPTED"
    rendered = "RENDERED"
    format_verified = "FORMAT_VERIFIED"


class ChapterState(BaseModel):
    name: str
    lifecycle: ChapterLifecycle = ChapterLifecycle.planned
    open_findings: int = 0


class Progress(BaseModel):
    current_stage: Stage = Stage.received
    completed_stages: list[Stage] = Field(default_factory=list)
    chapters: list[ChapterState] = Field(default_factory=list)
    degraded: list[str] = Field(default_factory=list)  # graceful-degradation notes
    last_updated: str = ""

    def is_complete(self, stage: Stage) -> bool:
        return stage in self.completed_stages
