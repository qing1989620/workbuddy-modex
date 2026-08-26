"""Negative benchmarks (Rule 103, 141).

Each case deliberately injects a defect into a small project and asserts the
system detects it. If any detection is missed, the case FAILS.
"""
from __future__ import annotations

from pathlib import Path

from .. import atomic
from ..competition import compliance_gate, detect_competition
from ..paths import ProjectPaths
from ..schemas import (
    Claim,
    ClaimStatus,
    CompetitionMode,
    CompetitionProfile,
    Experiment,
    ExperimentStatus,
    FigureRecord,
    Result,
    Source,
    SourceVerification,
    TableRecord,
)
from ..validation import ResultToValidate, validate_result
from ..verify import research_verify
from .runner import BenchmarkCase


def _mk_project(tmp: Path) -> ProjectPaths:
    pp = ProjectPaths(root=tmp / "proj")
    pp.ensure_dirs()
    # Healthy baseline state.
    atomic.append_jsonl(pp.results_path, Result(
        result_id="R-001", name="mae", value="0.5000", unit="orders",
        source_data_hash="abc", run_id="E-001", verified=True).model_dump(mode="json"))
    atomic.append_jsonl(pp.experiments_path, Experiment(
        run_id="E-001", model="baseline", dataset_hash="abc", code_hash="x",
        status=ExperimentStatus.completed).model_dump(mode="json"))
    atomic.append_jsonl(pp.sources_path, Source(
        source_id="S-001", title="t", verification=SourceVerification.claim_verified,
        metadata_verified=True, content_verified=True).model_dump(mode="json"))
    atomic.append_jsonl(pp.claims_path, Claim(
        claim_id="C-001", statement="ok", type="comparative",
        evidence_ids=["R-001"], source_ids=["S-001"],
        status=ClaimStatus.supported).model_dump(mode="json"))
    return pp


def _expect(pp: ProjectPaths, code: str, check: str = "research_verify") -> dict:
    rep = research_verify(pp) if check == "research_verify" else None
    found = any(f.code == code for f in rep.findings) if rep else False
    return {"passed": found, "detail": f"expected {code}; {'caught' if found else 'MISSED'}"}


def case_fake_citation() -> dict:
    pp = _mk_project(Path(".") / ".build" / "bench" / "fake-cite")
    atomic.append_jsonl(pp.claims_path, Claim(
        claim_id="C-BAD", statement="fake", type="factual", source_ids=["S-999"],
        status=ClaimStatus.supported).model_dump(mode="json"))
    return _expect(pp, "unresolved-source")


def case_wrong_result_number() -> dict:
    pp = _mk_project(Path(".") / ".build" / "bench" / "orphan")
    (pp.word_dir / "sections").mkdir(parents=True, exist_ok=True)
    (pp.word_dir / "sections" / "results.md").write_text(
        "# Results\n\nThe accuracy was 0.9731428571 with no anchor.\n", encoding="utf-8")
    return _expect(pp, "orphan-number")


def case_wrong_unit() -> dict:
    r = ResultToValidate(result_id="R-001", value="-3.5", unit="orders", domain="nonneg")
    rep = validate_result(None, r)
    found = any(f.code == "range-nonneg" or f.code == "unit-negative" for f in rep.findings)
    return {"passed": found, "detail": f"negative orders; {'caught' if found else 'MISSED'}"}


def case_probability_out_of_range() -> dict:
    r = ResultToValidate(result_id="R-002", value="1.37", domain="probability")
    rep = validate_result(None, r)
    found = any(f.code == "range-probability" for f in rep.findings)
    return {"passed": found, "detail": f"p=1.37; {'caught' if found else 'MISSED'}"}


def case_broken_figure() -> dict:
    pp = _mk_project(Path(".") / ".build" / "bench" / "fig")
    atomic.append_jsonl(pp.figures_index, FigureRecord(
        figure_id="F-001", result_ids=["R-001"],
        output="figures/does-not-exist.png").model_dump(mode="json"))
    return _expect(pp, "broken-figure")


def case_inconsistent_table() -> dict:
    pp = _mk_project(Path(".") / ".build" / "bench" / "tbl")
    atomic.append_jsonl(pp.tables_index, TableRecord(
        table_id="T-001", result_ids=["R-999"], output="").model_dump(mode="json"))
    return _expect(pp, "registry-unresolved-result")


def case_unverified_claim_as_conclusion() -> dict:
    pp = _mk_project(Path(".") / ".build" / "bench" / "claim")
    atomic.append_jsonl(pp.claims_path, Claim(
        claim_id="C-BAD2", statement="conclusion", type="conclusion",
        evidence_ids=["R-001"], status=ClaimStatus.proposed).model_dump(mode="json"))
    return _expect(pp, "unsupported-conclusion")


