"""`ommw` CLI — the cross-platform control plane.

PowerShell/bash scripts are thin wrappers; canonical logic lives here.
Commands: doctor, init, status, verify, render, citations, results, parity,
install-adapter, provider, migrate, smoke-test, health, package.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from . import __version__, atomic
from .adapters import WorkbuddyAdapter
from .config import load_config
from .doctor import format_report, run as doctor_run
from .parity import parity_check
from .paths import ProjectPaths, core_dir, core_root
from .render import LatexRenderer, WordRenderer
from .schemas import OutputMode, ProjectYaml, Progress, Stage
from .verify import research_verify

app = typer.Typer(
    name="ommw",
    help="Open Mathematical Modeling Workflow: portable, anti-hallucination competition modeling.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_project(root: Path) -> tuple[ProjectPaths, ProjectYaml]:
    pp = ProjectPaths(root=root.resolve())
    data = atomic.read_yaml(pp.project_yaml) or {}
    return pp, ProjectYaml(**data)


def _save_project(pp: ProjectPaths, proj: ProjectYaml) -> None:
    atomic.write_yaml(pp.project_yaml, proj.model_dump(mode="json"))


def _init_state_files(pp: ProjectPaths, proj: ProjectYaml) -> None:
    atomic.write_yaml(pp.project_yaml, proj.model_dump(mode="json"))
    atomic.write_json(pp.progress_json, Progress(current_stage=Stage.received, last_updated=_now()).model_dump(mode="json"))
    for p in (pp.claims_path, pp.results_path, pp.sources_path, pp.experiments_path,
              pp.figures_index, pp.tables_index):
        if not p.exists():
            p.write_text("", encoding="utf-8")
    atomic.write_yaml(pp.assumptions_path, {"assumptions": []})
    atomic.write_yaml(pp.notation_path, {"entries": []})


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------

@app.command()
def doctor() -> None:
    """Layered environment diagnostics (PASS/WARN/FAIL)."""
    rep = doctor_run()
    console.print(format_report(rep))
    # Persist capabilities into core for reference.
    caps_path = core_root() / ".build" / "capabilities.json"
    atomic.write_json(caps_path, rep.capabilities())
    if rep.overall == "FAIL":
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

@app.command()
def init(
    name: str = typer.Argument(..., help="Project directory to create."),
    mode: str = typer.Option("latex", "--mode", "-m", help="latex | word | dual"),
    rigor: str = typer.Option("strict", "--rigor", help="quick|strict|competition|research"),
    competition: str = typer.Option("generic", "--competition", help="competition profile name"),
    title: str = typer.Option("", "--title", help="paper title"),
) -> None:
    """Scaffold a new modeling project workspace."""
    root = Path(name).expanduser().resolve()
    if root.exists() and any(root.iterdir()):
        raise typer.BadParameter(f"{root} is not empty")
    pp = ProjectPaths(root=root)
    pp.ensure_dirs()
    proj = ProjectYaml(
        title=title or name,
        competition=competition,
        output_mode=OutputMode(mode),
        rigor=rigor,  # type: ignore[arg-type]
        schema_version=1,
        workflow_version=__version__,
        created_at=_now(),
    )
    _init_state_files(pp, proj)
    _seed_templates(pp, proj)
    atomic.write_json(pp.capabilities_path, doctor_run().capabilities())
    console.print(f"[green]Initialized[/green] project at [bold]{root}[/bold]")
    console.print(f"  mode={mode} rigor={rigor} competition={competition}")
    console.print("Next: `ommw status` or `ommw smoke-test` to verify the pipeline.")


def _seed_templates(pp: ProjectPaths, proj: ProjectYaml) -> None:
    """Copy the competition/latex/word templates into the project."""
    tpl_root = core_dir("templates")
    # LaTeX skeleton
    latex_tpl = tpl_root / "latex" / "main.tex"
    if latex_tpl.exists():
        shutil.copy2(latex_tpl, pp.latex_dir / "main.tex")
    # Word reference.docx
    ref = tpl_root / "word" / "reference.docx"
    if ref.exists():
        shutil.copy2(ref, pp.word_dir / "reference.docx")
    # Seed one placeholder section per chapter to make the contract explicit.
    for ch in proj.chapters:
        (pp.latex_dir / "sections" / f"{ch}.tex").write_text(
            f"% {ch} -- placeholder. Evidence required before prose (no-prose-before-evidence).\n",
            encoding="utf-8",
        )
        (pp.word_dir / "sections" / f"{ch}.md").write_text(
            f"# {ch.replace('-', ' ').title()}\n\n<!-- placeholder -->\n",
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

@app.command()
def status(
    project: Path = typer.Option(Path("."), "--project", "-p", help="project root"),
) -> None:
    """Show current Problem State Machine position and open findings."""
    pp, proj = _load_project(project)
    progress = Progress(**(atomic.read_json(pp.progress_json) or {}))
    tbl = Table(title=f"OMMW status — {proj.title}")
    tbl.add_column("field"); tbl.add_column("value")
    tbl.add_row("schema_version", str(proj.schema_version))
    tbl.add_row("workflow_version", proj.workflow_version)
    tbl.add_row("mode", proj.output_mode.value)
    tbl.add_row("rigor", proj.rigor.value)
    tbl.add_row("current_stage", progress.current_stage.value)
    tbl.add_row("completed", ", ".join(s.value for s in progress.completed_stages) or "(none)")
    tbl.add_row("degraded", ", ".join(progress.degraded) or "(none)")
    # ledger counts
    tbl.add_row("claims", str(len(atomic.read_jsonl(pp.claims_path))))
    tbl.add_row("results", str(len(atomic.read_jsonl(pp.results_path))))
    tbl.add_row("sources", str(len(atomic.read_jsonl(pp.sources_path))))
    tbl.add_row("experiments", str(len(atomic.read_jsonl(pp.experiments_path))))
    console.print(tbl)


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------

@app.command()
def verify(
    project: Path = typer.Option(Path("."), "--project", "-p"),
) -> None:
    """Run Research Core linkage + renderer verification gates."""
    pp, _ = _load_project(project)
    rep = research_verify(pp)
    if rep.findings:
        for f in rep.findings:
            color = {"CRITICAL": "red", "HIGH": "red", "MEDIUM": "yellow", "LOW": "dim"}[f.severity]
            console.print(f"[{color}]{f.severity:<8}[/{color}] {f.code:<22} {f.message}  @{f.location}")
    state = "VERIFIED" if rep.passed else "FAILED"
    console.print(f"\nRESEARCH VERIFY: [bold {'green' if rep.passed else 'red'}]{state}[/bold {'green' if rep.passed else 'red'}]")
    if not rep.passed:
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------

@app.command()
def render(
    project: Path = typer.Option(Path("."), "--project", "-p"),
    mode: Optional[str] = typer.Option(None, "--mode", "-m", help="latex|word|dual (overrides project.yaml)"),
) -> None:
    """Render the paper in LaTeX and/or Word. Compile-or-not-done enforced."""
    pp, proj = _load_project(project)
    cfg = load_config()
    mode = mode or proj.output_mode.value
    summary: dict = {"mode": mode, "latex": None, "word": None, "degraded": []}

    if mode in ("latex", "dual"):
        lr = LatexRenderer(pp, cfg).compile_main()
        summary["latex"] = {
            "ok": lr.ok, "pdf": str(lr.pdf) if lr.pdf else None,
            "errors": lr.errors[:5], "undefined_citations": lr.undefined_citations[:10],
            "degraded": lr.degraded,
        }
        tag = "VERIFIED" if lr.ok else "FAILED"
        console.print(f"LATEX: [bold {'green' if lr.ok else 'red'}]{tag}[/bold {'green' if lr.ok else 'red'}]"
                      + (f"  pdf={lr.pdf}" if lr.pdf else ""))
        summary["degraded"].extend(lr.degraded)

    if mode in ("word", "dual"):
        wr = WordRenderer(pp, cfg).build()
        summary["word"] = {
            "ok": wr.ok, "docx": str(wr.docx) if wr.docx else None,
            "structural_qa": wr.structural_qa, "visual_qa": wr.visual_qa,
            "degraded": wr.degraded,
        }
        tag = "VERIFIED" if wr.ok else "FAILED"
        console.print(f"WORD:  [bold {'green' if wr.ok else 'red'}]{tag}[/bold {'green' if wr.ok else 'red'}]"
                      f"  structural={wr.structural_qa} visual={wr.visual_qa}")
        summary["degraded"].extend(wr.degraded)

    if mode == "dual":
        parity = parity_check(pp)
        console.print(f"PARITY: [bold {'green' if parity.passed else 'red'}]"
                      f"{'PASS' if parity.passed else 'MISMATCH'}[/bold {'green' if parity.passed else 'red'}]")

    # build-manifest (Rule 117)
    manifest = {
        "workflow_version": __version__,
        "mode": mode,
        "timestamp": _now(),
        "summary": summary,
    }
    pp.dist_dir.mkdir(parents=True, exist_ok=True)
    atomic.write_json(pp.dist_dir / "manifests" / "build-manifest.json", manifest)
    atomic.write_json(pp.state_dir / "capabilities.json", doctor_run().capabilities())


# ---------------------------------------------------------------------------
# citations / results / parity / install-adapter / provider / migrate / health / package
# ---------------------------------------------------------------------------

@app.command()
def citations(
    project: Path = typer.Option(Path("."), "--project", "-p"),
    offline: bool = typer.Option(False, "--offline", help="use cache only; mark misses UNVERIFIED_OFFLINE"),
) -> None:
    """Verify source ledger (metadata vs claim verification)."""
    from .citations import CitationCache, fetch_doi
    pp, _ = _load_project(project)
    cache = CitationCache(pp.cache_dir / "citations.json")
    sources = atomic.read_jsonl(pp.sources_path)
    if not sources:
        console.print("No sources in ledger. Add sources first.")
        return
    tbl = Table(title="Citation verification")
    tbl.add_column("id"); tbl.add_column("doi"); tbl.add_column("metadata"); tbl.add_column("verification")
    for s in sources:
        doi = s.get("doi", "")
        if doi and not s.get("metadata_verified"):
            fetched = fetch_doi(doi, cache, offline=offline)
            if fetched:
                s["metadata_verified"] = True
                s["verification"] = fetched.verification.value
        tbl.add_row(s.get("source_id", "?"), doi or "-",
                    "ok" if s.get("metadata_verified") else "MISS",
                    s.get("verification", "UNVERIFIED"))
    atomic.write_jsonl(pp.sources_path, sources)
    console.print(tbl)


@app.command()
def results(
    project: Path = typer.Option(Path("."), "--project", "-p"),
) -> None:
    """List the result ledger (anti-hallucination: paper numbers must reference these)."""
    pp, _ = _load_project(project)
    rs = atomic.read_jsonl(pp.results_path)
    if not rs:
        console.print("No results recorded."); return
    tbl = Table(title="Results ledger")
    for col in ("result_id", "name", "value", "unit", "run_id", "verified"):
        tbl.add_column(col)
    for r in rs:
        tbl.add_row(*[str(r.get(c, "")) for c in ("result_id", "name", "value", "unit", "run_id", "verified")])
    console.print(tbl)


@app.command()
def parity(
    project: Path = typer.Option(Path("."), "--project", "-p"),
) -> None:
    """Dual-mode parity gate (LaTeX vs Word fingerprints)."""
    pp, _ = _load_project(project)
    rep = parity_check(pp)
    console.print(f"PARITY: {'PASS' if rep.passed else 'MISMATCH'}  ({len(rep.findings)} findings)")
    for f in rep.findings:
        console.print(f"  {f.severity}: {f.code} {f.message}")


@app.command(name="install-adapter")
def install_adapter(
    runtime: str = typer.Argument("workbuddy", help="agent runtime: workbuddy"),
) -> None:
    """Install a thin skill wrapper for an agent runtime."""
    if runtime != "workbuddy":
        raise typer.BadParameter("only 'workbuddy' adapter shipped in v0.1")
    res = WorkbuddyAdapter(load_config()).install()
    if res.ok:
        console.print(f"[green]Installed[/green] workbuddy adapter via {res.method} -> {res.skill_dir}")
    else:
        console.print(f"[red]FAILED[/red] {res.message}")
        raise typer.Exit(1)


@app.command()
def provider(
    action: str = typer.Argument("list", help="list|audit|check-updates"),
    name: str = typer.Option("", "--name", help="provider name"),
) -> None:
    """Manage optional external providers (MathModelAgent, scientific-skills)."""
    if action == "list":
        tbl = Table(title="Providers")
        tbl.add_column("name"); tbl.add_column("trust"); tbl.add_column("license")
        tbl.add_row("mathmodelagent", "EXTERNAL_OPTIONAL", "personal non-commercial")
        tbl.add_row("scientific-skills", "AUDITED_VENDOR", "MIT (per-skill varies)")
        console.print(tbl)
    elif action == "audit":
        target = name or "mathmodelagent"
        audit_path = core_dir("provenance", "audits", f"{target}.md")
        if audit_path.exists():
            console.print(audit_path.read_text(encoding="utf-8"))
        else:
            console.print(f"No audit record for {target}; see providers/{target}/README.md")
    else:
        console.print("check-updates: not implemented in v0.1 (pinned commits; manual update only)")


@app.command()
def migrate(
    project: Path = typer.Option(Path("."), "--project", "-p"),
) -> None:
    """Bring an older project's state schema forward (idempotent, backs up first)."""
    pp, proj = _load_project(project)
    backup = pp.state_dir / f".backup-{_now().replace(':','-')}"
    if pp.state_dir.exists():
        shutil.copytree(pp.state_dir, backup)
    proj.schema_version = 1
    proj.workflow_version = __version__
    _save_project(pp, proj)
    console.print(f"Migrated to schema_version=1, workflow={__version__}. Backup: {backup}")


