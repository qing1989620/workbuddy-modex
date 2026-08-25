"""Generate a minimal reference.docx for Word mode (Rule 42).

Run:  python templates/word/make_reference.py
Creates templates/word/reference.docx with competition-standard styles:
A4, 2.5cm margins, 12pt body, heading styles. This is OMMW-original scaffold
(CCO-1.0 for templates); users may replace it with an official competition template.
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.shared import Cm, Pt


def build(out: Path) -> None:
    doc = Document()
    # Page setup: A4, 2.5cm margins.
    for section in doc.sections:
        section.page_height = Cm(29.7)
        section.page_width = Cm(21.0)
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    # Normal style: 12pt.
    normal = doc.styles["Normal"]
    normal.font.size = Pt(12)
    normal.font.name = "Times New Roman"

    # Heading styles.
    for name, size in (("Heading 1", 16), ("Heading 2", 14), ("Heading 3", 12)):
        try:
            doc.styles[name].font.size = Pt(size)
            doc.styles[name].font.bold = True
        except KeyError:
            pass

    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))


if __name__ == "__main__":
    build(Path(__file__).resolve().parent / "reference.docx")
    print("reference.docx generated")
