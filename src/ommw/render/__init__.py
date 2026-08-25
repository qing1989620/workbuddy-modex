"""Renderers share the Research Core; only the排版 source differs.

  latex/ -> paper/latex/*.tex      (agent writes .tex directly)
  word/  -> paper/word/*.md -> .docx (pandoc + python-docx postprocessor)

Facts are never maintained separately across renderers (Rule 35).
"""
from __future__ import annotations

from .latex import LatexRenderer, LatexResult
from .word import WordRenderer, WordResult

__all__ = ["LatexRenderer", "LatexResult", "WordRenderer", "WordResult"]