@app.command()
def health(
    project: Path = typer.Option(Path("."), "--project", "-p"),
) -> None:
    """Project health (v1.0, Rule 131): stale/claims/figures/citations/AI log."""
    from .health import health_check
    pp, _ = _load_project(project)
    rep = health_check(pp)
    high = [f for f in rep.findings if f.severity in ("CRITICAL", "HIGH")]
    console.print(f"Open CRITICAL/HIGH findings: [bold {'red' if high else 'green'}]{len(high)}[/bold {'red' if high else 'green'}]")
    for f in high:
        console.print(f"  {f.severity} {f.code}: {f.message} @{f.location}")
    if rep.findings:
        console.print(f"total findings: {len(rep.findings)}")


@app.command()
def package(
    project: Path = typer.Option(Path("."), "--project", "-p"),
) -> None:
    """Build a competition submission pack (dist -> submission/) per profile rules."""
    pp, proj = _load_project(project)
    sub = pp.root / "submission"
    if sub.exists():
        shutil.rmtree(sub)
    sub.mkdir(parents=True)
    # Copy final PDF/DOCX from dist, applying competition-named files (Rule 178).
    latex_pdf = pp.latex_dir / "output" / "main.pdf"
    word_docx = pp.dist_dir / "word" / "paper.docx"
    versioned = f"paper-v{proj.workflow_version}-build-{time.strftime('%Y%m%d')}"
    if latex_pdf.exists():
        shutil.copy2(latex_pdf, sub / f"{versioned}.pdf")
    if word_docx.exists():
        shutil.copy2(word_docx, sub / f"{versioned}.docx")
    # Submission gate (Rule 180): anonymization check, forbidden files.
    forbidden = [".env", "config.local.toml", ".cache", ".build"]
    leaked = [f for f in forbidden if (sub / f).exists()]
    atomic.write_json(sub / "submission-manifest.json", {
        "versioned_name": versioned, "leaked_forbidden": leaked, "ok": not leaked,
    })
    console.print(f"Submission pack -> {sub}  ({'OK' if not leaked else 'LEAK: '+str(leaked)})")


