"""Paper Production Kernel (v0.2 upgrade).

Turns verified Research Core evidence into a *complete, dense, auditable*
competition paper. Deterministic engines here; narrative judgment in the
agent workflow + independent reviewers.
"""
from .contract import (
    PaperContract,
    QuestionContract,
    load_contract,
    scaffold_contract,
    save_contract,
)
from .density import analyze_latex_dir, build_density_report
from .gates import (
    abstract_gate,
    experiment_sufficiency_gate,
    figure_text_coupling_gate,
    formula_sufficiency_gate,
    gate_status,
    has_critical,
    latex_layout_gate,
    narrative_continuity_gate,
    placeholder_gate,
    result_consistency_gate,
    run_all_paper_gates,
    symbol_consistency_gate,
    visual_evidence_gate,
)
from .scorecard import Scorecard, score_paper

__all__ = [
    "PaperContract", "QuestionContract", "load_contract", "save_contract",
    "scaffold_contract",
    "analyze_latex_dir", "build_density_report",
    "abstract_gate", "placeholder_gate", "formula_sufficiency_gate",
    "visual_evidence_gate", "figure_text_coupling_gate",
    "experiment_sufficiency_gate", "narrative_continuity_gate",
    "symbol_consistency_gate", "result_consistency_gate",
    "latex_layout_gate", "run_all_paper_gates", "gate_status", "has_critical",
    "Scorecard", "score_paper",
]
