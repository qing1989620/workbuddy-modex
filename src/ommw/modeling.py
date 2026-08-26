"""Model Discovery (Layer 4, Rule 25-29).

Problem-Type Router: given a problem family, return candidate model families
with feasibility notes. NOT "pick a fancy model by default" — the baseline is
always present and complex models must justify themselves (Rule 28, 30).
"""
from __future__ import annotations

from .schemas import ModelCandidate

# Problem-type -> candidate families. Every candidate has a reason_to_test.
ROUTES: dict[str, list[ModelCandidate]] = {
    "prediction": [
        ModelCandidate(model="mean/naive baseline", family="baseline",
                       theoretical_fit="trivial reference", data_requirement="none",
                       computational_cost="low", expected_strength="simple, honest",
                       expected_weakness="ignores patterns", reason_to_test="mandatory baseline (Rule 28)"),
        ModelCandidate(model="linear regression", family="regression",
                       theoretical_fit="linear trend + noise", data_requirement="low",
                       computational_cost="low", interpretability="high",
                       expected_strength="interpretable, fast", expected_weakness="no nonlinearity",
                       reason_to_test="first strong candidate; interpretable"),
        ModelCandidate(model="random forest", family="ml",
                       theoretical_fit="nonlinear, tabular", data_requirement="medium",
                       computational_cost="medium", interpretability="medium",
                       expected_strength="captures interactions", expected_weakness="less interpretable",
                       reason_to_test="only if nonlinearity is evidenced"),
    ],
    "classification": [
        ModelCandidate(model="majority class baseline", family="baseline",
                       theoretical_fit="reference accuracy", data_requirement="none",
                       computational_cost="low", reason_to_test="mandatory baseline"),
        ModelCandidate(model="logistic regression", family="regression",
                       theoretical_fit="linear decision boundary", data_requirement="low",
                       computational_cost="low", interpretability="high",
                       expected_strength="calibrated probabilities", expected_weakness="linear only",
                       reason_to_test="first strong candidate"),
    ],
    "evaluation": [
        ModelCandidate(model="simple weighted score baseline", family="baseline",
                       theoretical_fit="explicit weights", data_requirement="low",
                       computational_cost="low", interpretability="high",
                       reason_to_test="mandatory baseline"),
        ModelCandidate(model="entropy/TOPSIS-like multi-criteria", family="mcda",
                       theoretical_fit="multi-criteria ranking", data_requirement="medium",
                       computational_cost="low", interpretability="high",
                       expected_weakness="weight sensitivity",
                       reason_to_test="only if problem explicitly multi-criteria"),
    ],
    "optimization": [
        ModelCandidate(model="greedy/naive feasible baseline", family="baseline",
                       theoretical_fit="any feasible solution as reference", data_requirement="low",
                       computational_cost="low", interpretability="high",
                       expected_strength="honest reference", expected_weakness="far from optimal",
                       reason_to_test="mandatory baseline (Rule 28)"),
        ModelCandidate(model="LP/QP deterministic solver", family="optimization",
                       theoretical_fit="linear/convex objective+constraints", data_requirement="low",
                       computational_cost="low", interpretability="high",
                       expected_weakness="non-convex not handled",
                       reason_to_test="mature solver first (Rule 30)"),
        ModelCandidate(model="MILP solver", family="optimization",
                       theoretical_fit="integer decisions", data_requirement="medium",
                       computational_cost="medium", interpretability="high",
                       reason_to_test="only if integer/binary variables exist"),
    ],
    "network": [
        ModelCandidate(model="networkx structural baseline", family="graph",
                       theoretical_fit="graph metrics", data_requirement="graph",
                       computational_cost="low", reason_to_test="mandatory baseline"),
        ModelCandidate(model="community/centrality analysis", family="graph",
                       theoretical_fit="network structure", data_requirement="graph",
                       computational_cost="low", interpretability="high",
                       reason_to_test="if question is about structure"),
    ],
    "simulation": [
        ModelCandidate(model="monte carlo simulation", family="simulation",
                       theoretical_fit="stochastic process", data_requirement="distributions",
                       computational_cost="medium", expected_weakness="seed sensitivity",
                       reason_to_test="multi-seed with mean/std (Rule 31)"),
    ],
    "timeseries": [
        ModelCandidate(model="naive/seasonal-naive baseline", family="baseline",
                       theoretical_fit="reference", data_requirement="none",
                       computational_cost="low", reason_to_test="mandatory baseline"),
        ModelCandidate(model="ARIMA/ETS", family="time-series",
                       theoretical_fit="autocorrelation structure", data_requirement="medium",
                       computational_cost="low", interpretability="high",
                       expected_weakness="stationarity assumptions",
                       reason_to_test="time-based split only (Rule 64)"),
    ],
    "spatial": [
        ModelCandidate(model="distance-based baseline", family="baseline",
                       theoretical_fit="reference", data_requirement="coordinates",
                       computational_cost="low", reason_to_test="mandatory baseline"),
        ModelCandidate(model="spatial interpolation (IDW/Kriging)", family="spatial",
                       theoretical_fit="spatial autocorrelation", data_requirement="medium",
                       computational_cost="medium", interpretability="medium",
                       reason_to_test="if spatial dependence is evidenced"),
    ],
    "multiobjective": [
        ModelCandidate(model="weighted-sum LP baseline", family="optimization",
                       theoretical_fit="scalarization", data_requirement="low",
                       computational_cost="low", interpretability="high",
                       reason_to_test="mandatory baseline"),
        ModelCandidate(model="epsilon-constraint / Pareto front", family="optimization",
                       theoretical_fit="trade-off surface", data_requirement="medium",
                       computational_cost="medium", interpretability="medium",
                       reason_to_test="if trade-offs are the question"),
    ],
}

DEFAULT_ROUTE = [
    ModelCandidate(model="baseline", family="baseline",
                   theoretical_fit="reference", data_requirement="low",
                   computational_cost="low", reason_to_test="mandatory baseline"),
    ModelCandidate(model="appropriate simple model", family="depends",
                   theoretical_fit="problem-specific", data_requirement="low",
                   computational_cost="low", interpretability="high",
                   reason_to_test="understand the problem before complex models"),
]


def route_candidates(problem_type: str) -> list[ModelCandidate]:
    """Return candidate families for a problem type (never empty)."""
    return ROUTES.get(problem_type, DEFAULT_ROUTE)