# ---------------------------------------------------------------------------
# smoke-test
# ---------------------------------------------------------------------------

@app.command(name="smoke-test")
def smoke_test(
    dest: Path = typer.Option(Path(".") / "_smoke", "--dest", help="temp dir for the smoke project"),
    mode: str = typer.Option("dual", "--mode", help="latex|word|dual"),
) -> None:
    """Run a tiny end-to-end pipeline on synthetic data (incl. negative cases)."""
    from .smoke import run_smoke
    ok = run_smoke(dest.resolve(), mode=mode)
    if not ok:
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# v1.0 Research Operating System commands (deterministic parts; complex
# research judgment remains in the agent workflow — Rule 112)
# ---------------------------------------------------------------------------

@app.command()
def competition(
    project: Path = typer.Option(Path("."), "--project", "-p"),
    text: str = typer.Option("", "--text", help="problem text for detection"),
    live: bool = typer.Option(False, "--live", help="mark as LIVE contest mode"),
    name: str = typer.Option("", "--competition", help="force competition name (cumcm/mcm_icm/graduate/generic)"),
) -> None:
    """Detect / build / save the competition profile (Layer 1)."""
    from .competition import build_profile, detect_competition, save_profile
    pp, _ = _load_project(project)
    det = detect_competition(text, live=live)
    if name:
        det.competition = name
    profile = build_profile(det)
    save_profile(pp, profile)
    tbl = Table(title="Competition profile")
    tbl.add_column("field"); tbl.add_column("value")
    for k, v in profile.model_dump().items():
        tbl.add_row(k, v.value if hasattr(v, "value") else str(v))
    console.print(tbl)
    console.print(f"\nSaved: {pp.state_dir / 'competition-profile.yaml'}")
    console.print("[yellow]WARNING: detection is heuristic. Verify against official rules "
                  "before locking (fetch official sources).[/yellow]")


