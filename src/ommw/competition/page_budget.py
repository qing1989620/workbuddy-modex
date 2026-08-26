"""Page Budget Engine (Rule 5).

Official Competition Rule > User Preference > OMMW Default. Nothing is
hardcoded to "30-40 pages". The engine just resolves and validates.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..schemas import CompetitionProfile

DEFAULT_PAGE_LIMIT = 30  # OMMW fallback only; official rule always wins


@dataclass
class PageBudget:
    limit: int
    source: str  # official | user | default

    def within(self, pages: int) -> tuple[bool, str]:
        if self.limit <= 0:
            return True, "no limit"
        if pages <= self.limit:
            return True, f"{pages} <= {self.limit}"
        return False, f"{pages} > {self.limit}"


def resolve(profile: CompetitionProfile, user_preference: int | None = None,
            default: int = DEFAULT_PAGE_LIMIT) -> PageBudget:
    if profile.page_limit:
        return PageBudget(limit=profile.page_limit, source="official")
    if user_preference:
        return PageBudget(limit=user_preference, source="user")
    return PageBudget(limit=default, source="default")
