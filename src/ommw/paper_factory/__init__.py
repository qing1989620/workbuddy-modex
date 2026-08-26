"""Paper Factory (Layer 8)."""
from __future__ import annotations

from .architect import (
    ChapterContract,
    PaperBlueprint,
    build_blueprint,
    consistency_graph,
    make_chapter_contract,
    propagate_stale,
)
from .tables import build_table_from_results, validate_table_against_results

__all__ = [
    "ChapterContract",
    "PaperBlueprint",
    "build_blueprint",
    "build_table_from_results",
    "consistency_graph",
    "make_chapter_contract",
    "propagate_stale",
    "validate_table_against_results",
]
