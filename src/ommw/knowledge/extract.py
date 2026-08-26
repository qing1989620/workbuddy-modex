"""Knowledge extraction (Rule 16-18).

Award papers (when study is permitted) are reduced to STRUCTURED knowledge —
methods, not text. Copying sentences into a new paper is forbidden and a
copy-overlap detector flags it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..verify import VerifyReport


@dataclass
class PaperKnowledge:
    """Structured knowledge extracted from an allowed historical paper."""

    source: str = ""  # paper id/path
    problem_type: str = ""
    question_decomposition: str = ""
    model_family: str = ""
    why_model_selected: str = ""
    baseline: str = ""
    experiments: list[str] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)
    validation: str = ""
    sensitivity: str = ""
    innovation: str = ""
    paper_structure: list[str] = field(default_factory=list)
    judge_strength: list[str] = field(default_factory=list)
    judge_weakness: list[str] = field(default_factory=list)
    notes: str = ""


def extract_knowledge(*, source: str, problem_type: str, model_family: str,
                      why_model_selected: str, baseline: str,
                      innovation: str, judge_strength: list[str] | None = None,
                      judge_weakness: list[str] | None = None) -> PaperKnowledge:
    """Build a structured knowledge entry. The agent fills fields from reading
    the paper; the structure forces method-level capture, not verbatim copies.
    """
    return PaperKnowledge(
        source=source, problem_type=problem_type, model_family=model_family,
        why_model_selected=why_model_selected, baseline=baseline,
        innovation=innovation, judge_strength=judge_strength or [],
        judge_weakness=judge_weakness or [],
    )


def detect_verbatim_copy(new_text: str, source_texts: list[str], *, threshold: int = 8) -> VerifyReport:
    """Copy-overlap detector (Rule 16-17): flag 8+ consecutive words copied
    verbatim from an award/source paper into the new paper.
    """
    rep = VerifyReport()

    def tokens(t: str) -> list[str]:
        import re as _re
        return _re.findall(r"[A-Za-z\u4e00-\u9fff]+", t.lower())

    ntok = tokens(new_text)
    if len(ntok) < threshold:
        return rep
    for i in range(len(ntok) - threshold + 1):
        window = " ".join(ntok[i:i + threshold])
        for src in source_texts:
            if window in " ".join(tokens(src)):
                rep.add("HIGH", "verbatim-copy",
                        f"{threshold}+ word verbatim overlap with source", "")
                return rep
    return rep


def save_knowledge_entry(kb_root: Path, entry: PaperKnowledge) -> Path:
    """Persist a structured entry under knowledge_base/problem_patterns etc."""
    import json
    out = kb_root / "problem_patterns" / f"{entry.problem_type or 'misc'}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(entry.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
