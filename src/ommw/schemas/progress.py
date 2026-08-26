"""Progress / Problem State Machine (workspace/state/progress.json).

Drives resume capability: `ommw status` reads this and continues from the
last completed gate. Writes are atomic (see atomic.py).
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Stage(str, Enum):
    """v1.0 Research Operating System state machine (backward compatible with v0.1).

    Added stages (v1.0): ENVIRONMENT_DISCOVERY, COMPETITION_DISCOVERY,
    COMPLIANCE_CHECK, PROBLEM_INGESTION, RESEARCH_PLAN, DATA_DISCOVERY,
    DOMAIN_RESEARCH, EXPERIMENT_PLAN, EXPERIMENT_EXECUTION,
    STATISTICAL_VALIDATION, MODEL_SELECTION, CLAIM_SYNTHESIS,
    GLOBAL_CONSISTENCY, COMPETITION_JUDGE, SUBMISSION_GATE, VERIFIED.
    """

    received = "RECEIVED"
    environment_discovery = "ENVIRONMENT_DISCOVERY"
    competition_discovery = "COMPETITION_DISCOVERY"
    compliance_check = "COMPLIANCE_CHECK"
    problem_ingestion = "PROBLEM_INGESTION"
    discovery = "DISCOVERY"
    competition_profile = "COMPETITION_PROFILE"
    problem_decomposition = "PROBLEM_DECOMPOSITION"
    research_plan = "RESEARCH_PLAN"
    data_discovery = "DATA_DISCOVERY"
    data_audit = "DATA_AUDIT"
    domain_research = "DOMAIN_RESEARCH"
    literature_research = "LITERATURE_RESEARCH"
    assumptions = "ASSUMPTIONS"
    model_candidates = "MODEL_CANDIDATES"
    baseline = "BASELINE"
    baseline_design = "BASELINE_DESIGN"
    model_screening = "MODEL_SCREENING"
    mathematical_formulation = "MATHEMATICAL_FORMULATION"
    formulation = "FORMULATION"
    experiment_plan = "EXPERIMENT_PLAN"
    implementation = "IMPLEMENTATION"
    experiment = "EXPERIMENT"
    experiment_execution = "EXPERIMENT_EXECUTION"
    validation = "VALIDATION"
    result_validation = "RESULT_VALIDATION"
    statistical_validation = "STATISTICAL_VALIDATION"
    robustness = "ROBUSTNESS"
    robustness_analysis = "ROBUSTNESS_ANALYSIS"
    model_selection = "MODEL_SELECTION"
    interpretation = "INTERPRETATION"
    claim_synthesis = "CLAIM_SYNTHESIS"
    paper_blueprint = "PAPER_BLUEPRINT"
    chapter_loop = "CHAPTER_LOOP"
    global_consistency = "GLOBAL_CONSISTENCY"
    global_audit = "GLOBAL_AUDIT"
    competition_judge = "COMPETITION_JUDGE"
    render = "RENDER"
    format_render = "FORMAT_RENDER"
    output_qa = "OUTPUT_QA"
    visual_qa = "VISUAL_QA"
    submission_gate = "SUBMISSION_GATE"
    final_verify = "FINAL_VERIFY"
    verified = "VERIFIED"

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
