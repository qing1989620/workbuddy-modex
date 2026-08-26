"""Competition compliance schemas (Layer 1).

A competition profile is the single source of truth for competition-specific
rules. Paper structure and renderers read this file; NOTHING is hardcoded to a
page count or rule set. Official rules > user preference > OMMW default.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class CompetitionMode(str, Enum):
    live = "LIVE"  # contest in progress: strict rules, no current-contest search
    training = "TRAINING"  # practice: past papers/solutions allowed, cite sources
    review = "REVIEW"  # reviewing own/draft work
    research = "RESEARCH"  # no contest deadline: deep study allowed


class CompetitionProfile(BaseModel):
    """Describes ONE competition entry (detected/fetched, never from model memory)."""

    competition: str = "generic"  # cumcm | mcm_icm | graduate | generic | ...
    year: int | None = None
    group: str = ""
    problem: str = ""  # A/B/C/D/E/F or problem label
    mode: CompetitionMode = CompetitionMode.training
    start_time: str = ""
    end_time: str = ""
    language: str = "zh"
    paper_format: str = "pdf"  # pdf | docx | both

    # Page budget: official rule wins (0 = unlimited / not specified).
    page_limit: int = 0
    page_limit_source: str = ""  # URL/rule id where the limit comes from

    abstract_rule: str = ""
    toc_rule: str = ""
    appendix_rule: str = ""
    reference_rule: str = ""
    supporting_material_rule: str = ""
    ai_policy: str = ""
    submission_format: list[str] = Field(default_factory=lambda: ["pdf"])
    file_size_limit: str = ""
    anonymization_rule: str = ""
    code_submission_rule: str = ""
    internet_rule: str = ""  # what web usage is forbidden (LIVE mode)

    official_sources: list[str] = Field(default_factory=list)
    verification_date: str = ""  # when rules were fetched/verified

    def effective_page_limit(self, user_preference: int | None = None, default: int = 30) -> int:
        """Official rule > user preference > OMMW default (Rule 5)."""
        if self.page_limit:
            return self.page_limit
        if user_preference:
            return user_preference
        return default

    def forbids_current_contest_search(self) -> bool:
        """LIVE mode with internet restrictions blocks current-contest content."""
        return self.mode == CompetitionMode.live and bool(self.internet_rule)
