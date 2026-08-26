"""Runner for the paper-production regression evals (spec §50-§56).

Builds a canonical minimal-but-complete base project (the same shape the
smoke test seeds), applies one mutation per case, runs every Paper Production
Gate, and asserts expectations declared in ``cases.yaml``.

Exit code 0 only when EVERY case matches. The report lands in
``evals/paper-production/eval-report.json`` plus a human-readable
``eval-report.md``.

Usage:
    python src/../evals/paper-production/run_evals.py [--workdir DIR]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]                      # evals/paper-production -> repo root
sys.path.insert(0, str(ROOT / "src"))

from ommw.paths import ProjectPaths  # noqa: E402
from ommw.paper.gates import has_critical, run_all_paper_gates  # noqa: E402

# --------------------------------------------------------------------------
# base project: minimal COMPLETE paper (mirrors ommw.smoke seeding)
# --------------------------------------------------------------------------

_MIN_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6260000000060005"
    "27de4bb90000000049454e44ae426082")

ABSTRACT_TEX = """\\section*{Abstract}
City-delivery demand is forecast over a 30-day horizon to compare a
mean-baseline predictor against a least-squares linear trend model.
The linear trend reaches an MAE of R-002 orders versus R-001 orders for
the baseline, a relative improvement of R-003 percent (claim C-001,
supported by source S-001). Model form and fitted parameters are given in
the models section; Figure F-001 and table T-001 summarize predictive
accuracy, and a sensitivity note on assumption A-001 closes the paper.

\\medskip\\noindent\\textbf{Keywords:} demand forecasting; linear regression; MAE
"""

MODELS_TEX = """\\section{Models}
Let $d_t$ denote demand on day $t$, the quantity the city operations team
must anticipate for every morning dispatch round. The naive baseline
predicts the global mean demand observed so far, which ignores both level
shifts and weekly seasonality; the proposed model is a least-squares
linear trend fitted on the trailing window, written as
\\begin{equation}\\hat{d}_t = \\beta_0 + \\beta_1 t\\label{eq:trend}\\end{equation}
with closed-form estimators
\\begin{equation}\\hat{\\beta}_1 = \\frac{n\\sum t d_t - \\sum t \\sum d_t}"
"{n\\sum t^2 - (\\sum t)^2}\\label{eq:slope}\\end{equation}
The intercept $\\beta_0$ captures the demand level while the slope
$\\beta_1$ captures growth; both are estimated per rolling window and then
frozen for evaluation. Residuals are checked for autocorrelation before
the forecast is accepted, because a trend fitted on drifting data would
systematically undershoot peak days. Fitted parameters are listed in
Table~\\ref{tab:params}; scoring uses the mean absolute error metric
defined in Eq.~\\eqref{eq:mae} of the results chapter, which keeps model
selection and reporting on a single scale (see also T-002).

\\begin{table}[htbp]\\centering
\\caption{Estimated model parameters (T-002)}\\label{tab:params}
\\begin{tabular}{lll}Parameter & Meaning & Type \\\\
$\\beta_0$ & intercept & estimated \\\\
$\\beta_1$ & slope & estimated \\\\\\end{tabular}\\end{table}
"""

RESULTS_TEX = """\\section{Results}
The linear regression model achieves a mean absolute error of R-002 orders,
versus R-001 orders for the mean baseline, a relative improvement of R-003
percent (claim C-001, supported by source S-001):
\\begin{equation}\\mathrm{MAE}(\\hat{d}) = \\frac{1}{n}\\sum_{t=1}^{n}|\\hat{d}_t - d_t|
\\label{eq:mae}\\end{equation}

Figure~\\ref{fig:forecast} (F-001) plots baseline versus regression
forecasts across the 30-day horizon. Its most important pattern is that the
trend line tracks the weekly oscillation while the flat baseline lags
demand growth, which matters operationally because understaffed peak days
are precisely where the MAE gap in Table~\\ref{tab:cmp} (T-001) accumulates.
The comparison therefore supports conclusion C-001, and it answers the Q1
forecast question posed in the introduction.