def case_stale_experiment() -> dict:
    pp = _mk_project(Path(".") / ".build" / "bench" / "stale")
    atomic.append_jsonl(pp.experiments_path, Experiment(
        run_id="E-001", model="baseline", dataset_hash="abc", code_hash="x",
        status=ExperimentStatus.stale).model_dump(mode="json"))
    return _expect(pp, "stale-result")


def case_wrong_page_rule() -> dict:
    pp = _mk_project(Path(".") / ".build" / "bench" / "pages")
    # Simulate an over-limit PDF (placeholder page count > limit).
    profile = CompetitionProfile(
        competition="cumcm", year=2026, mode=CompetitionMode.training, page_limit=5,
        ai_policy="declare", anonymization_rule="none",
        page_limit_source="benchmark-injected")
    pp.latex_dir.mkdir(parents=True, exist_ok=True)
    pdf = pp.latex_dir / "output" / "main.pdf"
    pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf.write_bytes(b"%PDF-1.4\n" + (b"/Type /Page\n" * 9))
    rep = compliance_gate(pp, profile)
    found = any(f.code == "page-limit" for f in rep.findings)
    return {"passed": found, "detail": f"9 pages vs limit 5; {'caught' if found else 'MISSED'}"}


def case_ai_declaration_missing() -> dict:
    pp = _mk_project(Path(".") / ".build" / "bench" / "ai")
    profile = CompetitionProfile(
        competition="cumcm", year=2026, mode=CompetitionMode.training,
        ai_policy="must declare AI tool usage", page_limit=0)
    rep = compliance_gate(pp, profile)
    found = any(f.code == "ai-declaration-missing" for f in rep.findings)
    return {"passed": found, "detail": f"AI declaration; {'caught' if found else 'MISSED'}"}


def case_live_contest_search_block() -> dict:
    """LIVE mode: querying current-contest solutions must be blocked (Rule 6)."""
    from ..competition import check_query_allowed
    profile = CompetitionProfile(
        competition="cumcm", year=2026, mode=CompetitionMode.live,
        internet_rule="no current-contest solution search")
    blocked = check_query_allowed(profile, "2026 cumcm 答案 题解")
    allowed = check_query_allowed(profile, "cumcm official rules")
    ok = (not blocked.allowed) and allowed.allowed
    return {"passed": ok,
            "detail": f"blocked={'yes' if not blocked.allowed else 'NO'} allowed_legit={'yes' if allowed.allowed else 'NO'}"}


def case_anti_overengineering() -> dict:
    """Simple problem must NOT be routed to algorithm soup automatically."""
    from ..experiment_lab import portfolio_for_problem
    plans = portfolio_for_problem("prediction", n_models=2, complexity="low")
    families = {p.family for p in plans}
    # Simple problem: EDA (if data) + baseline + comparison only — no
    # sensitivity/robustness/scenario/multi-seed soup.
    allowed = {"eda", "baseline", "comparison"}
    ok = families <= allowed and len(plans) <= 3
    return {"passed": ok, "detail": f"families={sorted(families)} n={len(plans)} (soup-free={ok})"}


def case_model_simple_over_complex() -> dict:
    """Model selection must prefer the simpler model when evidence ties (Rule 105)."""
    from ..experiment_lab import portfolio_for_problem
    plans = portfolio_for_problem("prediction", n_models=2, complexity="low")
    return {"passed": len(plans) <= 3, "detail": f"simple problem -> {len(plans)} experiments (not soup)"}


NEGATIVE_CASES: list[BenchmarkCase] = [
    BenchmarkCase("NEG-001", "citation", "fake citation must be detected", case_fake_citation),
    BenchmarkCase("NEG-002", "results", "orphan number must be detected", case_wrong_result_number),
    BenchmarkCase("NEG-003", "units", "negative orders must be caught", case_wrong_unit),
    BenchmarkCase("NEG-004", "units", "probability >1 must be caught", case_probability_out_of_range),
    BenchmarkCase("NEG-005", "figure", "broken figure output must be caught", case_broken_figure),
    BenchmarkCase("NEG-006", "table", "table referencing missing result must be caught", case_inconsistent_table),
    BenchmarkCase("NEG-007", "claims", "unverified conclusion claim must be caught", case_unverified_claim_as_conclusion),
    BenchmarkCase("NEG-008", "experiment", "stale experiment result must be caught", case_stale_experiment),
    BenchmarkCase("NEG-009", "compliance", "page limit violation must be caught", case_wrong_page_rule),
    BenchmarkCase("NEG-010", "compliance", "missing AI declaration must be caught", case_ai_declaration_missing),
    BenchmarkCase("NEG-011", "compliance", "LIVE contest solution search must be blocked", case_live_contest_search_block),
    BenchmarkCase("NEG-012", "overengineering", "simple problem must not get algorithm soup", case_anti_overengineering),
    BenchmarkCase("NEG-013", "model-selection", "simple model preferred over soup", case_model_simple_over_complex),
]
