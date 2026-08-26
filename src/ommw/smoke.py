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
import time
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

    dest = Path(dest)
    # Sandbox-safe isolation: a stale run directory would pollute this run
    # with outdated chapter files (glob-based gates scan everything under
    # sections/). Deleting is fail-closed in the sandbox, so we ARCHIVE the
    # previous run by rename (a move, not a delete) into a .prev-* sibling.
    if dest.exists() and any(dest.iterdir()):
        bak = dest.parent / f"{dest.name}.prev-{time.strftime('%Y%m%d-%H%M%S')}"
        if not bak.exists():
            try:
                dest.rename(bak)
            except OSError:
                pass  # fall through; run will overwrite in place
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

    # 10. chapter content (shared Research Core -> both renderers).
    # v0.2: the smoke project IS a minimal *complete* paper -- every seeded
    # section carries real content so the new Paper Production Gates pass
    # POSITIVELY, while injected negatives below prove they catch failures.
    abstract_md = (
        "# Abstract\n\n"
        "City-delivery demand is forecast for a 30-day horizon to compare a "
        "mean-baseline predictor against a least-squares linear trend model. "
        "The linear trend reaches an MAE of R-002 orders versus R-001 orders "
        "for the baseline, a relative improvement of R-003 percent (claim "
        "C-001, supported by source S-001). Model form and parameters are given "
        "in Section models; Figure F-001 and table T-001 summarize accuracy. "
        "A sensitivity note on the stationarity assumption A-001 closes the "
        "paper.\n\n"
        "**Keywords:** demand forecasting; linear regression; MAE; baseline\n"
    )
    abstract_tex = (
        "\\section*{Abstract}\n"
        "City-delivery demand is forecast for a 30-day horizon to compare a\n"
        "mean-baseline predictor against a least-squares linear trend model.\n"
        "The linear trend reaches an MAE of R-002 orders versus R-001 orders\n"
        "for the baseline, a relative improvement of R-003 percent (claim\n"
        "C-001, supported by source S-001). Model form and parameters are\n"
        "given in the models section; Figure F-001 and table T-001 summarize\n"
        "accuracy. A sensitivity note on assumption A-001 closes the paper.\n\n"
        "\\medskip\\noindent\\textbf{Keywords:} demand forecasting; linear "
        "regression; MAE; baseline\n"
    )
    models_md = (
        "# Models\n\n"
        "Let $d_t$ be demand on day $t$. Baseline predicts the global mean;\n"
        "the trend model is fitted by least squares:\n"
        "\n"
        "$$\n"
        "\\hat{d}_t = \\beta_0 + \\beta_1 t\n"
        "$$\n"
        "\n"
        "with closed-form estimators\n"
        "\n"
        "$$\n"
        "\\hat{\\beta}_1 = \\frac{n\\sum t d_t - \\sum t \\sum d_t}"
        "{n\\sum t^2 - (\\sum t)^2}\n"
        "$$\n"
        "\n"
        "Parameters are summarized in table T-002; accuracy metrics use the\n"
        "mean absolute error $\\mathrm{MAE}$ defined in the results section.\n\n"
        "| Parameter | Meaning | Value type |\n|---|---|---|\n"
        "| beta0 | intercept | estimated |\n| beta1 | slope | estimated |\n"
    )
    models_tex = (
        "\\section{Models}\n"
        "Let $d_t$ denote demand on day $t$. The baseline predicts the global\n"
        "mean; the trend model fitted by least squares is\n"
        "\\begin{equation}\n\\hat{d}_t = \\beta_0 + \\beta_1 t\n"
        "\\label{eq:trend}\\end{equation}\n"
        "with closed-form estimators\n"
        "\\begin{equation}\n\\hat{\\beta}_1 = \\frac{n\\sum t d_t - "
        "\\sum t \\sum d_t}{n\\sum t^2 - (\\sum t)^2}\n"
        "\\label{eq:slope}\\end{equation}\n"
        "Fitted parameters are listed in Table~\\ref{tab:params}; both are\n"
        "evaluated with the mean absolute error metric of Eq.~\\eqref{eq:mae}.\n\n"
        "\\begin{table}[htbp]\\centering\n"
        "\\caption{Estimated model parameters (T-002)}\n"
        "\\label{tab:params}\n"
        "\\begin{tabular}{lll}\nParameter & Meaning & Type \\\\\n"
        "$\\beta_0$ & intercept & estimated \\\\\n"
        "$\\beta_1$ & slope & estimated \\\\\n"
        "\\end{tabular}\\end{table}\n"
    )
    chapter_md = (
        "# Results\n\n"
        "The linear regression model achieves a mean absolute error of R-002 "
        "orders, versus R-001 orders for the mean baseline, a relative improvement "
        "of R-003 (claim C-001, supported by source S-001):\n\n"
        "$$\n"
        "\\mathrm{MAE}(\\hat{d}) = \\frac{1}{n}\\sum_{t=1}^{n}|\\hat{d}_t - d_t|\n"
        "$$\n\n"
        "Figure~F-001 plots baseline versus regression forecasts; its most\n"
        "important pattern is that the trend tracks the weekly oscillation\n"
        "while the flat baseline lags demand growth, which matters because it\n"
        "explains the MAE gap in table T-001. The comparison therefore supports\n"
        "conclusion C-001.\n\n"
        "| Model | MAE (orders) |\n|---|---|\n| Baseline | R-001 |\n| Linear regression | R-002 |\n\n"
        "![Baseline vs regression forecast](../figures/forecast.png)\n\n"
        "Forecast comparison figure F-001 shows the trend line following the\n"
        "weekly cycle; see table T-001 for the numeric summary.\n"
    )
    chapter_tex = (
        r"\section{Results}" "\n"
        r"The linear regression model achieves a mean absolute error of R-002 "
        r"orders, versus R-001 orders for the mean baseline, a relative improvement "
        r"of R-003 (claim C-001, supported by source S-001):" "\n"
        r"\begin{equation}" "\n"
        r"\mathrm{MAE}(\hat{d}) = \frac{1}{n}\sum_{t=1}^{n}|\hat{d}_t - d_t|" "\n"
        r"\label{eq:mae}\end{equation}" "\n\n"
        r"Figure~\ref{fig:forecast} (F-001) plots baseline versus regression "
        r"forecasts. Its most important pattern is that the trend tracks the "
        r"weekly oscillation while the flat baseline lags demand growth, which "
        r"matters because it explains the MAE gap in Table~\ref{tab:cmp} (T-001). "
        r"The comparison therefore supports conclusion C-001." "\n\n"
        r"\begin{table}[htbp]\centering\caption{Model comparison (T-001)}"
        r"\label{tab:cmp}\begin{tabular}{ll}"
        r"Model & MAE \\ Baseline & R-001 \\ Linear regression & R-002 \\\end{tabular}\end{table}" "\n\n"
        r"\begin{figure}[htbp]\centering"
        r"\includegraphics[width=.7\linewidth]{figures/forecast.png}"
        r"\caption{Baseline vs regression forecast (F-001)}"
        r"\label{fig:forecast}\end{figure}" "\n"
    )
    # figure file must exist BOTH at project root (registry path) and under
    # latex/figures (compile-time path resolution).
    _write_minimal_png(pp.figures_dir / "forecast.png")
    _write_minimal_png(pp.latex_dir / "figures" / "forecast.png")
    atomic.append_jsonl(pp.figures_index, FigureRecord(
        figure_id="F-001", generator="code/smoke_inline.py", data=str(raw_csv),
        result_ids=["R-001", "R-002"], caption="Baseline vs regression forecast",
        section="results", output="figures/forecast.png").model_dump(mode="json"))
    atomic.append_jsonl(pp.tables_index, TableRecord(
        table_id="T-001", generator="code/smoke_inline.py", data=str(processed),
        result_ids=["R-001", "R-002", "R-003"], section="results",
        caption="Model comparison").model_dump(mode="json"))
    atomic.append_jsonl(pp.tables_index, TableRecord(
        table_id="T-002", generator="code/smoke_inline.py", data=str(processed),
        result_ids=[], section="models",
        caption="Estimated model parameters").model_dump(mode="json"))

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

    for fname, body in (("abstract", (abstract_md, abstract_tex)),
                        ("models", (models_md, models_tex)),
                        ("results", (chapter_md, chapter_tex))):
        (pp.word_dir / "sections" / f"{fname}.md").write_text(body[0], encoding="utf-8")
        (pp.latex_dir / "sections" / f"{fname}.tex").write_text(body[1], encoding="utf-8")
    # main.tex for latex compile (minimal, CJK-safe engine chosen by renderer)
    (pp.latex_dir / "main.tex").write_text(
        r"\documentclass{article}" "\n"
        r"\usepackage{graphicx,amsmath}" "\n"
        r"\title{Smoke Test Paper}" r"\author{OMMW}" "\n"
        r"\begin{document}\maketitle" "\n"
        r"\input{sections/abstract}" "\n"
        r"\input{sections/models}" "\n"
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

    # 13b. v0.2 Paper Production Gates on the POSITIVE project: every gate
    # must pass (no CRITICAL/HIGH) -- this is what demo4 could not do.
    from .paper import run_all_paper_gates
    gate_reps = run_all_paper_gates(pp)
    gates_ok = all(r.passed for r in gate_reps.values())
    gate_fails = {g: [f.code for f in r.findings if f.severity in ("CRITICAL", "HIGH")]
                  for g, r in gate_reps.items() if not r.passed}

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
    print(f"  paper gates: {'ALL PASS' if gates_ok else 'FAIL ' + str(gate_fails)}")
    print(f"  latex: {'OK' if lr.ok else 'DEGRADED'} ({lr.degraded or lr.errors[:1]})")
    print(f"  word:  structural={wr.structural_qa} visual={wr.visual_qa} ({wr.degraded})")
    print(f"  parity: {'PASS' if parity_ok else 'MISMATCH'}")
    print(f"  negative-case detection: {'ALL CAUGHT' if neg_ok else 'MISSED'}")
    all_ok = rep.passed and neg_ok and parity_ok and gates_ok
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

    # (d) v0.2: abstract removed from BOTH renderers -> ABSTRACT_MISSING
    # (CRITICAL) MUST fire. A missing abstract in every format is exactly the
    # demo4 failure class.
    abs_path = pp.latex_dir / "sections" / "abstract.tex"
    wabs_path = pp.word_dir / "sections" / "abstract.md"
    saved_abstract = abs_path.read_text(encoding="utf-8")
    saved_wabs = wabs_path.read_text(encoding="utf-8")
    from .paper.gates import abstract_gate
    try:
        abs_path.write_text("% abstract -- placeholder\n", encoding="utf-8")
        wabs_path.write_text("<!-- placeholder -->\n", encoding="utf-8")
        arep = abstract_gate(pp)
        caught_d = any(f.code == "ABSTRACT_MISSING" for f in arep.findings)
    finally:
        abs_path.write_text(saved_abstract, encoding="utf-8")
        wabs_path.write_text(saved_wabs, encoding="utf-8")
    ok &= caught_d

    # (e) v0.2: stub a REAL chapter -> stub-section (research_verify) AND
    # PLACEHOLDER_SECTION / VISUAL_EVIDENCE_INSUFFICIENT (paper gates) MUST fire.
    # We stub models.tex (always present in the positive project) and RESTORE
    # it afterwards -- no file is ever created-then-deleted, because unlink is
    # fail-closed in the sandbox and would leave stale stubs behind.
    stub = pp.latex_dir / "sections" / "models.tex"
    saved_stub = stub.read_text(encoding="utf-8")
    stub.write_text("% models -- placeholder. Evidence required before prose.\n",
                    encoding="utf-8")
    try:
        srep = research_verify(pp)
        caught_e1 = any(f.code == "stub-section" and "models" in f.location
                        for f in srep.findings)
        from .paper import run_all_paper_gates
        greps = run_all_paper_gates(pp)
        codes = {f.code for r in greps.values() for f in r.findings}
        caught_e2 = ("PLACEHOLDER_SECTION" in codes
                     or "VISUAL_EVIDENCE_INSUFFICIENT" in codes)
    finally:
        stub.write_text(saved_stub, encoding="utf-8")
    ok &= caught_e1 and caught_e2

    return ok


def _write_minimal_png(path) -> None:
    """Write a real minimal PNG (1x1 gray) using stdlib zlib+struct.

    Generates an actual image file so figure-registry gates are exercised
    honestly without requiring matplotlib.
    """
    import struct
    import zlib

    def _chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0)  # 1x1 grayscale 8-bit
    idat = zlib.compress(b"\x00\x80")  # filter byte 0 + one gray pixel
    png = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
           + _chunk(b"IDAT", idat) + _chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)

