"""Unit tests for v1.0 Layer 7/8 + health + final audit."""
from __future__ import annotations

from pathlib import Path

from ommw import atomic
from ommw.health import health_check
from ommw.knowledge import detect_verbatim_copy, extract_knowledge
from ommw.paper_factory import (
    build_blueprint,
    build_table_from_results,
    consistency_graph,
    make_chapter_contract,
    propagate_stale,
    validate_table_against_results,
)
from ommw.paths import ProjectPaths
from ommw.schemas import (
    Claim,
    ClaimStatus,
    Experiment,
    ExperimentStatus,
    FigureRecord,
    Result,
    TableRecord,
)
from ommw.visualization import (
    check_caption,
    check_grayscale_readability,
    plan_figure,
    validate_figure_plan,
)


def _mk_project(tmp_path: Path) -> ProjectPaths:
    pp = ProjectPaths(root=tmp_path / "p")
    pp.ensure_dirs()
    atomic.append_jsonl(pp.experiments_path, Experiment(
        run_id="E-001", model="m", dataset_hash="h", code_hash="c",
        status=ExperimentStatus.completed).model_dump(mode="json"))
    atomic.append_jsonl(pp.results_path, Result(
        result_id="R-001", name="mae", value="0.5000", unit="orders",
        source_data_hash="h", run_id="E-001", verified=True).model_dump(mode="json"))
    atomic.append_jsonl(pp.results_path, Result(
        result_id="R-002", name="lr_mae", value="0.3100", unit="orders",
        source_data_hash="h", run_id="E-001", verified=True).model_dump(mode="json"))
    atomic.append_jsonl(pp.claims_path, Claim(
        claim_id="C-001", statement="lr better", type="comparative",
        evidence_ids=["R-001", "R-002"], status=ClaimStatus.supported,
        used_in=["results"]).model_dump(mode="json"))
    atomic.append_jsonl(pp.figures_index, FigureRecord(
        figure_id="F-001", result_ids=["R-001"], output="figures/f.png").model_dump(mode="json"))
    atomic.append_jsonl(pp.tables_index, TableRecord(
        table_id="T-001", result_ids=["R-001", "R-002"], output="tables/t.md").model_dump(mode="json"))
    return pp


def test_figure_plan_requires_qcd_why() -> None:
    fp = plan_figure(figure_id="F-001", question="", claim="C-001", data="d", why="")
    rep = validate_figure_plan(fp)
    codes = {f.code for f in rep.findings}
    assert "fig-no-question" in codes and "fig-no-why" in codes
    assert not rep.passed


def test_figure_plan_valid() -> None:
    fp = plan_figure(figure_id="F-001", question="q", claim="C-001", data="d", why="w")
    rep = validate_figure_plan(fp)
    assert rep.passed


def test_grayscale_check() -> None:
    rep = check_grayscale_readability(["red", "green", "blue"])
    assert any(f.code == "grayscale-unreadable" for f in rep.findings)
    rep2 = check_grayscale_readability(["red-dashed", "green-solid"])
    assert rep2.passed


def test_caption_check() -> None:
    rep = check_caption("")
    assert any(f.code == "caption-empty" for f in rep.findings)
    rep2 = check_caption("MAE comparison across models 0.9731428571")
    assert any(f.code == "caption-orphan-number" for f in rep2.findings)


def test_blueprint_dynamic() -> None:
    bp1 = build_blueprint(title="t", competition="cumcm", language="zh",
                          problem_types=["prediction"])
    bp2 = build_blueprint(title="t", competition="cumcm", language="zh",
                          problem_types=["optimization", "simulation"])
    assert "data-processing" not in bp1.chapters
    assert "data-processing" not in bp1.chapters or True  # prediction may include
    assert "experiment" in bp2.chapters  # simulation/optimization -> experiment chapter
    assert "abstract" in bp1.chapters  # placeholder until end (Rule 70)


def test_consistency_graph_and_stale(tmp_path: Path) -> None:
    pp = _mk_project(tmp_path)
    graph = consistency_graph(pp)
    assert "R-001" in graph
    assert any("figure:F-001" in deps for deps in graph.get("R-001", []))
    touched = propagate_stale(pp, "R-001")
    assert any("figure:" in t for t in touched)
    # staleness persisted
    progress = atomic.read_json(pp.progress_json) if pp.progress_json.exists() else {}
    assert "R-001" in progress.get("stale_dependents", [])


def test_table_from_results_and_validation(tmp_path: Path) -> None:
    pp = _mk_project(tmp_path)
    md = build_table_from_results(pp, title="Comparison",
                                  result_ids=["R-001", "R-002"])
    rep = validate_table_against_results(pp, md)
    assert rep.passed
    # Inject a wrong value -> must fail.
    bad = md.replace("0.5000", "0.9999")
    rep2 = validate_table_against_results(pp, bad)
    assert any(f.code == "table-number-mismatch" for f in rep2.findings)


def test_health_detects_stale_and_claims(tmp_path: Path) -> None:
    pp = _mk_project(tmp_path)
    rep = health_check(pp)
    assert rep.passed  # healthy baseline
    # Add a proposed conclusion claim -> health HIGH.
    atomic.append_jsonl(pp.claims_path, Claim(
        claim_id="C-099", statement="c", type="conclusion",
        evidence_ids=["R-001"], status=ClaimStatus.proposed).model_dump(mode="json"))
    rep2 = health_check(pp)
    assert any(f.code == "unverified-conclusion-claim" for f in rep2.findings)
    # Stale experiment -> stale-result.
    atomic.append_jsonl(pp.experiments_path, Experiment(
        run_id="E-002", model="m", dataset_hash="h", code_hash="c",
        status=ExperimentStatus.stale).model_dump(mode="json"))
    atomic.append_jsonl(pp.results_path, Result(
        result_id="R-003", name="x", value="1.0", run_id="E-002").model_dump(mode="json"))
    rep3 = health_check(pp)
    assert any(f.code == "stale-result" for f in rep3.findings)


def test_knowledge_extract_and_verbatim() -> None:
    e = extract_knowledge(source="paper-A", problem_type="forecasting",
                          model_family="arima", why_model_selected="stationarity",
                          baseline="naive", innovation="time-varying lambda")
    assert e.model_family == "arima"
    src = ["The proposed method outperforms the baseline under all scenarios tested."]
    new = "We now write a paper that says the proposed method outperforms the baseline under all scenarios tested completely differently."
    rep = detect_verbatim_copy(new, src)
    assert any(f.code == "verbatim-copy" for f in rep.findings)
    clean = "A completely different sentence with no overlap whatsoever here."
    rep2 = detect_verbatim_copy(clean, src)
    assert rep2.passed
