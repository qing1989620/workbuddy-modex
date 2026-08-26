"""Visualization backend tests (Layer 7, Rule 55-56): real matplotlib rendering.

Requires the `plot` extra (matplotlib+numpy). Skipped automatically when the
optional dependency is absent so CI without the extra stays green.
"""
from __future__ import annotations

import struct
from pathlib import Path

import pytest

from ommw.visualization import (
    matplotlib_available,
    render_figure,
    render_plan_to_file,
    plan_figure,
)

pytestmark = pytest.mark.skipif(
    not matplotlib_available(), reason="ommw[plot] not installed"
)


def _png_size(path: Path) -> tuple[int, int]:
    """Read PNG IHDR width/height without PIL."""
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    w, h = struct.unpack(">II", data[16:24])
    return w, h


def test_render_line_png_and_pdf(tmp_path: Path) -> None:
    out = render_figure(
        figure_type="line",
        output=tmp_path / "fig",
        series={"baseline": [10, 12, 11, 13], "model": [9, 8, 7, 6]},
        xlabel="t", ylabel="MAE", unit="orders", title="Test",
        formats=("png", "pdf"),
    )
    assert out.status == "RENDERED", out.note
    png = Path(out.output)
    assert png.exists() and png.stat().st_size > 500
    w, h = _png_size(png)
    assert w > 100 and h > 100  # high-DPI 200dpi output
    assert (tmp_path / "fig.pdf").exists()


def test_render_grouped_bar_from_csv(tmp_path: Path) -> None:
    csv_f = tmp_path / "data.csv"
    csv_f.write_text(
        "model,baseline,candidate\nA,10.0,8.5\nB,12.0,9.0\nC,11.5,7.5\n",
        encoding="utf-8",
    )
    out = render_figure(
        figure_type="grouped-bar",
        output=tmp_path / "bar",
        data_csv=csv_f,
        ylabel="MAE", unit="orders",
    )
    assert out.status == "RENDERED", out.note
    assert Path(out.output).exists()


def test_render_unsupported_type_degrades_to_line(tmp_path: Path) -> None:
    out = render_figure(
        figure_type="bogus-type",
        output=tmp_path / "f",
        series={"a": [1, 2, 3]},
    )
    assert out.status == "RENDERED"  # falls back to line with a warning
    assert any("falling back" in w for w in out.warnings)


def test_render_failed_on_no_data(tmp_path: Path) -> None:
    out = render_figure(figure_type="line", output=tmp_path / "x", series={})
    assert out.status == "FAILED"


def test_render_plan_wrapper(tmp_path: Path) -> None:
    fp = plan_figure(figure_id="F-001", question="趋势?", claim="C-001",
                     data="results", why="展示趋势", claim_type="trend")
    out = render_plan_to_file(fp, tmp_path / "w", series={"y": [1, 2, 3, 4]})
    assert out.status == "RENDERED", out.note
    assert Path(out.output).exists()