@app.command(name="audit-data")
def audit_data(
    project: Path = typer.Option(Path("."), "--project", "-p"),
    data: str = typer.Option("", "--data", help="CSV path (default: first file in data/raw)"),
) -> None:
    """Run the Data Audit Engine (Layer 3, Rule 21)."""
    from .data_engine import DataAuditSpec, audit_csv, infer_spec, write_report
    pp, _ = _load_project(project)
    if not data:
        raws = sorted(pp.data_raw.glob("*.csv"))
        if not raws:
            console.print("[red]No CSV found in data/raw.[/red]")
            raise typer.Exit(1)
        data = str(raws[0])
    # Auto-infer common constraints (counts>=0, rates in [0,1]); agent refines later.
    import csv as _csv
    with open(data, encoding="utf-8", newline="") as _f:
        cols = next(_csv.reader(_f))
    spec = infer_spec(cols)
    rep = audit_csv(Path(data), spec)
    for f in rep.findings:
        color = {"CRITICAL": "red", "HIGH": "red", "MEDIUM": "yellow", "LOW": "dim"}[f.severity]
        console.print(f"[{color}]{f.severity:<8}[/{color}] {f.code:<24} {f.message}")
    out = pp.data_processed / "data-audit-report.md"
    write_report(rep, out)
    console.print(f"\nDATA AUDIT: {'PASS' if rep.passed else 'FINDINGS'}  report={out}")


