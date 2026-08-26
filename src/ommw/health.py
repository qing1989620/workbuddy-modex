"""Project health (Rule 131): stale results/claims/figures, missing tables,
unverified citations, unclosed review findings, missing AI log,
competition-profile mismatch.
"""
from __future__ import annotations

from . import atomic
from .paths import ProjectPaths
from .schemas import ClaimStatus, SourceVerification
from .verify import VerifyReport


def health_check(project: ProjectPaths) -> VerifyReport:
    rep = VerifyReport()

    # Stale results (already in research_verify via experiments; quick pass here).
    experiments = {e.get("run_id"): e for e in atomic.read_jsonl(project.experiments_path)}
    for r in atomic.read_jsonl(project.results_path):
        run_id = r.get("run_id", "")
        if run_id and experiments.get(run_id, {}).get("status") == "STALE":
            rep.add("HIGH", "stale-result", f"result {r.get('result_id')} from STALE experiment", run_id)

    # Stale dependents recorded by propagate_stale.
    if project.progress_json.exists():
        progress = atomic.read_json(project.progress_json) or {}
        for rid in progress.get("stale_dependents", []):
            rep.add("HIGH", "stale-dependents",
                    f"result {rid} changed; dependents need re-verification", rid)

    # Claims: proposed conclusions; verified claims without used_in.
    for c in atomic.read_jsonl(project.claims_path):
        cid = c.get("claim_id", "?")
        if c.get("type") == "conclusion" and c.get("status") not in (
            ClaimStatus.supported.value, ClaimStatus.verified.value):
            rep.add("HIGH", "unverified-conclusion-claim", f"claim {cid} used as conclusion but {c.get('status')}", cid)
        if c.get("status") in (ClaimStatus.supported.value, ClaimStatus.verified.value) and not c.get("used_in"):
            rep.add("LOW", "claim-unused", f"verified claim {cid} not referenced by any section", cid)

    # Missing table / figure outputs.
    for tbl in atomic.read_jsonl(project.tables_index):
        if not tbl.get("output"):
            rep.add("MEDIUM", "missing-table-output", f"table {tbl.get('table_id')} has no output file", tbl.get("table_id", "?"))

    # Unverified citations.
    for s in atomic.read_jsonl(project.sources_path):
        if s.get("verification") == SourceVerification.unverified.value:
            rep.add("HIGH", "unverified-citation", f"source {s.get('source_id')} UNVERIFIED", s.get("source_id", "?"))

    # Unclosed review findings (if a review register exists).
    findings_path = project.state_dir / "review-findings.jsonl"
    if findings_path.exists():
        for f in atomic.read_jsonl(findings_path):
            if f.get("status") != "CLOSED" and f.get("severity") in ("CRITICAL", "HIGH"):
                rep.add("HIGH", "unclosed-finding",
                        f"finding {f.get('finding_id')} {f.get('status')}: {f.get('problem', '')[:60]}", f.get("finding_id", "?"))

    # Missing AI log (Rule 7): if the competition profile requires a declaration.
    profile_path = project.state_dir / "competition-profile.yaml"
    if profile_path.exists():
        profile = atomic.read_yaml(profile_path) or {}
        if "declare" in (profile.get("ai_policy") or "").lower():
            if not (project.paper_dir / "ai-usage-declaration.md").exists():
                rep.add("HIGH", "missing-ai-log", "profile requires AI declaration; none generated", "")

    # Competition profile mismatch with project.yaml.
    proj_path = project.project_yaml
    if proj_path.exists() and profile_path.exists():
        proj = atomic.read_yaml(proj_path) or {}
        prof = atomic.read_yaml(profile_path) or {}
        if proj.get("competition", "generic") != prof.get("competition", "generic"):
            rep.add("MEDIUM", "competition-mismatch",
                    f"project.yaml competition={proj.get('competition')} vs profile={prof.get('competition')}", "")

    return rep
