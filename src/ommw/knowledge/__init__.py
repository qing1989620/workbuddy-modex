"""Knowledge Base (Rule 16-18, 107-109)."""
from __future__ import annotations

from .extract import (
    PaperKnowledge,
    detect_verbatim_copy,
    extract_knowledge,
    save_knowledge_entry,
)

__all__ = ["PaperKnowledge", "detect_verbatim_copy", "extract_knowledge", "save_knowledge_entry"]