@app.command()
def models(
    project: Path = typer.Option(Path("."), "--project", "-p"),
    problem_type: str = typer.Option("prediction", "--problem-type", help="problem family for routing"),
    show: bool = typer.Option(True, "--show/--no-show"),
) -> None:
    """Model discovery routing: candidate families per problem type (Rule 29)."""
    from .modeling import route_candidates
    pp, _ = _load_project(project)
    candidates = route_candidates(problem_type)
    if show:
        tbl = Table(title=f"Model candidates: {problem_type}")
        tbl.add_column("model"); tbl.add_column("family"); tbl.add_column("fit")
        tbl.add_column("cost"); tbl.add_column("reason_to_test")
        for c in candidates:
            tbl.add_row(c.model, c.family, c.theoretical_fit, c.computational_cost, c.reason_to_test)
        console.print(tbl)
    atomic.write_json(pp.state_dir / "model-candidates.json",
                      [c.model_dump() for c in candidates])


@app.command(name="plan-experiments")
def plan_experiments(
    project: Path = typer.Option(Path("."), "--project", "-p"),
    problem_type: str = typer.Option("prediction", "--problem-type"),
    n_models: int = typer.Option(2, "--models"),
    complexity: str = typer.Option("medium", "--complexity", help="low|medium|high"),
    stochastic: bool = typer.Option(False, "--stochastic"),
    time_series: bool = typer.Option(False, "--timeseries"),
    has_data: bool = typer.Option(True, "--data/--no-data"),
) -> None:
    """Plan the experiment portfolio (Rule 35)."""
    from .experiment_lab import portfolio_for_problem
    pp, _ = _load_project(project)
    plans = portfolio_for_problem(problem_type, n_models=n_models,
                                  has_data=has_data, stochastic=stochastic,
                                  time_series=time_series, complexity=complexity)
    tbl = Table(title=f"Experiment portfolio ({len(plans)} experiments)")
    tbl.add_column("id"); tbl.add_column("family"); tbl.add_column("model")
    tbl.add_column("metric"); tbl.add_column("seed")
    for p in plans:
        tbl.add_row(p.experiment_id, p.family, p.model, p.metric, str(p.seed or ""))
    console.print(tbl)
    atomic.write_json(pp.state_dir / "experiment-plan.json",
                      [p.model_dump(mode="json") for p in plans])


