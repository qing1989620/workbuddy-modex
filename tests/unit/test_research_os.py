"""Unit tests for the v1.0 Research Operating System modules."""
from __future__ import annotations

from pathlib import Path

from ommw import atomic
from ommw.competition import (
    build_profile,
    check_query_allowed,
    detect_competition,
    generate_ai_report,
    save_profile,
)
from ommw.data_engine import DataAuditSpec, audit_csv
from ommw.experiment_lab import portfolio_for_problem, run_experiment
from ommw.paths import ProjectPaths
from ommw.schemas import AIUsageRecord, CompetitionMode
from ommw.schemas.experiment_lab import ExperimentPlan, ExperimentStatus
from ommw.validation import ResultToValidate, SanityPair, independent_sanity_check, validate_result


def test_detect_cumcm() -> None:
    d = detect_competition("全国大学生数学建模竞赛 C 题", live=False)
    assert d.competition == "cumcm"
    assert d.mode == CompetitionMode.training


def test_detect_mcm_live() -> None:
    d = detect_competition("MCM Problem C", live=True)
    assert d.competition == "mcm_icm"
    assert d.mode == CompetitionMode.live


def test_profile_page_budget_precedence() -> None:
    # Official rule > user preference > default (Rule 5).
    p = build_profile(detect_competition("cumcm"), page_limit=20)
    assert p.effective_page_limit(user_preference=12, default=30) == 20
    p2 = build_profile(detect_competition("generic", live=False), page_limit=0)
    assert p2.effective_page_limit(user_preference=12, default=30) == 12
    assert p2.effective_page_limit(default=30) == 30


def test_live_gate_blocks_solution_search() -> None:
    p = build_profile(detect_competition("cumcm", live=True))
    assert not check_query_allowed(p, "2026 cumcm 答案 题解").allowed
    assert not check_query_allowed(p, "本题答案").allowed
    assert check_query_allowed(p, "cumcm official rules").allowed


def test_profile_save_load(tmp_path: Path) -> None:
    pp = ProjectPaths(root=tmp_path / "p")
    pp.ensure_dirs()
    prof = build_profile(detect_competition("cumcm"))
    save_profile(pp, prof)
    from ommw.competition import load_profile
    loaded = load_profile(pp)
    assert loaded is not None
    assert loaded.competition == "cumcm"


def test_ai_usage_ledger_and_report(tmp_path: Path) -> None:
    pp = ProjectPaths(root=tmp_path / "p")
    pp.ensure_dirs()
    from ommw.competition import append_usage, summarize
    append_usage(pp, AIUsageRecord(tool="ommw-agent", task="t", purpose="p",
                                   verification_method="executed-test", accepted=True,
                                   human_review=True))
    append_usage(pp, AIUsageRecord(tool="sympy", task="t2", purpose="p2",
                                   verification_method="manual", accepted=False))
    s = summarize(pp)
    assert s.total_records == 2 and s.accepted == 1 and s.human_reviewed == 1
    decl, detail = generate_ai_report(pp)
    assert "AI" in decl
    assert pp.paper_dir.joinpath("ai-usage-declaration.md").exists()


def test_experiment_planner_portfolio() -> None:
    plans = portfolio_for_problem("prediction", n_models=2, complexity="low", has_data=False)
    families = {p.family for p in plans}
    assert families <= {"baseline", "comparison"}
    plans2 = portfolio_for_problem("timeseries", n_models=2, time_series=True, complexity="high")
    families2 = {p.family for p in plans2}
    assert "validation" in families2 and "sensitivity" in families2


def test_experiment_runner_persists(tmp_path: Path) -> None:
    pp = ProjectPaths(root=tmp_path / "p")
    pp.ensure_dirs()
    plan = ExperimentPlan(experiment_id="E-001", model="m", metric="mae",
                          family="comparison", status=ExperimentStatus.planned)

    def exec(p):
        return {"metrics": {"mae": 0.5}, "predictions": [{"t": 0, "y": 1.0}],
                "result": {"mae": 0.5}}

    arts = run_experiment(pp, plan, exec)
    assert (pp.root / arts.result_json).exists()
    assert (pp.root / arts.metrics_csv).exists()
    assert (pp.root / arts.predictions_csv).exists()


def test_result_validator_units_and_ranges() -> None:
    rep1 = validate_result(None, ResultToValidate(result_id="R-1", value="1.37", domain="probability"))
    assert any(f.code == "range-probability" for f in rep1.findings)
    rep2 = validate_result(None, ResultToValidate(result_id="R-2", value="0.5", domain="probability"))
    assert rep2.passed
    rep3 = validate_result(None, ResultToValidate(result_id="R-3", value="-2", unit="orders"))
    assert any(f.code in ("unit-negative", "range-nonneg") for f in rep3.findings)


def test_independent_sanity_check() -> None:
    rep = independent_sanity_check([SanityPair(label="a", value_a=1.0, value_b=1.000001, tolerance=1e-3)])
    assert rep.passed
    rep2 = independent_sanity_check([SanityPair(label="b", value_a=1.0, value_b=2.0, tolerance=1e-6)])
    assert any(f.code == "sanity-mismatch" for f in rep2.findings)


def test_data_audit_detects_issues(tmp_path: Path) -> None:
    csv = tmp_path / "d.csv"
    csv.write_text("id,count,prob\na,-1,0.5\nb,,1.37\nc,3,\n", encoding="utf-8")
    spec = DataAuditSpec(expected_columns=["id", "count", "prob"],
                         nonneg_columns=["count"], bounded_columns={"prob": (0.0, 1.0)},
                         id_column="id")
    rep = audit_csv(csv, spec)
    codes = {f.code for f in rep.findings}
    assert "impossible-negative" in codes  # count=-1
    assert "range-out-of-bounds" in codes  # prob=1.37
    assert "missing" in codes or "missing-ratio" in codes  # missing values


def test_model_router_has_baseline() -> None:
    from ommw.modeling import route_candidates
    for pt in ("prediction", "optimization", "timeseries", "evaluation"):
        cands = route_candidates(pt)
        assert any(c.family == "baseline" for c in cands), pt
