"""Figure & table registries (workspace/state/figures.jsonl, tables.jsonl)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class FigureRecord(BaseModel):
    figure_id: str  # e.g. F-001
    generator: str = ""  # script under code/ that produced it
    data: str = ""  # source data path/hash
    result_ids: list[str] = Field(default_factory=list)  # Result IDs plotted
    caption: str = ""
    purpose: str = ""
    section: str = ""
    output: str = ""  # relative path to the figure file


class TableRecord(BaseModel):
    table_id: str  # e.g. T-001
    generator: str = ""
    data: str = ""
    result_ids: list[str] = Field(default_factory=list)
    section: str = ""
    caption: str = ""
    output: str = ""
