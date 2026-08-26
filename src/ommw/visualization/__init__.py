"""Visualization Laboratory (Layer 7)."""
from __future__ import annotations

from .backend import RenderOutcome, matplotlib_available, render_figure, render_plan_to_file
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
    "RenderOutcome",
    "check_caption",
    "check_grayscale_readability",
    "matplotlib_available",
    "plan_figure",
    "recommend_figure_type",
    "render_figure",
    "render_plan_to_file",
    "validate_figure_outputs",
    "validate_figure_plan",
    "validate_figure_registry_entries",
]
