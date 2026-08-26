"""Final Audit (Rule 138) + Paper Manifest (Rule 136) + Supporting material
manifest (Rule 100). Aggregates the 13 audit dimensions into one gate.
"""
from __future__ import annotations

import time

from . import __version__, atomic
from .competition import compliance_gate, load_profile
from .paths import ProjectPaths
from .paper_factory import consistency_graph
from .verify import VerifyReport, research_verify


def final_audit(project: ProjectPaths) -> VerifyReport:
    """Run the 13 audit dimensions (Rule 138). Deterministic aggregate."""
    rep = VerifyReport()
    profile = load_profile(project)

    # 1. Competition compliance.
    if profile:
        sub = compliance_gate(project, profile)
        for f in sub.findings:
            rep.add(f.severity, "compliance:" + f.code, f.message, f.location)

    # 2. Data audit (re-run on raw if present).
    from .data_engine import audit_csv, infer_spec
    raws = sorted(project.data_raw.glob("*.csv"))
    if raws:
        import csv as _csv
        with open(raws[0], encoding="utf-8", newline="") as f:
            cols = next(_csv.reader(f))
        data_rep = audit_csv(raws[0], infer_spec(cols))
        for f in data_rep.findings:
            rep.add(f.severity, "data:" + f.code, f.message, f.location)

    # 3-6. Mathematical (notation) / experiment / result / citation / claim.
    for c in atomic.read_jsonl(project.claims_path):
        if c.get("status") not in ("SUPPORTED", "VERIFIED") and c.get("type") == "conclusion":
            rep.add("HIGH", "claim:unsupported-conclusion", f"claim {c.get('claim_id')} not verified", c.get("claim_id", "?"))
    for s in atomic.read_jsonl(project.sources_path):
        if s.get("verification") == "UNVERIFIED":
            rep.add("HIGH", "citation:unverified", f"source {s.get('source_id')} UNVERIFIED", s.get("source_id", "?"))
    for e in atomic.read_jsonl(project.experiments_path):
        if e.get("status") in ("FAILED", "STALE"):
            rep.add("HIGH", "experiment:" + str(e.get("status")).lower(),
                    f"experiment {e.get('run_id')} {e.get('status')}", e.get("run_id", "?"))

    # 7-8. Figure / table (broken outputs covered by research_verify).
    rv = research_verify(project)
    for f in rv.findings:
        rep.add(f.severity, f.code, f.message, f.location)

    # 9. Paper consistency (result dependents all re-verified?).
    graph = consistency_graph(project)
    for rid, deps in graph.items():
        if not deps:
            rep.add("LOW", "paper:result-unused", f"result {rid} not referenced by figure/table/claim", rid)

    # 10. AI usage (must exist if profile requires).
    if profile and "declare" in (profile.ai_policy or "").lower():
        if not (project.paper_dir / "ai-usage-declaration.md").exists():
            rep.add("HIGH", "ai:declaration-missing", "no AI usage declaration", "")

    # 11-13. Format / submission (page limit + forbidden files).
    if profile:
        pdf = project.latex_dir / "output" / "main.pdf"
        if pdf.exists():
            pages = pdf.read_bytes().count(b"/Type /Page") - pdf.read_bytes().count(b"/Type /Pages")
            limit = profile.effective_page_limit()
            if limit and pages > limit:
                rep.add("HIGH", "format:page-limit", f"{pages} pages > limit {limit}", str(pdf))
        sub = project.root / "submission"
        if sub.exists():
            for name in (".env", "config.local.toml"):
                if (sub / name).exists():
                    rep.add("HIGH", "submission:forbidden-file", f"submission contains {name}", str(sub))
    return rep


def paper_manifest(project: ProjectPaths, *, render_status: dict | None = None) -> dict:
    """Generate the final paper-manifest.json (Rule 136)."""
    manifest = {
        "workflow_version": __version__,
        "competition_profile": load_profile(project).model_dump(mode="json") if load_profile(project) else None,
        "data_hash": None,
        "code_commit": None,
        "models": [],
        "experiments": len(atomic.read_jsonl(project.experiments_path)),
        "results": len(atomic.read_jsonl(project.results_path)),
        "claims": len(atomic.read_jsonl(project.claims_path)),
        "citations": len(atomic.read_jsonl(project.sources_path)),
        "figures": len(atomic.read_jsonl(project.figures_index)),
        "tables": len(atomic.read_jsonl(project.tables_index)),
        "renderers": render_status or {},
        "verification": None,
        "AI_usage_report": str(project.dist_dir / "AI工具使用详情.md"),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    raws = sorted(project.data_raw.glob("*"))
    if raws:
        import hashlib
        h = hashlib.sha256()
        for p in raws:
            h.update(p.read_bytes())
        manifest["data_hash"] = h.hexdigest()[:16]
    project.dist_dir.mkdir(parents=True, exist_ok=True)
    atomic.write_json(project.dist_dir / "manifests" / "paper-manifest.json", manifest)
    return manifest


def supporting_material_manifest(project: ProjectPaths) -> dict:
    """Rule 100: every code/data/result/figure referenced must exist in the pack."""
    manifest = {"code": [], "data": [], "results": [], "figures": []}
    code_dir = project.code_dir
    if code_dir.exists():
        manifest["code"] = sorted(str(p.relative_to(project.root)) for p in code_dir.rglob("*") if p.is_file())
    for d in (project.data_raw, project.data_processed, project.data_interim):
        if d.exists():
            manifest["data"] += [str(p.relative_to(project.root)) for p in d.rglob("*") if p.is_file()]
    for f in atomic.read_jsonl(project.figures_index):
        out = f.get("output", "")
        if out:
            manifest["figures"].append({"figure_id": f.get("figure_id"), "file": out,
                                        "exists": (project.root / out).exists()})
    # Check: every registered result must have a run artifact.
    for r in atomic.read_jsonl(project.results_path):
        run_id = r.get("run_id", "")
        manifest["results"].append({"result_id": r.get("result_id"),
                                    "run_id": run_id,
                                    "artifact_exists": (project.root / "experiment_lab" / run_id / "result.json").exists()})
    out = project.root / "supporting-material-manifest.json"
    atomic.write_json(out, manifest)
    return manifest
