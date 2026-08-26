"""Paper Production Kernel -- Paper Quality Scorecard (v0.2, spec §61-§62).

Deterministic, evidence-based scoring. The score is an INTERNAL engineering
bar, not a judge simulation and not a promise of an award.

Two invariants:
  1. Critical failures override any total (a 95 with no abstract = BLOCKED).
  2. Every sub-score must cite its evidence (counts / gate findings); the
     scorer never invents points.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from .. import atomic
from ..paths import ProjectPaths
from .density import analyze_latex_dir, classify_chapter
from .gates import has_critical, run_all_paper_gates

# dimension -> weight (sums to 100; spec §61)
WEIGHTS = {
    "problem_understanding": 8,
    "mathematical_formulation": 15,
    "model_appropriateness": 10,
    "experimental_evidence": 12,
    "validation_robustness": 10,
    "visualization": 10,
    "results_interpretation": 10,
    "narrative_coherence": 8,
    "writing_quality": 5,
    "reproducibility": 5,
    "citation_integrity": 3,
    "latex_presentation": 4,
}

COMPETITION_READY_SCORE = 88
CHAPTER_APPROVED_SCORE = 85


@dataclass
class SubScore:
    dimension: str
    score: float          # 0..weight
    weight: int
    evidence: str

    @property
    def ratio(self) -> float:
        return self.score / self.weight if self.weight else 0.0


@dataclass
class Scorecard:
    subscores: list[SubScore] = field(default_factory=list)
    critical: list[tuple[str, str]] = field(default_factory=list)
    verdict: str = "BLOCKED"
    total: float = 0.0

    def finalize(self) -> None:
        self.total = round(sum(s.score for s in self.subscores), 1)
        if self.critical:
            self.verdict = "BLOCKED"
        elif self.total >= COMPETITION_READY_SCORE:
            self.verdict = "COMPETITION_READY"
        elif self.total >= CHAPTER_APPROVED_SCORE:
            self.verdict = "APPROVED"
        else:
            self.verdict = "REVISE"

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "total": self.total,
            "critical_failures": [f"{g}:{c}" for g, c in self.critical],
            "subscores": [
                {"dimension": s.dimension, "score": s.score,
                 "weight": s.weight, "evidence": s.evidence}
                for s in self.subscores
            ],
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def score_paper(pp: ProjectPaths) -> Scorecard:
    """Compute the deterministic scorecard for one project."""
    sc = Scorecard()
    reports = run_all_paper_gates(pp)
    sc.critical = has_critical(reports)
    analysis = analyze_latex_dir(pp.latex_dir)
    totals = analysis["totals"]
    sections = analysis["sections"]

    def _role_words(role: str) -> int:
        return sum(s.words for s in sections if classify_chapter(s.file) == role)

    def _gate(code_prefix: str) -> int:  # count findings whose code contains prefix
        return sum(1 for rep in reports.values() for f in rep.findings
                   if code_prefix.lower() in f.code.lower())

    model_words = _role_words("model")
    n_model = max(1, sum(1 for s in sections if classify_chapter(s.file) == "model"))

    # 1 problem understanding (8): analysis/restatement chapters carry content
    pu = 8 * _clamp(_role_words("support") / (400 * 1), 0, 1)
    sc.subscores.append(SubScore("problem_understanding", round(pu, 1), 8,
                                 f"support-chapter words={_role_words('support')}"))

    # 2 mathematical formulation (15): equations across model chapters + notation
    eq_total = sum(s.display_equations + s.inline_math for s in sections
                   if classify_chapter(s.file) == "model")
    notation_n = len((atomic.read_yaml(pp.notation_path) or {}).get("entries", []))
    mf = 15 * _clamp((eq_total / (4.0 * n_model)) * 0.75 + min(notation_n / 8, 1) * 0.25, 0, 1)
    sc.subscores.append(SubScore("mathematical_formulation", round(mf, 1), 15,
                                 f"model equations={eq_total} ({eq_total/max(n_model,1):.1f}/chapter), "
                                 f"notation entries={notation_n}, formula warnings={_gate('FORMULA_DENSITY')}"))

    # 3 model appropriateness (10): candidate matrix + selection rationale recorded
    cand_path = pp.state_dir / "model-candidates.json"
    cand = atomic.read_json(cand_path) if cand_path.exists() else []
    mc = 10 * (_clamp(len(cand) / 3, 0, 0.6) + (0.4 if len(cand) >= 2 else 0))
    sc.subscores.append(SubScore("model_appropriateness", round(mc, 1), 10,
                                 f"model-candidates recorded={len(cand)} "
                                 "(>=2 families + rationale required)"))

    # 4 experimental evidence (12): experiments ledger + coverage of claims
    exps = atomic.read_jsonl(pp.experiments_path)
    results = atomic.read_jsonl(pp.results_path)
    ee = 12 * _clamp(len(exps) / 3, 0, 0.7) + 12 * _clamp(len(results) / 6, 0, 0.3)
    ee *= 0 if any(f.code == "EXPERIMENT_EVIDENCE_MISSING"
                   for r in reports.values() for f in r.findings) else 1
    sc.subscores.append(SubScore("experimental_evidence", round(ee, 1), 12,
                                 f"experiments={len(exps)}, results={len(results)}"))

    # 5 validation & robustness (10): sensitivity/robustness chapter content
    vr_words = sum(s.words for s in sections
                   if any(k in Path(s.file).stem.lower()
                          for k in ("sensitivity", "robust", "validation")))
    vr = 10 * _clamp(vr_words / 350, 0, 1)
    sc.subscores.append(SubScore("validation_robustness", round(vr, 1), 10,
                                 f"sensitivity/robustness words={vr_words}"))

    # 6 visualization (10): visual assets minus coupling failures
    assets = totals["visual_assets"] + totals["tables"]
    coupling_pen = _gate("FIGURE_NOT_REFERENCED") + _gate("TABLE_NOT_REFERENCED") \
        + _gate("ORPHAN_FIGURE") + _gate("VISUAL_EVIDENCE_INSUFFICIENT")
    viz = 10 * _clamp(assets / 6, 0, 1) - min(coupling_pen * 1.5, 5)
    viz = _clamp(viz, 0, 10)
    sc.subscores.append(SubScore("visualization", round(viz, 1), 10,
                                 f"assets={assets} (fig {totals['figures']}+tikz {totals['tikz']}+tab {totals['tables']}), "
                                 f"coupling violations={coupling_pen}"))

    # 7 results & interpretation (10): results chapter + conclusions non-stub
    ri_words = _role_words("experiment")
    concl = next((s for s in sections if "conclusion" in s.file.lower()), None)
    ri = 10 * _clamp(ri_words / 500, 0, 0.7) + (3 if concl and concl.words > 120 else 0)
    ri = _clamp(ri, 0, 10)
    sc.subscores.append(SubScore("results_interpretation", round(ri, 1), 10,
                                 f"results-side words={ri_words}, conclusion words="
                                 f"{concl.words if concl else 0}"))

    # 8 narrative coherence (8): backbone exists + continuity warnings
    nb_ok = (pp.state_dir / "paper-narrative.md").exists()
    nc_warn = _gate("NARRATIVE_CONTINUITY")
    nc = 8 * ((0.4 if nb_ok else 0) + 0.6) - nc_warn * 2
    nc = _clamp(nc, 0, 8)
    sc.subscores.append(SubScore("narrative_coherence", round(nc, 1), 8,
                                 f"backbone={'yes' if nb_ok else 'NO'}, continuity warnings={nc_warn}"))

    # 9 writing quality (5): AI-style phrase hits across body
    ai_hits = len(totals.get("ai_style_hits", []))
    wq = _clamp(5 - ai_hits * 1.5, 0, 5)
    sc.subscores.append(SubScore("writing_quality", round(wq, 1), 5,
                                 f"AI-style phrases present: {totals.get('ai_style_hits', []) or 'none'}"))

    # 10 reproducibility (5): code dir + experiment hashes
    code_files = list(pp.code_dir.rglob("*")) if pp.code_dir.exists() else []
    hashed = sum(1 for e in exps if e.get("code_hash"))
    rp = 5 * (_clamp(len(code_files) / 3, 0, 0.5) + _clamp(hashed / max(len(exps), 1), 0, 0.5)) if exps else 0
    sc.subscores.append(SubScore("reproducibility", round(rp, 1), 5,
                                 f"code files={len(code_files)}, experiments with code_hash={hashed}/{len(exps)}"))

    # 11 citation integrity (3)
    sources = atomic.read_jsonl(pp.sources_path)
    unverified = sum(1 for s in sources if s.get("verification") == "UNVERIFIED")
    ci = _clamp(3 * _clamp(len(sources) / 3, 0, 1) - unverified * 1.5, 0, 3)
    sc.subscores.append(SubScore("citation_integrity", round(ci, 1), 3,
                                 f"sources={len(sources)}, unverified={unverified}"))

    # 12 latex presentation (4): compile ok + layout findings
    pdf = pp.latex_dir / "output" / "main.pdf"
    layout_bad = sum(1 for r in reports["latex_layout"].findings
                     if r.severity in ("HIGH", "CRITICAL"))
    lp = (2.0 if pdf.exists() else 0) + _clamp(2 - layout_bad, 0, 2)
    sc.subscores.append(SubScore("latex_presentation", round(lp, 1), 4,
                                 f"pdf={'yes' if pdf.exists() else 'NO'}, layout HIGH/CRITICAL={layout_bad}"))

    sc.finalize()
    return sc


def write_scorecard(sc: Scorecard, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(sc.to_dict(), ensure_ascii=False, indent=2),
                   encoding="utf-8")
    return out