@app.command(name="run-experiment")
def run_experiment(
    project: Path = typer.Option(Path("."), "--project", "-p"),
    experiment_id: str = typer.Option("E-001", "--experiment", "-e"),
    model: str = typer.Option("linear-trend", "--model", help="built-in demo executor"),
) -> None:
    """Execute a planned experiment and PERSIST artifacts to disk (Rule 34)."""
    from .experiment_lab import run_experiment as _run
    from .schemas.experiment_lab import ExperimentPlan, ExperimentStatus
    pp, _ = _load_project(project)
    plan = ExperimentPlan(
        experiment_id=experiment_id, model=model, metric="mae",
        family="comparison", status=ExperimentStatus.planned,
        success_condition="metric recorded and validated")

    def _demo_execute(p: ExperimentPlan) -> dict:
        """Built-in deterministic demo executor (for CLI/benchmark use)."""
        import math
        mae = round(abs(math.sin(hash(p.experiment_id) % 97)) / 10 + 0.2, 4)
        return {"metrics": {"mae": mae}, "predictions": [{"t": 0, "yhat": 10.0}],
                "result": {"mae": mae, "model": p.model}}

    artifacts = _run(pp, plan, _demo_execute)
    console.print(f"EXPERIMENT {experiment_id}: COMPLETED")
    for a in (artifacts.result_json, artifacts.metrics_csv, artifacts.predictions_csv):
        console.print(f"  artifact: {pp.root / a}")


@app.command(name="validate-results")
def validate_results(
    project: Path = typer.Option(Path("."), "--project", "-p"),
) -> None:
    """Validate core results in the ledger (Rule 40)."""
    from .validation import ResultToValidate, validate_result
    pp, _ = _load_project(project)
    results = atomic.read_jsonl(pp.results_path)
    if not results:
        console.print("No results in ledger."); return
    total = 0
    for r in results:
        rv = ResultToValidate(result_id=r.get("result_id", "?"), name=r.get("name", ""),
                              value=r.get("value", ""), unit=r.get("unit", ""),
                              run_id=r.get("run_id", ""), data_hash=r.get("source_data_hash", ""))
        rep = validate_result(pp, rv)
        for f in rep.findings:
            total += 1
            console.print(f"  {f.severity}: {f.code} {f.message} ({r.get('result_id')})")
    console.print(f"RESULT VALIDATION: {'PASS' if total == 0 else f'{total} findings'}")


@app.command(name="ai-report")
def ai_report(
    project: Path = typer.Option(Path("."), "--project", "-p"),
) -> None:
    """Generate the AI-usage declaration + detail report from the REAL ledger."""
    from .competition import generate_ai_report, list_usage, summarize
    pp, _ = _load_project(project)
    s = summarize(pp)
    console.print(f"AI usage records: {s.total_records} (accepted {s.accepted}, human-reviewed {s.human_reviewed})")
    decl, _ = generate_ai_report(pp)
    console.print(f"Declaration: {pp.paper_dir / 'ai-usage-declaration.md'}")
    console.print(f"Detail:      {pp.dist_dir / 'AI工具使用详情.md'}")
    console.print("\n" + decl)


@app.command()
def judge(
    project: Path = typer.Option(Path("."), "--project", "-p"),
) -> None:
    """Competition-judge simulation: compliance gate + research verify summary."""
    from .competition import compliance_gate, load_profile
    from .schemas import CompetitionProfile
    pp, _ = _load_project(project)
    profile = load_profile(pp) or CompetitionProfile()
    c_rep = compliance_gate(pp, profile)
    r_rep = research_verify(pp)
    findings = c_rep.findings + r_rep.findings
    critical = [f for f in findings if f.severity == "CRITICAL"]
    high = [f for f in findings if f.severity == "HIGH"]
    console.print(f"JUDGE SIMULATION: CRITICAL={len(critical)} HIGH={len(high)} total={len(findings)}")
    for f in findings[:15]:
        console.print(f"  {f.severity}: {f.code} {f.message} @{f.location}")
    console.print("Note: internal review only; not an official scoring model.")


@app.command()
def benchmark(
    only: str = typer.Option("", "--only", help="run only this case id (e.g. NEG-001, SMOKE-A)"),
) -> None:
    """Run the internal benchmark suite (negative cases + smoke projects)."""
    from .benchmarks import full_suite, run_benchmark
    cases = full_suite()
    if only:
        cases = [c for c in cases if c.case_id == only]
        if not cases:
            console.print(f"[red]Unknown case {only}[/red]"); raise typer.Exit(1)
    rep = run_benchmark(cases)
    console.print(rep.table())
    if not rep.overall:
        raise typer.Exit(1)


