"""Visualization QA (Rule 55-57, 97): grayscale/black-white readability,
color accessibility, caption checks. Deterministic checks only.
"""
from __future__ import annotations

import re

from ..verify import VerifyReport


def check_caption(text: str) -> VerifyReport:
    """Caption QA: must exist, be specific, not empty boilerplate."""
    rep = VerifyReport()
    t = text.strip()
    if not t:
        rep.add("HIGH", "caption-empty", "figure/table caption is empty")
        return rep
    boilerplate = ("figure", "fig", "图", "表", "caption")
    if len(t) < 8 or (t.lower() in boilerplate):
        rep.add("MEDIUM", "caption-vague", f"caption too vague: '{t[:40]}'")
    # Data-consistency hint: captions should not hardcode numbers that look
    # like results without a Result ID (Rule 60).
    if re.search(r"\d+\.\d{3,}", t) and not re.search(r"\bR-\d{3,4}\b", t):
        rep.add("MEDIUM", "caption-orphan-number",
                "caption contains a numeric value with no Result ID")
    return rep


def check_grayscale_readability(palette: list[str]) -> VerifyReport:
    """Grayscale/black-white readability (Rule 97): if series are distinguished
    ONLY by color, they become indistinguishable when printed in grayscale.
    """
    rep = VerifyReport()
    # A palette that relies purely on hue (red/green/blue) without linestyle/
    # marker hints fails the grayscale check.
    hue_only = all(_is_pure_hue(c) for c in palette) and len(palette) >= 2
    if hue_only:
        rep.add("HIGH", "grayscale-unreadable",
                "series distinguished only by hue; add linestyle/marker/pattern")
    return rep


def _is_pure_hue(color: str) -> bool:
    c = color.lower()
    return c in ("red", "green", "blue", "cyan", "magenta", "yellow",
                 "orangered", "lime", "teal") or c.startswith("#")


def validate_figure_outputs(registry: list[dict]) -> VerifyReport:
    """Figure output format QA (Rule 56): prefer PDF/SVG; PNG must be high-DPI
    (a 'screenshot-like' low-res PNG is flagged)."""
    rep = VerifyReport()
    for e in registry:
        out = (e.get("output") or "").lower()
        fid = e.get("figure_id", "?")
        if out.endswith(".png") and not (e.get("dpi") or 0) >= 300:
            rep.add("MEDIUM", "fig-low-res-png",
                    f"{fid}: PNG without dpi>=300; prefer PDF/SVG or high-DPI PNG", fid)
    return rep
