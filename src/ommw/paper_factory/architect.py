"""Paper Factory (Layer 8, Rule 63-71).

- paper_architect: builds a DYNAMIC paper blueprint from problem decomposition
  + competition profile (not a fixed template; Rule 64).
- chapter_contract: per-question contract binding claims/models/experiments/
  results/figures/tables/citations (Rule 67).
- consistency_graph: RESULT -> figure/table/section/abstract/conclusion edges;
  any upstream change propagates STALE downstream (Rule 60, 111).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .. import atomic
from ..paths import ProjectPaths

# Typical chapter pool; the architect selects a subset per problem (Rule 64).
CHAPTER_POOL = [
    "abstract", "introduction", "problem-restatement", "problem-analysis",
    "assumptions", "notation", "data-processing", "models",
    "experiment", "results", "validation", "sensitivity", "evaluation",
    "conclusions", "references", "appendix",
]


@dataclass
class ChapterContract:
    chapter_id: str
    question: str = ""
    purpose: str = ""
    claims: list[str] = field(default_factory=list)
    models: list[str] = field(default_factory=list)
    equations: list[str] = field(default_factory=list)
    experiments: list[str] = field(default_factory=list)
    results: list[str] = field(default_factory=list)
    figures: list[str] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    limitations: str = ""


@dataclass
class PaperBlueprint:
    title: str = ""
    competition: str = "generic"
    language: str = "zh"
    chapters: list[str] = field(default_factory=list)
    contracts: dict[str, ChapterContract] = field(default_factory=dict)
    page_limit: int = 0

    def chapter_ids(self) -> list[str]:
        return [c for c in self.chapters if c != "abstract"]


def build_blueprint(*, title: str, competition: str, language: str,
                    problem_types: list[str], page_limit: int = 0) -> PaperBlueprint:
    """Build a dynamic blueprint: chapter set depends on problem types.

    Core chapters always present; analysis/experiment/validation chapters are
    added when the problem type warrants them (no fixed template, Rule 64).
    """
    chapters = [
        "abstract", "introduction", "problem-restatement", "problem-analysis",
        "assumptions", "notation",
    ]
    if any(t in problem_types for t in ("timeseries", "spatial", "network", "classification")):
        chapters.append("data-processing")
    chapters.append("models")
    if any(t in problem_types for t in ("simulation", "optimization", "multiobjective")):
        chapters.append("experiment")
    chapters += ["results", "validation"]
    if any(t in problem_types for t in ("optimization", "timeseries", "classification")):
        chapters.append("sensitivity")
    chapters += ["evaluation", "conclusions", "references"]
    # Abstract is written LAST (Rule 70); placeholder until experiments settle.
    return PaperBlueprint(title=title, competition=competition, language=language,
                          chapters=chapters, page_limit=page_limit)


def make_chapter_contract(chapter_id: str, *, question: str = "", purpose: str = "",
                          claims: list[str] | None = None, models: list[str] | None = None,
                          results: list[str] | None = None, figures: list[str] | None = None,
                          tables: list[str] | None = None, citations: list[str] | None = None,
                          limitations: str = "") -> ChapterContract:
    return ChapterContract(
        chapter_id=chapter_id, question=question, purpose=purpose,
        claims=claims or [], models=models or [], results=results or [],
        figures=figures or [], tables=tables or [], citations=citations or [],
        limitations=limitations,
    )


def consistency_graph(project: ProjectPaths) -> dict[str, list[str]]:
    """Build RESULT -> dependents edges from the ledgers (Rule 60, 111).

    Returns {result_id: [dependent labels]}.
    """
    graph: dict[str, list[str]] = {}
    results = atomic.read_jsonl(project.results_path)

    def add(result_id: str, dep: str) -> None:
        graph.setdefault(result_id, []).append(dep)

    for r in results:
        rid = r.get("result_id")
        if not rid:
            continue
        graph.setdefault(rid, [])
    for fig in atomic.read_jsonl(project.figures_index):
        for r in fig.get("result_ids", []):
            add(r, f"figure:{fig.get('figure_id')}")
    for tbl in atomic.read_jsonl(project.tables_index):
        for r in tbl.get("result_ids", []):
            add(r, f"table:{tbl.get('table_id')}")
    for c in atomic.read_jsonl(project.claims_path):
        for r in c.get("evidence_ids", []):
            add(r, f"claim:{c.get('claim_id')}")
    return graph


def propagate_stale(project: ProjectPaths, changed_result_id: str) -> list[str]:
    """Mark dependents of a changed result STALE (Rule 111). Returns touched deps."""
    graph = consistency_graph(project)
    touched = [d for d in graph.get(changed_result_id, [])]
    # Persist staleness into progress.json for the agent to re-verify (create if absent).
    progress = atomic.read_json(project.progress_json) if project.progress_json.exists() else {}
    stale = progress.setdefault("stale_dependents", [])
    if changed_result_id not in stale:
        stale.append(changed_result_id)
    atomic.write_json(project.progress_json, progress)
    return touched