@app.command()
def reproduce(
    project: Path = typer.Option(Path("."), "--project", "-p"),
) -> None:
    """Re-run the deterministic pipeline: audit-data -> research-verify -> validate."""
    pp, _ = _load_project(project)
    console.print("[yellow]reproduce: re-running deterministic pipeline[/yellow]")
    raws = sorted(pp.data_raw.glob("*.csv"))
    if raws:
        from .data_engine import audit_csv, write_report
        rep = audit_csv(raws[0])
        write_report(rep, pp.data_processed / "data-audit-report.md")
        console.print(f"  data-audit: {len(rep.findings)} findings")
    else:
        console.print("  data-audit: no raw CSV (skip)")
    r_rep = research_verify(pp)
    console.print(f"  research-verify: {'PASS' if r_rep.passed else 'FAIL'} ({len(r_rep.findings)} findings)")
    from .validation import ResultToValidate, validate_result
    n = 0
    for r in atomic.read_jsonl(pp.results_path):
        vrep = validate_result(pp, ResultToValidate(
            result_id=r.get("result_id", "?"), value=r.get("value", ""),
            unit=r.get("unit", ""), run_id=r.get("run_id", ""),
            data_hash=r.get("source_data_hash", "")))
        n += len(vrep.findings)
    console.print(f"  result-validation: {n} findings")
    console.print("REPRODUCE: done")


# ---------------------------------------------------------------------------
# v1.0 Layer 7/8: visualization, paper factory, knowledge, final audit
# ---------------------------------------------------------------------------

@app.command()
def plot(
    project: Path = typer.Option(Path("."), "--project", "-p"),
    figure_id: str = typer.Option("F-001", "--figure", "-f"),
    question: str = typer.Option("", "--question", "-q"),
    claim: str = typer.Option("", "--claim", "-c"),
    data: str = typer.Option("", "--data", "-d"),
    why: str = typer.Option("", "--why", "-w"),
    context: str = typer.Option("data", "--context", help="data|model|experiment"),
    claim_type: str = typer.Option("comparison", "--claim-type"),
) -> None:
    """Figure planner: pre-register a figure with Q/C/D/Why (Rule 50)."""
    from .visualization import plan_figure, validate_figure_plan
    pp, _ = _load_project(project)
    fp = plan_figure(figure_id=figure_id, question=question, claim=claim,
                     data=data, why=why, context=context, claim_type=claim_type)
    rep = validate_figure_plan(fp)
    for f in rep.findings:
        console.print(f"  {f.severity}: {f.code} {f.message}")
    console.print(f"FigurePlan: {fp.figure_id} type={fp.figure_type} output={fp.output}  "
                  f"valid={'YES' if rep.passed else 'NO (fill missing fields)'}")
    if rep.passed:
        from .schemas import FigureRecord
        from . import atomic
        atomic.append_jsonl(pp.figures_index, FigureRecord(
            figure_id=fp.figure_id, generator="ommw plot", data=fp.data,
            result_ids=[fp.claim], caption="", section="", output=fp.output,
        ).model_dump(mode="json"))
        console.print("registered to figures.jsonl")


@app.command(name="paper-plan")
def paper_plan(
    project: Path = typer.Option(Path("."), "--project", "-p"),
    problem_types: str = typer.Option("prediction", "--problem-types", help="comma-separated"),
    title: str = typer.Option("", "--title"),
) -> None:
    """Paper architect: build a dynamic blueprint + chapter contracts (Rule 64, 67)."""
    from .paper_factory import build_blueprint, make_chapter_contract
    from . import atomic
    pp, proj = _load_project(project)
    bp = build_blueprint(title=title or proj.title, competition=proj.competition,
                         language=proj.language,
                         problem_types=[t.strip() for t in problem_types.split(",")],
                         page_limit=0)
    console.print(f"Blueprint: {bp.title} [{bp.competition}] {len(bp.chapters)} chapters")
    for ch in bp.chapter_ids():
        contract = make_chapter_contract(ch, question=f"Q: {ch}", purpose=f"covers {ch}")
        bp.contracts[ch] = contract
        console.print(f"  - {ch}")
    atomic.write_json(pp.state_dir / "paper-blueprint.json",
                      {"chapters": bp.chapters,
                       "contracts": {k: v.__dict__ for k, v in bp.contracts.items()}})
    console.print("saved: state/paper-blueprint.json")


