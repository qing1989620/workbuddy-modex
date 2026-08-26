"""Paper Production Kernel -- Paper Contract & Question Contract (v0.2).

Spec §11 / §14: no prose before a contract. The contract is written to
``state/paper-contract.yaml`` once research has essentially settled; every
chapter then draws its obligations (evidence, equations, figures, experiments)
from the contract instead of improvising.

Contracts are data, not prose: gates read them to know what "complete" means
for THIS competition and THESE questions.
"""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from .. import atomic
from ..paths import ProjectPaths


class QuestionContract(BaseModel):
    """One subproblem's binding plan (spec §14)."""
    question_id: str = "Q1"
    objective: str = ""
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    decision_variables: list[str] = Field(default_factory=list)
    model_family: str = ""
    mathematical_formulation: str = ""       # short description of eq groups
    solution_algorithm: str = ""
    min_display_equations: int = 2           # feeds FORMULA_SUFFICIENCY_GATE
    requires_experiments: bool = True
    requires_visual_evidence: bool = True
    experiments: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    figures: list[str] = Field(default_factory=list)
    tables: list[str] = Field(default_factory=list)
    validation: str = ""
    sensitivity: str = ""
    answer: str = ""                          # explicit subproblem answer
    depends_on: list[str] = Field(default_factory=list)  # e.g. ["Q1"]
    section_files: list[str] = Field(default_factory=list)


class PaperContract(BaseModel):
    """Whole-paper contract (spec §11)."""
    competition: str = "generic"
    problem: str = ""
    language: str = "zh"
    page_limit: int = 0                       # 0 = from profile / unlimited
    template_id: str = ""                     # template-registry.json key
    title: str = ""

    questions: list[QuestionContract] = Field(default_factory=list)

    abstract_required: bool = True            # ABSTRACT_GATE is always on anyway
    paper_sections: list[str] = Field(default_factory=lambda: [
        "abstract", "introduction", "problem-restatement", "problem-analysis",
        "assumptions", "notation", "data-processing", "models",
        "experiment", "results", "validation", "sensitivity", "evaluation",
        "conclusions", "references", "appendix",
    ])
    required_equations: dict[str, int] = Field(default_factory=dict)   # chapter -> min display eqs
    justified_low_formula_density: list[str] = Field(default_factory=list)
    justified_no_visual: list[str] = Field(default_factory=list)

    def gate_options(self) -> dict:
        """Flatten into the options dict consumed by paper.gates."""
        return {
            "min_display_equations": self.required_equations,
            "justified_low_formula_density": self.justified_low_formula_density,
            "justified_no_visual": self.justified_no_visual,
            "requires_experiments": any(q.requires_experiments for q in self.questions)
            if self.questions else True,
        }


CONTRACT_PATH = "paper-contract.yaml"


def contract_path(pp: ProjectPaths) -> Path:
    return pp.state_dir / CONTRACT_PATH


def save_contract(pp: ProjectPaths, c: PaperContract) -> Path:
    p = contract_path(pp)
    atomic.write_yaml(p, c.model_dump(mode="json"))
    return p


def load_contract(pp: ProjectPaths) -> PaperContract | None:
    p = contract_path(pp)
    data = atomic.read_yaml(p) if p.exists() else None
    return PaperContract(**data) if data else None


def scaffold_contract(pp: ProjectPaths, *, competition: str, problem: str,
                      language: str, n_questions: int,
                      page_limit: int = 0, template_id: str = "") -> PaperContract:
    """Build a starter contract from the problem decomposition.

    The agent refines objectives/model families afterwards; the scaffold only
    guarantees that every question HAS a contract before drafting starts.
    """
    qs = []
    for i in range(1, n_questions + 1):
        qid = f"Q{i}"
        q = QuestionContract(
            question_id=qid,
            objective=f"(fill) what exactly {qid} must answer",
            model_family="(fill after MODEL_SCREENING)",
            min_display_equations=3,
            depends_on=(["Q1"] if i == 2 else [f"Q{i-1}"] if i > 1 else []),
            section_files=[f"question{i}"],
        )
        qs.append(q)
    req_eq = {q.section_files[0]: q.min_display_equations for q in qs}
    return PaperContract(
        competition=competition, problem=problem, language=language,
        page_limit=page_limit, template_id=template_id,
        questions=qs, required_equations=req_eq,
    )
