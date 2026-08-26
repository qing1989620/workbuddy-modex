"""Visualization Laboratory (Layer 7, Rule 49-57).

A figure must serve a question: before creating one, answer
Question / Claim / Data / Why-this-figure (Rule 50). The planner recommends
figure types from claim types; the QA validates plans and figure registries.
Deterministic, no matplotlib dependency in this core.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..verify import Finding, VerifyReport

# Data visualization catalog (Rule 51) — selected by claim/question type.
DATA_VIZ: dict[str, list[str]] = {
    "distribution": ["histogram", "kde", "box-plot", "violin"],
    "missingness": ["missingness-heatmap", "bar"],
    "correlation": ["scatter", "pair-plot", "correlation-heatmap"],
    "trend": ["line", "seasonal-decompose"],
    "comparison": ["bar", "box-plot", "grouped-bar"],
    "spatial": ["spatial-map", "choropleth"],
    "network": ["network-graph", "adjacency-heatmap"],
    "cluster": ["pca-2d", "cluster-scatter"],
}

# Model visualization catalog (Rule 52).
MODEL_VIZ: dict[str, list[str]] = {
    "workflow": ["mermaid-flow", "graphviz-flow"],
    "optimization": ["optimization-flow", "feasible-region"],
    "network-model": ["network-diagram"],
    "state-transition": ["state-diagram"],
    "ode": ["phase-plot", "trajectory"],
    "architecture": ["model-architecture"],
    "decision": ["decision-tree", "causal-diagram"],
}

# Experiment visualization catalog (Rule 53).
EXPERIMENT_VIZ: dict[str, list[str]] = {
    "baseline-comparison": ["grouped-bar", "line"],
    "model-comparison": ["bar", "box-plot"],
    "error": ["error-distribution", "residual-plot"],
    "classification": ["roc", "pr-curve", "confusion-matrix"],
    "calibration": ["calibration-curve"],
    "convergence": ["convergence-line"],
    "sensitivity": ["parameter-sweep", "heatmap"],
    "ablation": ["ablation-bar"],
    "uncertainty": ["interval-plot", "error-bar"],
    "scenario": ["scenario-line", "scenario-bar"],
}


@dataclass
class FigurePlan:
    """Pre-registration for one figure (Rule 50)."""

    figure_id: str
    question: str = ""
    claim: str = ""  # Claim ID the figure supports
    data: str = ""  # data path / result IDs
    why: str = ""  # why THIS figure answers the question
    figure_type: str = ""  # recommended type
    section: str = ""
    output: str = ""


def recommend_figure_type(claim_type: str, context: str = "data") -> str:
    """Map a claim/question type to a recommended figure type."""
    key = claim_type.lower()
    for tag, viz in (DATA_VIZ if context == "data" else EXPERIMENT_VIZ).items():
        if tag in key or key in tag:
            return viz[0]
    if context == "model":
        return MODEL_VIZ.get(key, ["mermaid-flow"])[0]
    return "line"  # safe fallback


def plan_figure(*, figure_id: str, question: str, claim: str, data: str,
                why: str, section: str = "", context: str = "data",
                claim_type: str = "comparison") -> FigurePlan:
    """Build a figure plan; missing elements fail validation later."""
    return FigurePlan(
        figure_id=figure_id, question=question, claim=claim, data=data,
        why=why, figure_type=recommend_figure_type(claim_type, context),
        section=section, output=f"figures/{figure_id.lower()}.png",
    )


def validate_figure_plan(plan: FigurePlan) -> VerifyReport:
    """Figure QA (Rule 50, 55): every figure must answer Q/C/D/Why."""
    rep = VerifyReport()
    if not plan.question:
        rep.add("HIGH", "fig-no-question", f"{plan.figure_id}: missing Question", plan.figure_id)
    if not plan.claim:
        rep.add("HIGH", "fig-no-claim", f"{plan.figure_id}: missing Claim link", plan.figure_id)
    if not plan.data:
        rep.add("MEDIUM", "fig-no-data", f"{plan.figure_id}: missing Data", plan.figure_id)
    if not plan.why:
        rep.add("HIGH", "fig-no-why", f"{plan.figure_id}: missing Why-this-figure", plan.figure_id)
    return rep


def validate_figure_registry_entries(entries: list[dict]) -> VerifyReport:
    """Validate persisted figure-register entries against the Q/C/D/Why contract."""
    rep = VerifyReport()
    for e in entries:
        fid = e.get("figure_id", "?")
        for req in ("question", "claim", "data", "why"):
            if not e.get(req):
                rep.add("MEDIUM", "fig-registry-incomplete",
                        f"{fid}: missing '{req}' in registry", fid)
        out = e.get("output", "")
        if out and not out.endswith((".png", ".pdf", ".svg")):
            rep.add("MEDIUM", "fig-output-format",
                    f"{fid}: output should be PDF/SVG/high-DPI PNG, got {out}", fid)
    return rep