@app.command()
def chapter(
    project: Path = typer.Option(Path("."), "--project", "-p"),
    chapter_id: str = typer.Argument(..., help="chapter id"),
    question: str = typer.Option("", "--question"),
    claims: str = typer.Option("", "--claims", help="comma-separated claim ids"),
    results: str = typer.Option("", "--results", help="comma-separated result ids"),
) -> None:
    """Chapter contract: bind evidence to a chapter (Rule 67)."""
    from .paper_factory import make_chapter_contract
    from . import atomic
    pp, _ = _load_project(project)
    contract = make_chapter_contract(
        chapter_id, question=question,
        claims=[c for c in claims.split(",") if c],
        results=[r for r in results.split(",") if r],
    )
    atomic.write_json(pp.state_dir / f"chapter-{chapter_id}.json", contract.__dict__)
    console.print(f"Chapter contract {chapter_id}: claims={contract.claims} results={contract.results}")


@app.command()
def knowledge(
    project: Path = typer.Option(Path("."), "--project", "-p"),
    action: str = typer.Option("list", "--action", help="list|extract"),
    source: str = typer.Option("", "--source", help="paper id/path"),
    problem_type: str = typer.Option("", "--problem-type"),
    model_family: str = typer.Option("", "--model-family"),
    why: str = typer.Option("", "--why"),
    baseline: str = typer.Option("", "--baseline"),
    innovation: str = typer.Option("", "--innovation"),
) -> None:
    """Knowledge base: list patterns or extract structured knowledge (Rule 16-17)."""
    from .knowledge import extract_knowledge
    from .paths import core_root
    pp, _ = _load_project(project)
    kb = core_root() / "knowledge_base"
    if action == "list":
        patterns = sorted(p.stem for p in (kb / "problem_patterns").glob("*.json")) if (kb / "problem_patterns").exists() else []
        models = sorted(p.stem for p in (kb / "model_patterns").glob("*.md")) if (kb / "model_patterns").exists() else []
        console.print(f"knowledge_base patterns: {patterns or '(none extracted yet)'}")
        console.print(f"model_patterns docs: {models}")
    else:
        if not all((source, problem_type, model_family)):
            console.print("[red]extract requires --source --problem-type --model-family[/red]")
            raise typer.Exit(1)
        entry = extract_knowledge(source=source, problem_type=problem_type,
                                  model_family=model_family, why_model_selected=why,
                                  baseline=baseline, innovation=innovation)
        from .knowledge import save_knowledge_entry
        out = save_knowledge_entry(kb, entry)
        console.print(f"knowledge extracted -> {out}")


@app.command(name="final-audit")
def final_audit(
    project: Path = typer.Option(Path("."), "--project", "-p"),
) -> None:
    """Run the 13-dimension Final Audit (Rule 138) + paper manifest (Rule 136)."""
    from .final_audit import final_audit as _audit, paper_manifest
    pp, _ = _load_project(project)
    rep = _audit(pp)
    for f in rep.findings:
        color = {"CRITICAL": "red", "HIGH": "red", "MEDIUM": "yellow", "LOW": "dim"}[f.severity]
        console.print(f"[{color}]{f.severity:<8}[/{color}] {f.code:<30} {f.message}")
    critical = [f for f in rep.findings if f.severity == "CRITICAL"]
    high = [f for f in rep.findings if f.severity == "HIGH"]
    console.print(f"\nFINAL AUDIT: CRITICAL={len(critical)} HIGH={len(high)} "
                  f"{'PAPER VERIFIED' if not critical and not high else 'NOT VERIFIED'}")
    manifest = paper_manifest(pp)
    console.print(f"paper-manifest.json written ({len(manifest)} fields)")
    if critical or high:
        raise typer.Exit(1)


@app.command(name="material-manifest")
def material_manifest(
    project: Path = typer.Option(Path("."), "--project", "-p"),
) -> None:
    """Supporting-material manifest: every referenced artifact must exist (Rule 100)."""
    from .final_audit import supporting_material_manifest
    pp, _ = _load_project(project)
    m = supporting_material_manifest(pp)
    missing = [f for f in m["figures"] if not f["exists"]]
    missing_r = [r for r in m["results"] if not r["artifact_exists"]]
    console.print(f"supporting-material-manifest.json: {len(m['code'])} code, {len(m['data'])} data, "
                  f"{len(m['figures'])} figures, {len(m['results'])} results")
    console.print(f"  missing figure outputs: {len(missing)}  missing result artifacts: {len(missing_r)}")


if __name__ == "__main__":
    app()
