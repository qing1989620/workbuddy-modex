"""Anti-hallucination tests (Rule 105-109, 167).

These assert that the verification gates actually catch fabricated numbers,
unresolved results/sources, and orphan numbers. The smoke pipeline also injects
negative cases; here we test the gates directly.
"""
from __future__ import annotations

from pathlib import Path

from ommw import atomic
from ommw.paths import ProjectPaths
from ommw.schemas import Claim, ClaimStatus, Result, Source, SourceVerification
from ommw.verify import research_verify


def _make_project(tmp_path: Path) -> ProjectPaths:
    pp = ProjectPaths(root=tmp_path / "proj")
    pp.ensure_dirs()
    # minimal valid state
    atomic.append_jsonl(pp.results_path, Result(result_id="R-001", name="n", value="0.5").model_dump())
    atomic.append_jsonl(pp.sources_path, Source(
        source_id="S-001", title="t", verification=SourceVerification.claim_verified,
        metadata_verified=True, content_verified=True).model_dump())
    atomic.append_jsonl(pp.claims_path, Claim(
        claim_id="C-001", statement="ok", evidence_ids=["R-001"], source_ids=["S-001"],
        status=ClaimStatus.supported).model_dump())
    return pp


def test_clean_project_passes(tmp_path: Path) -> None:
    pp = _make_project(tmp_path)
    rep = research_verify(pp)
    assert rep.passed, [f.__dict__ for f in rep.findings]


def test_unresolved_result_is_caught(tmp_path: Path) -> None:
    pp = _make_project(tmp_path)
    atomic.append_jsonl(pp.claims_path, Claim(
        claim_id="C-002", statement="bad", evidence_ids=["R-999"],
        status=ClaimStatus.supported).model_dump())
    rep = research_verify(pp)
    assert any(f.code == "unresolved-result" for f in rep.findings)
    assert not rep.passed


def test_unresolved_source_is_caught(tmp_path: Path) -> None:
    pp = _make_project(tmp_path)
    atomic.append_jsonl(pp.claims_path, Claim(
        claim_id="C-003", statement="bad", source_ids=["S-999"],
        status=ClaimStatus.supported).model_dump())
    rep = research_verify(pp)
    assert any(f.code == "unresolved-source" for f in rep.findings)


def test_unverified_citation_is_caught(tmp_path: Path) -> None:
    pp = _make_project(tmp_path)
    atomic.append_jsonl(pp.sources_path, Source(
        source_id="S-002", title="t", verification=SourceVerification.unverified).model_dump())
    atomic.append_jsonl(pp.claims_path, Claim(
        claim_id="C-004", statement="bad", source_ids=["S-002"],
        status=ClaimStatus.supported).model_dump())
    rep = research_verify(pp)
    assert any(f.code == "unverified-citation" for f in rep.findings)


def test_orphan_number_is_caught(tmp_path: Path) -> None:
    pp = _make_project(tmp_path)
    (pp.word_dir / "sections").mkdir(parents=True, exist_ok=True)
    (pp.word_dir / "sections" / "results.md").write_text(
        "# Results\n\nThe accuracy was 0.9731428571 with no anchor.\n", encoding="utf-8")
    rep = research_verify(pp)
    assert any(f.code == "orphan-number" for f in rep.findings)


def test_docx_placeholder_leak_is_caught(tmp_path: Path) -> None:
    """Rule 46/48: verify_docx must flag unresolved tokens."""
    import zipfile
    from ommw.verify import verify_docx
    fake = tmp_path / "bad.docx"
    with zipfile.ZipFile(fake, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", "<w:document><w:body><TODO>leak</TODO></w:body></w:document>")
    rep = verify_docx(fake)
    assert any(f.code == "placeholder-leak" for f in rep.findings)
    assert not rep.passed
