"""Rendering tests (may degrade if TeX/pandoc absent; structural QA still tested)."""
from __future__ import annotations

import zipfile
from pathlib import Path

from ommw import atomic
from ommw.config import Config, LatexConfig, WordConfig
from ommw.paths import ProjectPaths
from ommw.render import WordRenderer
from ommw.verify import verify_docx


def _word_project(tmp_path: Path) -> ProjectPaths:
    pp = ProjectPaths(root=tmp_path / "w")
    pp.ensure_dirs()
    (pp.word_dir / "sections").mkdir(parents=True, exist_ok=True)
    (pp.word_dir / "sections" / "intro.md").write_text(
        "# Introduction\n\nA claim supported by R-001 and S-001.\n", encoding="utf-8")
    return pp


def test_verify_docx_on_minimal_docx(tmp_path: Path) -> None:
    """A well-formed minimal docx passes structural QA."""
    docx = tmp_path / "ok.docx"
    with zipfile.ZipFile(docx, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml",
                   '<w:document xmlns:w="x"><w:body>'
                   '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr></w:p>'
                   '</w:body></w:document>')
    rep = verify_docx(docx)
    assert rep.passed
