"""Competition profile detection/build/cache (Rule 3-5, 134).

DETECT COMPETITION -> DETECT YEAR -> DETECT PROBLEM -> DETECT MODE ->
BUILD PROFILE. Official rules are cached with URL+hash+retrieved_at and
re-fetched before each contest (Rule 134).
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass

from .. import atomic
from ..paths import ProjectPaths
from ..schemas import CompetitionMode, CompetitionProfile

CURRENT_YEAR = 2026


@dataclass
class CompetitionDetect:
    competition: str = "generic"
    year: int | None = None
    problem: str = ""
    mode: CompetitionMode = CompetitionMode.training
    confidence: str = "low"  # low | medium | high
    evidence: str = ""  # which keywords matched


def detect_competition(text: str, *, live: bool = False) -> CompetitionDetect:
    """Heuristic detection from problem text. NEVER the source of truth — the
    agent must verify against official sources before locking the profile.
    """
    t = text.lower()
    d = CompetitionDetect()
    d.year = CURRENT_YEAR
    d.mode = CompetitionMode.live if live else CompetitionMode.training
    hits: list[str] = []

    if any(k in t for k in ("cumcm", "高教社杯", "全国大学生数学建模竞赛", "国赛")):
        d.competition = "cumcm"
        hits.append("cumcm")
    elif any(k in t for k in ("mcm/icm", "mcm ", "icm ", "美赛", "comap", "mathematical contest in modeling")):
        d.competition = "mcm_icm"
        hits.append("mcm_icm")
    elif any(k in t for k in ("研究生数学建模", "中国研究生")):
        d.competition = "graduate"
        hits.append("graduate")

    # Problem label: A-F / A-G (after "问题一"/"Problem A" etc.)
    import re
    m = re.search(r"\b(?:problem|问题)\s*([a-gA-G一二三四五六七])", t)
    if m:
        d.problem = m.group(1).upper()

    if hits:
        d.confidence = "medium"
        d.evidence = ",".join(hits)
    return d


def build_profile(det: CompetitionDetect, *, official_sources: list[str] | None = None,
                  internet_rule: str = "", ai_policy: str = "",
                  page_limit: int = 0) -> CompetitionProfile:
    """Build a profile from detection + fetched official sources. Rule defaults
    are per-competition SAFE defaults; the agent must verify with the fetched
    official rules (which override everything below via editing the profile).
    """
    src = official_sources or []
    if det.competition == "cumcm":
        src = src or ["https://www.mcm.edu.cn/"]
        return CompetitionProfile(
            competition="cumcm", year=det.year, problem=det.problem, mode=det.mode,
            language="zh", page_limit=page_limit or 20,
            page_limit_source="cumcm official (fetch to verify)",
            reference_rule="GB/T 7714 style encouraged",
            ai_policy=ai_policy or "declare AI tool usage",
            submission_format=["pdf", "code"], official_sources=src,
            verification_date=time.strftime("%Y-%m-%d"),
            internet_rule=internet_rule or "no current-contest solution search",
        )
    if det.competition == "mcm_icm":
        src = src or ["https://www.contest.comap.com/"]
        return CompetitionProfile(
            competition="mcm_icm", year=det.year, problem=det.problem, mode=det.mode,
            language="en", page_limit=page_limit or 25,
            page_limit_source="COMAP official summary sheet rules",
            anonymization_rule="no personal info; no name/ID outside provided page",
            ai_policy=ai_policy or "report AI usage per COMAP AI policy",
            submission_format=["pdf", "code"], official_sources=src,
            verification_date=time.strftime("%Y-%m-%d"),
            internet_rule=internet_rule or "no current-contest solution search",
        )
    # generic fallback
    return CompetitionProfile(
        competition="generic", year=det.year, problem=det.problem, mode=det.mode,
        language="zh", page_limit=page_limit, official_sources=src,
        verification_date=time.strftime("%Y-%m-%d"),
    )


def save_profile(pp: ProjectPaths, profile: CompetitionProfile) -> None:
    atomic.write_yaml(pp.state_dir / "competition-profile.yaml", profile.model_dump(mode="json"))


def load_profile(pp: ProjectPaths) -> CompetitionProfile | None:
    p = pp.state_dir / "competition-profile.yaml"
    if not p.exists():
        return None
    return CompetitionProfile(**(atomic.read_yaml(p) or {}))


# ---------------------------------------------------------------------------
# Official rules cache (Rule 134): URL + retrieved_at + content hash.
# ---------------------------------------------------------------------------

def cache_rule_fetch(pp: ProjectPaths, url: str, content: str) -> str:
    """Record an official-rules fetch. Returns the content hash."""
    h = hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()
    cache = pp.cache_dir / "competition-rules.json"
    data = atomic.read_json(cache) if cache.exists() else {"fetches": []}
    data.setdefault("fetches", []).append({
        "url": url, "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "sha256": h,
    })
    atomic.write_json(cache, data)
    return h


def last_rule_fetch(pp: ProjectPaths, url: str) -> dict | None:
    cache = pp.cache_dir / "competition-rules.json"
    if not cache.exists():
        return None
    for f in atomic.read_json(cache).get("fetches", []):
        if f.get("url") == url:
            return f
    return None
