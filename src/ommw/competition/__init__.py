"""Competition Compliance Kernel (Layer 1)."""
from __future__ import annotations

from .ai_usage import append_usage, generate_ai_report, list_usage, summarize
from .compliance import check_query_allowed, compliance_gate
from .page_budget import PageBudget, resolve as resolve_page_budget
from .profile import (
    build_profile,
    cache_rule_fetch,
    detect_competition,
    last_rule_fetch,
    load_profile,
    save_profile,
)

__all__ = [
    "append_usage",
    "build_profile",
    "cache_rule_fetch",
    "check_query_allowed",
    "compliance_gate",
    "detect_competition",
    "generate_ai_report",
    "last_rule_fetch",
    "list_usage",
    "load_profile",
    "resolve_page_budget",
    "save_profile",
    "summarize",
]
