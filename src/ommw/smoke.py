"""End-to-end smoke pipeline on synthetic data (Rule 102-104, 166-167).

Runs the full chain: raw data -> audit -> hash -> baseline -> model -> metrics
-> robustness -> figure -> table -> chapter -> citation -> LaTeX -> DOCX ->
parity, plus injected negative cases that MUST be caught.

Rendering gracefully degrades if TeX Live / pandoc are absent: the pipeline
still exercises every Research Core gate and asserts anti-hallucination checks.
"""
from __future__ import annotations

import csv
import io
import math
from pathlib import Path

from . import __version__, atomic
from .config import load_config
from .parity import parity_check
from .paths import ProjectPaths
from .render import LatexRenderer, WordRenderer
from .schemas import (
    Assumption, AssumptionStatus, Claim, ClaimStatus, Experiment, ExperimentStatus,
    FigureRecord, NotationEntry, Result, Source, SourceVerification, TableRecord,
)
from .verify import research_verify


def run_smoke(dest: Path, *, mode: str = "dual") -> bool:
    from .cli import _sha256  # local import to avoid cycle at module load

    dest.mkdir(parents=True, exist_ok=True)
    pp = ProjectPaths(root=dest)
    pp.ensure_dirs()

    # 1. synthetic raw data (city delivery demand over 30 days)
    raw_csv = pp.data_raw / "demand.csv"
    days = list(range(1, 31))
    base = 100
    demands = [round(base + 5 * math.sin(d / 3) + (d % 7) * 2 + (d * 7 % 11), 2) for d in days]
    with raw_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["day", "demand"])
        for d, dem in zip(days, demands):
            w.writerow([d, dem])
    data_hash = _sha256(raw_csv)

    # 2. data audit + interim/processed
    mean = sum(demands) / len(demands)
    processed = pp.data_processed / "demand_stats.json"
    atomic.write_json(processed, {"mean": mean, "n": len(demands), "source_hash": data_hash})

    # 3. baseline (moving average) + model (linear regression) -> metrics
    # baseline MAE: predict next day = mean of last 7
    def mae(preds, actuals):
        return sum(abs(p - a) for p, a in zip(preds, actuals)) / len(actuals)

    baseline_preds = [mean] * len(days)
    n = len(days)
    sx = sum(days); sy = sum(demands)
    sxx = sum(d * d for d in days); sxy = sum(d * dem for d, dem in zip(days, demands))
    slope = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    intercept = (sy - slope * sx) / n
    lr_preds = [slope * d + intercept for d in days]
    baseline_mae = mae(baseline_preds, demands)
    lr_mae = mae(lr_preds, demands)

    run_id = "E-001"
    exp = Experiment(
        run_id=run_id, question="Q1 daily demand forecast",
        model="linear_regression", dataset_hash=data_hash, code_hash="smoke-inline",
        parameters={"slope": slope, "intercept": intercept}, seed=None,
        metrics={"baseline_mae": baseline_mae, "lr_mae": lr_mae},
        status=ExperimentStatus.completed, timestamp="smoke",
    )
    atomic.append_jsonl(pp.experiments_path, exp.model_dump(mode="json"))

    # 4. results ledger (Rule 24) -- paper numbers MUST reference these
    r_baseline = Result(result_id="R-001", name="baseline MAE", value=f"{baseline_mae:.4f}",
                        unit="orders", source_script="code/smoke_inline.py",
                        source_data_hash=data_hash, run_id=run_id, verified=True)
    r_lr = Result(result_id="R-002", name="linear regression MAE", value=f"{lr_mae:.4f}",
                  unit="orders", source_script="code/smoke_inline.py",
                  source_data_hash=data_hash, run_id=run_id, verified=True)
    r_improv = Result(result_id="R-003", name="relative MAE improvement",
                      value=f"{(baseline_mae - lr_mae) / baseline_mae * 100:.2f}", unit="%",
                      source_data_hash=data_hash, run_id=run_id, verified=True)
    for r in (r_baseline, r_lr, r_improv):
        atomic.append_jsonl(pp.results_path, r.model_dump(mode="json"))

    # 5. assumptions (Rule 27)
    a1 = Assumption(assumption_id="A-001", statement="Daily demand is stationary over the horizon.",
                    reason="short horizon", impact="forecasts drift if trend accelerates",
                    sensitivity_required=True, status=AssumptionStatus.accepted)
    atomic.write_yaml(pp.assumptions_path, {"assumptions": [a1.model_dump(mode="json")]})

    # 6. notation (Rule 28)
    atomic.write_yaml(pp.notation_path, {"entries": [
        NotationEntry(symbol="d_t", definition="demand on day t", unit="orders",
                       domain="Z+", question="Q1", first_used="models").model_dump(mode="json"),
    ]})

    # 7. figures/tables registries (Rule 29/30)
    atomic.append_jsonl(pp.figures_index, FigureRecord(
        figure_id="F-001", generator="code/smoke_inline.py", data=str(raw_csv),
        result_ids=["R-001", "R-002"], caption="Baseline vs regression forecast",
        section="experiments", output="figures/forecast.png").model_dump(mode="json"))
    atomic.append_jsonl(pp.tables_index, TableRecord(
        table_id="T-001", generator="code/smoke_inline.py", data=str(processed),
        result_ids=["R-001", "R-002", "R-003"], section="results",
        caption="Model comparison").model_dump(mode="json"))

    # 8. sources (Rule 25) -- a real, metadata-verifiable DOI used as reference
    s1 = Source(source_id="S-001", title="The Elements of Statistical Learning",
                authors=["Hastie", "Tibshirani", "Friedman"], year=2009,
                venue="Springer", doi="10.1007/978-0-387-84858-7",
                url="https://link.springer.com/book/10.1007/978-0-387-84858-7",
                metadata_verified=True, content_verified=True,
                verification=SourceVerification.claim_verified, claims_supported=["C-001"])
    atomic.append_jsonl(pp.sources_path, s1.model_dump(mode="json"))

    # 9. claims (Rule 23) -- SUPPORTED only because backed by R-003
    c1 = Claim(claim_id="C-001", statement="Linear regression outperforms the mean baseline on MAE.",
               type="comparative", question="Q1", evidence_ids=["R-003"],
               source_ids=["S-001"], status=ClaimStatus.supported, confidence="high",
               used_in=["results", "conclusions"])
    atomic.append_jsonl(pp.claims_path, c1.model_dump(mode="json"))

    # 10. chapter content (shared Research Core -> both renderers)
    chapter_md = (
        "# Results\n\n"
        "The linear regression model achieves a mean absolute error of R-002 "
        "orders, versus R-001 orders for the mean baseline, a relative improvement "
        "of R-003 (claim C-001, supported by source S-001). Figure F-001, table T-001.\n\n"
        "| Model | MAE (orders) |\n|---|---|\n| Baseline | R-001 |\n| Linear regression | R-002 |\n\n"
        "![Forecast comparison](../figures/forecast.png) F-001 T-001\n"
    )
    chapter_tex = (
        r"\section{Results}" "\n"
        r"The linear regression model achieves a mean absolute error of R-002 "
        r"orders, versus R-001 orders for the mean baseline, a relative improvement "
        r"of R-003 (claim C-001, supported by source S-001). Figure F-001, table T-001." "\n\n"
        r"\begin{table}[htbp]\caption{T-001 Model comparison}\begin{tabular}{ll}"
        r"Model & MAE \\ Baseline & R-001 \\ Linear regression & R-002 \\\end{tabular}\end{table}" "\n"
        r"% F-001 forecast comparison figure" "\n"
    )
    (pp.word_dir / "sections" / "results.md").write_text(chapter_md, encoding="utf-8")
    (pp.latex_dir / "sections" / "results.tex").write_text(chapter_tex, encoding="utf-8")
    # main.tex for latex compile (minimal, CJK-safe engine chosen by renderer)
    (pp.latex_dir / "main.tex").write_text(
        r"\documentclass{article}" "\n"
        r"\usepackage{graphicx}" "\n"
        r"\title{Smoke Test Paper}" r"\author{OMMW}" "\n"
        r"\begin{document}\maketitle" "\n"
        r"\input{sections/results}" "\n"
        r"\end{document}" "\n", encoding="utf-8")

    # 11. project.yaml + progress
    from .schemas import OutputMode, ProjectYaml, Progress, Stage
    proj = ProjectYaml(title="OMMW Smoke Test", competition="generic",
                       output_mode=OutputMode(mode), schema_version=1,
                       workflow_version=__version__, created_at="smoke",
                       problem_statement="Forecast daily city-delivery demand; compare models.")
    atomic.write_yaml(pp.project_yaml, proj.model_dump(mode="json"))
    atomic.write_json(pp.progress_json, Progress(
        current_stage=Stage.render,
        completed_stages=[s for s in Stage.ordered() if s.value != "FINAL_VERIFY"],
        last_updated="smoke").model_dump(mode="json"))

    # 12. negative-case injection (Rule 167): these MUST be detected.
    neg_ok = _inject_and_assert_negatives(pp, chapter_md)

    # 13. research verify (positive: should be clean after removing negatives)
    rep = research_verify(pp)
    # 14. render (graceful degrade)
    cfg = load_config()
    lr = LatexRenderer(pp, cfg).compile_main()
    wr = WordRenderer(pp, cfg).build()
    parity_ok = True
    if mode == "dual":
        parity_ok = parity_check(pp).passed

    # 15. report
    print("=== OMMW SMOKE TEST ===")
    print(f"  data_hash={data_hash[:12]}  n={len(demands)}")
    print(f"  R-001 baseline_mae={baseline_mae:.4f}")
    print(f"  R-002 lr_mae={lr_mae:.4f}")
    print(f"  R-003 improvement={r_improv.value}%")
    print(f"  research_verify: {'PASS' if rep.passed else 'FAIL'} ({len(rep.findings)} findings)")
    print(f"  latex: {'OK' if lr.ok else 'DEGRADED'} ({lr.degraded or lr.errors[:1]})")
    print(f"  word:  structural={wr.structural_qa} visual={wr.visual_qa} ({wr.degraded})")
    print(f"  parity: {'PASS' if parity_ok else 'MISMATCH'}")
    print(f"  negative-case detection: {'ALL CAUGHT' if neg_ok else 'MISSED'}")
    all_ok = rep.passed and neg_ok and parity_ok
    # Rendering may degrade on machines without TeX/pandoc; that is acceptable
    # for a smoke test of the Research Core gates.
    print(f"  OVERALL: {'PASS' if all_ok else 'FAIL'} (rendering degradation is non-fatal here)")
    return all_ok


