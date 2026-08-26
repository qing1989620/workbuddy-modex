"""Visualization Laboratory (Layer 7)."""
from __future__ import annotations

from .planner import (
    FigurePlan,
    plan_figure,
    recommend_figure_type,
    validate_figure_plan,
    validate_figure_registry_entries,
)
from .qa import check_caption, check_grayscale_readability, validate_figure_outputs

__all__ = [
    "FigurePlan",
    "check_caption",
    "check_grayscale_readability",
    "plan_figure",
    "recommend_figure_type",
    "validate_figure_outputs",
    "validate_figure_plan",
    "validate_figure_registry_entries",
]