\\begin{table}[htbp]\\centering\\caption{Model comparison (T-001)}\\label{tab:cmp}
\\begin{tabular}{ll}Model & MAE \\\\ Baseline & R-001 \\\\ Linear regression & R-002 \\\\
\\end{tabular}\\end{table}

\\begin{figure}[htbp]\\centering
\\includegraphics[width=.7\\linewidth]{figures/forecast.png}
\\caption{Baseline vs regression forecast (F-001)}\\label{fig:forecast}
\\end{figure}

The gain is robust to dropping the last week of data (R-003 varies by less
than two points), and the stationarity assumption A-001 is re-checked
before each deployment window.
"""

MD = {
    "abstract": "# Abstract\n\n" + ABSTRACT_TEX.replace("\\section*{Abstract}\n", "")
              .replace("\\medskip\\noindent", "").replace("\\textbf{Keywords:}", "**Keywords:**")
              .replace("\\", "") + "\n",
    "models": "# Models\n\nLet $d_t$ be demand on day $t$. Baseline predicts the global mean;\n"
              "the trend model is fitted by least squares:\n\n$$\n\\\\hat{d}_t = \\\\beta_0 + \\\\beta_1 t\n$$\n\n"
              "with closed-form estimators given in the LaTeX source; parameters are\n"
              "summarized in table T-002 and scored with the MAE metric of the results\nchapter.\n",
    "results": "# Results\n\nLinear regression reaches MAE R-002 orders versus R-001 baseline,\n"
               "an improvement of R-003 percent (C-001, S-001). Figure F-001 shows the\n"
               "trend tracking the weekly cycle while the baseline lags; see table T-001.\n\n"
               "![Baseline vs regression forecast](figures/forecast.png)\n",
}

MAIN_TEX = ("\\documentclass{article}\n"
            "\\usepackage{graphicx,amsmath}\n"
            "\\begin{document}\n"
            "\\input{sections/abstract.tex}\n\\input{sections/models.tex}\n"
            "\\input{sections/results.tex}\n\\end{document}\n")

NARRATIVE_MD = ("# Narrative backbone\n\nQ1 (forecast demand) feeds the staffing decision; "
                "models chapter derives eq:trend/eq:slope, results chapter scores them "
                "(eq:mae) against ledger experiments E-001 and reports R-001..R-003.\n")


def _write_base_project(dest: Path) -> ProjectPaths:
    pp = ProjectPaths(root=dest)
    pp.ensure_dirs()
    sec = pp.latex_dir / "sections"
    sec.mkdir(parents=True, exist_ok=True)
    (sec / "abstract.tex").write_text(ABSTRACT_TEX, encoding="utf-8")
    (sec / "models.tex").write_text(MODELS_TEX, encoding="utf-8")
    (sec / "results.tex").write_text(RESULTS_TEX, encoding="utf-8")
    wsec = pp.word_dir / "sections"
    wsec.mkdir(parents=True, exist_ok=True)
    for name, body in MD.items():
        (wsec / f"{name}.md").write_text(body, encoding="utf-8")
    (pp.latex_dir / "main.tex").write_text(MAIN_TEX, encoding="utf-8")
    (pp.latex_dir / "figures").mkdir(exist_ok=True)
    (pp.latex_dir / "figures" / "forecast.png").write_bytes(_MIN_PNG)

    def jl(path, rows):
        path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    jl(pp.results_path, [
        {"result_id": "R-001", "name": "baseline MAE", "value": "0.9123", "unit": "orders"},
        {"result_id": "R-002", "name": "linear regression MAE", "value": "0.7054", "unit": "orders"},
        {"result_id": "R-003", "name": "relative MAE improvement", "value": "22.68", "unit": "%"},
    ])
    jl(pp.experiments_path, [{
        "run_id": "E-001", "question": "Q1 daily demand forecast",
        "model": "linear_regression", "status": "completed",
        "metrics": {"baseline_mae": 0.9123, "lr_mae": 0.7054}, "timestamp": "eval"}])
    jl(pp.claims_path, [{"claim_id": "C-001", "type": "comparative",
                         "statement": "trend beats mean baseline",
                         "evidence_ids": ["R-001", "R-002", "R-003"]}])
    jl(pp.figures_index, [{"figure_id": "F-001", "path": "figures/forecast.png",
                           "section": "results", "caption": "forecast comparison"}])
    jl(pp.tables_index, [{"table_id": "T-001", "section": "results"},
                         {"table_id": "T-002", "section": "models"}])
    pp.notation_path.write_text(
        "entries:\n  - symbol: d_t\n    definition: demand on day t\n    unit: orders\n",
        encoding="utf-8")
    (pp.state_dir / "question-dependency-map.yaml").write_text(
        "dependencies:\n  - from: models\n    to: results\n", encoding="utf-8")
    (pp.state_dir / "paper-narrative.md").write_text(NARRATIVE_MD, encoding="utf-8")
    return pp


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


# --------------------------------------------------------------------------
# mutations: each returns a short note about what it damaged
# --------------------------------------------------------------------------

def m_drop_abstract(pp: ProjectPaths) -> str:
    (pp.latex_dir / "sections" / "abstract.tex").write_text("", encoding="utf-8")
    (pp.word_dir / "sections" / "abstract.md").write_text("", encoding="utf-8")
    return "abstract emptied in BOTH renderers"


def m_stub_question_chapter(pp: ProjectPaths) -> str:
    stub = "\\section{Models}\n% This chapter will describe the model.\n"
    (pp.latex_dir / "sections" / "models.tex").write_text(stub, encoding="utf-8")
    (pp.word_dir / "sections" / "models.md").write_text("# Models\n\nTODO\n", encoding="utf-8")
    return "models chapter reduced to a comment stub"


def m_text_only_algorithm(pp: ProjectPaths) -> str:
    prose = ("The algorithm proceeds as follows. Step one: collect the demand "
             "history for the full horizon and verify that no delivery round is "
             "missing from the ledger. Step two: compute the moving average of "
             "the observed series and inspect its drift. Step three: fit the "
             "trend line by ordinary least squares on the trailing window. "
             "Step four: iterate the residual correction until the change of "
             "the fitted slope falls below the preset tolerance, which in our "
             "runs happened after a handful of passes. Step five: produce the "
             "forecast for the next day and hand it to the dispatch planner, "
             "who compares it against the safety stock before committing "
             "vehicles. The loop terminates when convergence is reached; if it "
             "does not terminate within the budget, the last iterate is used "
             "and the failure is recorded so that downstream chapters can "
             "qualify the numbers they report.\n")
    body = "\\section{Models}\n" + prose
    (pp.latex_dir / "sections" / "models.tex").write_text(body, encoding="utf-8")
    (pp.word_dir / "sections" / "models.md").write_text(
        "# Models\n\n" + prose.replace("\\", ""), encoding="utf-8")
    return "model chapter is prose-only algorithm, zero display equations"


def m_figure_without_discussion(pp: ProjectPaths) -> str:
    p = pp.latex_dir / "sections" / "results.tex"
    t = _read(p)
    t = re.sub(r"^.*\\ref\{fig:forecast\}.*$\n?", "", t, flags=re.MULTILINE)
    t = t.replace("(F-001)", "")
    p.write_text(t, encoding="utf-8")
    return "every textual reference to fig:forecast removed"


def m_unsupported_claim(pp: ProjectPaths) -> str:
    p = pp.latex_dir / "sections" / "results.tex"
    p.write_text(_read(p) +
                 "\nOverall, our method improves accuracy by 23.5\\% over "
                 "the baseline under every regime we tested.\n", encoding="utf-8")
    return "floating percentage claim with no Result-ID anchor"


def m_disconnected_questions(pp: ProjectPaths) -> str:
    (pp.state_dir / "question-dependency-map.yaml").write_text(
        "dependencies:\n  - from: models\n    to: results\n", encoding="utf-8")
    p = pp.latex_dir / "sections" / "results.tex"
    t = _read(p).replace("answers the Q1\nforecast question posed in the introduction. ",
                         "").replace("answers the Q1 forecast question posed in the introduction. ", "")
    # remove shared tokens so the declared coupling is not materialized
    for tok in ["Eq.~\\eqref{eq:mae}", "(T-001)", "T-001"]:
        pass
    p.write_text(t, encoding="utf-8")
    (pp.state_dir / "question-dependency-map.yaml").write_text(
        "dependencies:\n  - from: models\n    to: results\n", encoding="utf-8")
    # sever shared tokens between the two chapters
    mp = pp.latex_dir / "sections" / "models.tex"
    mt = _read(mp).replace("defined in Eq.~\\eqref{eq:mae} of the results chapter, which keeps model\nselection and reporting on a single scale (see also T-002).",
                           "defined in the results chapter.")
    mp.write_text(mt, encoding="utf-8")
    rp = pp.latex_dir / "sections" / "results.tex"
    rt = _read(rp).replace("which matters operationally because understaffed peak days",
                           "which matters operationally because understaffed peaks")
    rt = re.sub(r"\(T-001\)", "", rt)
    rp.write_text(rt, encoding="utf-8")
    return "declared models->results coupling with no shared evidence"


def m_real_compile_overfull(pp: ProjectPaths) -> str:
    """REAL compile: produce main.log/main.pdf containing an overfull >15pt."""
    texbin = None
    try:
        from ommw.config import detect_texlive_bin, load_config
        texbin = detect_texlive_bin(load_config())
    except Exception:
        texbin = None
    out = pp.latex_dir / "output"
    out.mkdir(parents=True, exist_ok=True)
    if not texbin or not (texbin / "xelatex.exe").exists() and not (texbin / "xelatex").exists():
        return "SKIP-REAL-COMPILE (engine unavailable; case inconclusive)"
    bad_doc = (
        "\\documentclass{article}\\begin{document}\n"
        "\\noindent\\rule{540pt}{12pt} and now an unbreakable token:\n"
        "supercalifragilisticexpialidocious-donothing-xxxxxxxxxxxxxxxxxxxx-yyyy.\n"
        "\\end{document}\n")
    src = out / "layout_probe.tex"
    src.write_text(bad_doc, encoding="utf-8")
    exe = texbin / ("xelatex.exe" if sys.platform.startswith("win") else "xelatex")
    subprocess.run(
        [str(exe), "-interaction=nonstopmode", "-halt-on-error",
         "-output-directory", ".", "layout_probe.tex"],
        cwd=str(out), capture_output=True, text=True, timeout=180)
    (out / "main.log").write_text(_read(out / "layout_probe.log"), encoding="utf-8")
    pdf = out / "layout_probe.pdf"
    if pdf.exists():
        shutil.copy2(pdf, out / "main.pdf")
    return "real xelatex run produced layout_probe.log/pdf as output/main.*"


def m_formula_inflation(pp: ProjectPaths) -> str:
    # second, well-formed model chapter keeps the paper-wide word floor
    # satisfied so ONLY the inflation anomaly fires (MEDIUM, no gate fails)
    q1_prose = (
        "The first question asks for a one-day-ahead demand forecast that the "
        "dispatch team can act on before the morning round. We treat the demand "
        "series as the superposition of a slowly moving level and a weekly "
        "seasonal component, and we model the level with the trend regression "
        "of the models chapter while the seasonal factor is estimated as the "
        "mean ratio between the observed demand and the fitted level for each "
        "weekday. Formally the seasonal index is defined by\n"
        "\\begin{equation}s_j = \\frac{1}{K}\sum_{k=1}^{K}"
        "\\frac{d_{7k+j}}{\\hat{d}_{7k+j}}, \\quad j=1,\\ldots,7"
        "\\label{eq:q1}\\end{equation}\n"
        "where $K$ counts the complete weeks in the trailing window and the "
        "index is normalised so that its average equals one; the adjusted "
        "forecast multiplies the trend prediction by $s_j$: \n"
        "\\begin{equation}\\hat{d}^{\\,\\mathrm{adj}}_{7k+j} = s_j\\,"
        "\\hat{d}_{7k+j}\\label{eq:q1b}\\end{equation}\n"
        "This two-stage "
        "design keeps the interpretable slope of the trend model while "
        "absorbing the pronounced weekend dip that the raw fit systematically "
        "underestimates. We validate the stage-one residuals for remaining "
        "autocorrelation before accepting the index, because a drifting level "
        "would contaminate the ratios and propagate into every weekday. The "
        "per-weekday indices are tabulated below and referenced throughout "
        "the experiment discussion of the results chapter.\n")
    q1_body = ("\\section{Question I: Demand Forecast}\n" + q1_prose +
               "\\begin{table}[htbp]\\centering\n"
               "\\caption{Weekday seasonal indices used by question I}"
               "\\label{tab:q1}\n"
               "\\begin{tabular}{lc}Weekday & Index \\\\ Mon & 1.04 \\\\ "
               "Sat & 0.91 \\\\\\end{tabular}\\end{table}\n"
               "Table~\\ref{tab:q1} lists the indices applied on top of the "
               "trend forecast.\n")
    (pp.latex_dir / "sections" / "question1.tex").write_text(q1_body, encoding="utf-8")
    (pp.word_dir / "sections" / "question1.md").write_text(
        "# Question I\n\nSeasonal-adjusted one-day forecast; see LaTeX source.\n",
        encoding="utf-8")

    prose = ("The model family below enumerates rolling-window variants of the "
             "trend specification; each variant is scored with the metric of "
             "Eq.~\\eqref{eq:mae}. ") * 2
    dump = "".join(
        "\\begin{equation}\\hat{d}_t^{(%d)} = \\beta_0^{(%d)} + \\beta_1^{(%d)} t"
        "\\label{eq:dup%d}\\end{equation}\n" % (i, i, i, i)
        for i in range(45))
    body = ("\\section{Models}\n" + prose + "\n" + dump + "\n"
            "\\begin{table}[htbp]\\centering\n"
            "\\caption{Estimated model parameters (T-002)}\\label{tab:params}\n"
            "\\begin{tabular}{lll}Parameter & Meaning & Type \\\\\n"
            "$\\beta_0$ & intercept & estimated \\\\\n"
            "$\\beta_1$ & slope & estimated \\\\\\end{tabular}\\end{table}\n"
            "\nThe enumerated variants are recorded alongside "
            "Table~\\ref{tab:params}.\n")
    (pp.latex_dir / "sections" / "models.tex").write_text(body, encoding="utf-8")
    mt = (pp.latex_dir / "main.tex").read_text(encoding="utf-8").replace(
        "\\input{sections/models.tex}",
        "\\input{sections/question1.tex}\n\\input{sections/models.tex}")
    (pp.latex_dir / "main.tex").write_text(mt, encoding="utf-8")
    return "45 near-identical equations with thin prose in ONE chapter only"


def m_strip_visuals(pp: ProjectPaths) -> str:
    r = pp.latex_dir / "sections" / "results.tex"
    t = _read(r)
    t = re.sub(r"\\begin\{figure\}.*?\\end\{figure\}", "", t, flags=re.DOTALL)
    t = re.sub(r"\\begin\{table\}.*?\\end\{table\}", "", t, flags=re.DOTALL)
    r.write_text(t, encoding="utf-8")
    m = pp.latex_dir / "sections" / "models.tex"
    mt = re.sub(r"\\begin\{table\}.*?\\end\{table\}", "", _read(m), flags=re.DOTALL)
    m.write_text(mt, encoding="utf-8")
    (pp.figures_index).write_text("", encoding="utf-8")
    return "all figure/table environments and registry entries removed"


MUTATIONS = {
    "drop_abstract": m_drop_abstract,
    "stub_question_chapter": m_stub_question_chapter,
    "text_only_algorithm": m_text_only_algorithm,
    "figure_without_discussion": m_figure_without_discussion,
    "unsupported_claim": m_unsupported_claim,
    "disconnected_questions": m_disconnected_questions,
    "real_compile_overfull": m_real_compile_overfull,
    "formula_inflation": m_formula_inflation,
    "strip_visuals": m_strip_visuals,
    "none": lambda pp: "base untouched",
}


# --------------------------------------------------------------------------
# runner
# --------------------------------------------------------------------------

def load_cases() -> list[dict]:
    import yaml
    return yaml.safe_load((HERE / "cases.yaml").read_text(encoding="utf-8"))["cases"]


def run_case(case: dict, workdir: Path) -> dict:
    # Idempotent, delete-free rebuild (sandbox-safe): every base file is
    # overwritten in place; no rmtree anywhere.
    dest = workdir / case["id"]
    dest.mkdir(parents=True, exist_ok=True)
    pp = _write_base_project(dest)
    note = MUTATIONS[case["mutation"]](pp)
    reports = {g: r for g, r in run_all_paper_gates(pp).items()}
    crits = has_critical(reports)
    failed_gates = sorted(g for g, r in reports.items() if not r.passed)
    codes = [f.code for r in reports.values() for f in r.findings]
    expect_fail = bool(case.get("expect_fail"))
    ok_codes: list[str] = case.get("expect_codes") or []
    any_of: list[str] = case.get("expect_codes_any") or []

    checks = {}
    checks["fail_expectation"] = (bool(failed_gates) == expect_fail)
    checks["required_codes"] = all(c in codes for c in ok_codes)
    checks["any_of_codes"] = (not any_of) or any(c in codes for c in any_of)
    if expect_fail and case.get("critical"):
        checks["critical_present"] = any(c in {c for _, c in crits} for c in ok_codes)
    passed = all(checks.values())
    return {"id": case["id"], "mutation_note": note, "passed": passed,
            "checks": checks, "failed_gates": failed_gates,
            "criticals": [list(c) for c in crits],
            "codes_found": sorted(set(codes))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default=str(ROOT / ".build" / "evals" / "paper-production"))
    args = ap.parse_args()
    workdir = Path(args.workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    cases = load_cases()
    results, failures = [], 0
    for case in cases:
        res = run_case(case, workdir)
        results.append(res)
        if not res["passed"]:
            failures += 1
        flag = "PASS" if res["passed"] else "FAIL"
        print(f"[{flag}] {case['id']}: {res['mutation_note']}")
        if not res["passed"]:
            print(f"       failed_gates={res['failed_gates']} criticals={res['criticals']}")
            print(f"       checks={res['checks']}")
            print(f"       codes_found={res['codes_found']}")

    report = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "total": len(cases), "failures": failures, "cases": results}
    (HERE / "eval-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Paper-production eval report", "",
             f"- generated: {report['generated_at']}",
             f"- cases: {report['total']}, failures: {report['failures']}", "",
             "| case | result | mutation |", "|---|---|---|"]
    for r in results:
        lines.append(f"| {r['id']} | {'PASS' if r['passed'] else 'FAIL'} "
                     f"| {r['mutation_note']} |")
    (HERE / "eval-report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\nreport -> {HERE / 'eval-report.md'}")
    print(f"EVALS {'ALL PASS' if failures == 0 else f'{failures} FAILED'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