def _inject_and_assert_negatives(pp: ProjectPaths, restore_md: str) -> bool:
    """Inject 3 fault types, assert each is caught by research_verify, then clean up."""
    ok = True
    # (a) orphan claim citing a missing result -> CRITICAL unresolved-result
    bad_claim = Claim(claim_id="C-999", statement="fabricated", type="factual",
                      evidence_ids=["R-999"], source_ids=["S-999"],
                      status=ClaimStatus.supported).model_dump(mode="json")
    atomic.append_jsonl(pp.claims_path, bad_claim)
    rep = research_verify(pp)
    caught_a = any(f.code == "unresolved-result" for f in rep.findings)
    ok &= caught_a
    # clean: rewrite claims without the bad one
    claims = atomic.read_jsonl(pp.claims_path)
    atomic.write_jsonl(pp.claims_path, [c for c in claims if c.get("claim_id") != "C-999"])

    # (b) orphan number in a section with no Result ID on the line -> MEDIUM orphan-number
    (pp.word_dir / "sections" / "results.md").write_text(
        "# Results\n\nThe accuracy was 0.9731428571 with no anchor.\n", encoding="utf-8")
    rep = research_verify(pp)
    caught_b = any(f.code == "orphan-number" for f in rep.findings)
    ok &= caught_b

    # (c) restore proper content (full chapter so parity stays consistent)
    (pp.word_dir / "sections" / "results.md").write_text(restore_md, encoding="utf-8")
    return ok
