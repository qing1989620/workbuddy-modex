"""Unit tests for atomic writes and path portability."""
from __future__ import annotations

import json
from pathlib import Path

from ommw import atomic
from ommw.paths import ProjectPaths, is_portable_path


def test_atomic_json_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "a" / "b" / "x.json"
    atomic.write_json(p, {"k": "v", "中文": "测试"})
    assert atomic.read_json(p) == {"k": "v", "中文": "测试"}


def test_atomic_jsonl_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "ledger.jsonl"
    atomic.write_jsonl(p, [{"id": "R-001"}, {"id": "R-002"}])
    assert [r["id"] for r in atomic.read_jsonl(p)] == ["R-001", "R-002"]
    atomic.append_jsonl(p, {"id": "R-003"})
    assert len(atomic.read_jsonl(p)) == 3


def test_yaml_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "x.yaml"
    atomic.write_yaml(p, {"a": [1, 2], "b": "中文"})
    assert atomic.read_yaml(p)["b"] == "中文"


def test_project_paths_chinese_and_spaces(tmp_path: Path) -> None:
    # Rule 10: paths with spaces and CJK must work.
    root = tmp_path / "测试 工作区" / "数学建模案例"
    pp = ProjectPaths(root=root)
    pp.ensure_dirs()
    assert pp.state_dir.exists()
    assert pp.data_raw.exists()
    atomic.write_json(pp.project_yaml, {"title": "t"})
    assert pp.project_yaml.exists()


def test_is_portable_path() -> None:
    assert is_portable_path(Path("skills/x")) is True
    assert is_portable_path(Path("a/b/c")) is True
    assert is_portable_path(Path("D:/foo")) is False
    assert is_portable_path(Path("/Users/someone/x")) is False
    assert is_portable_path(Path("/home/someone/x")) is False


def test_schema_models_validate() -> None:
    from ommw.schemas import Claim, Result, Source, ProjectYaml
    c = Claim(claim_id="C-001", statement="x", status="PROPOSED")
    assert c.status.value == "PROPOSED"
    r = Result(result_id="R-001", name="n", value="0.5")
    assert r.result_id == "R-001"
    s = Source(source_id="S-001", title="t", verification="UNVERIFIED")
    assert s.verification.value == "UNVERIFIED"
    p = ProjectYaml(title="t")
    assert p.output_mode.value == "latex"
