"""End-to-end smoke projects (Rule 140).

Smoke A: CUMCM-style training task — full chain with CUMCM profile + AI usage.
Smoke B: MCM/ICM-style task — different profile, English-oriented, different
page/section rules. Proves the system is not hardcoded for one competition.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

from .. import atomic
from ..competition import (
    append_usage,
    build_profile,
    detect_competition,
    generate_ai_report,
    save_profile,
)
from ..paths import ProjectPaths
from ..schemas import (
    AIUsageRecord,
    CompetitionMode,
    Experiment,
    ExperimentStatus,
    Result,
    Source,
    SourceVerification,
)
from ..verify import research_verify


def _synthetic_data(pp: ProjectPaths, seed: int = 7) -> str:
    raw = pp.data_raw / "input.csv"
    rng = __import__("random").Random(seed)
    n = 60
    with raw.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "y"])
        for t in range(n):
            w.writerow([t, round(10 + 0.3 * t + 2 * math.sin(t / 4) + rng.gauss(0, 0.5), 3)])
    import hashlib
    return hashlib.sha256(raw.read_bytes()).hexdigest()


def _fill_ledgers(pp: ProjectPaths, data_hash: str) -> None:
    atomic.append_jsonl(pp.experiments_path, Experiment(
        run_id="E-001", model="linear-trend", dataset_hash=data_hash, code_hash="smoke",
        metrics={"mae": 0.31}, status=ExperimentStatus.completed).model_dump(mode="json"))
    atomic.append_jsonl(pp.results_path, Result(
        result_id="R-001", name="MAE", value="0.31", unit="units",
        source_data_hash=data_hash, run_id="E-001", verified=True).model_dump(mode="json"))
    atomic.append_jsonl(pp.sources_path, Source(
        source_id="S-001", title="Smoke reference", year=2009, doi="10.1000/example",
        metadata_verified=True, content_verified=True,
        verification=SourceVerification.claim_verified).model_dump(mode="json"))


def smoke_a_cumcm() -> dict:
    """CUMCM-style training task: forecasting with a Chinese contest profile."""
    root = Path(".") / ".build" / "bench" / "smoke-a-cumcm"
    pp = ProjectPaths(root=root)
    pp.ensure_dirs()
    data_hash = _synthetic_data(pp)

    det = detect_competition("全国大学生数学建模竞赛 C 题 预测", live=False)
    profile = build_profile(det)
    save_profile(pp, profile)
    assert profile.competition == "cumcm", profile.competition
    assert profile.language == "zh"

    _fill_ledgers(pp, data_hash)

    # AI usage ledger + report (Rule 7) — generated from real records.
    append_usage(pp, AIUsageRecord(
        tool="ommw-agent", task="smoke-A-modeling", purpose="linear trend baseline",
        input_category="processed_data", output_category="result",
        verification_method="executed-test", accepted=True, human_review=True))
    decl, detail = generate_ai_report(pp)
    assert "AI" in decl and pp.paper_dir.joinpath("ai-usage-declaration.md").exists()

    rep = research_verify(pp)
    return {"passed": rep.passed, "detail": f"CUMCM smoke: verify={'PASS' if rep.passed else 'FAIL'}"}


def smoke_b_mcm() -> dict:
    """MCM/ICM-style task: evaluation problem, English profile, different rules."""
    root = Path(".") / ".build" / "bench" / "smoke-b-mcm"
    pp = ProjectPaths(root=root)
    pp.ensure_dirs()
    data_hash = _synthetic_data(pp)

    det = detect_competition("MCM Problem C evaluation", live=True)
    profile = build_profile(det)
    profile.anonymization_rule = "no personal info"  # MCM-specific
    save_profile(pp, profile)
    assert profile.competition == "mcm_icm", profile.competition
    assert profile.language == "en"
    assert profile.mode == CompetitionMode.live

    _fill_ledgers(pp, data_hash)
    # LIVE: AI usage must still be logged.
    append_usage(pp, AIUsageRecord(
        tool="ommw-agent", task="smoke-B-eval", purpose="evaluation baseline",
        input_category="processed_data", output_category="result",
        verification_method="executed-test", accepted=True, human_review=False))
    generate_ai_report(pp)

    rep = research_verify(pp)
    return {"passed": rep.passed, "detail": f"MCM smoke: verify={'PASS' if rep.passed else 'FAIL'}"}


def all_smoke_projects() -> list:
    from .runner import BenchmarkCase
    return [
        BenchmarkCase("SMOKE-A", "cumcm", "CUMCM-style full-chain training task", smoke_a_cumcm),
        BenchmarkCase("SMOKE-B", "mcm_icm", "MCM/ICM-style full-chain live task", smoke_b_mcm),
    ]
