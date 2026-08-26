"""Real matplotlib rendering backend (Layer 7, Rule 49-56).

Turns a validated FigurePlan into an actual image file (PNG by default,
PDF/SVG on request). matplotlib is an OPTIONAL dependency: when missing the
backend reports DEGRADED instead of crashing (graceful degradation, Rule 150).

Design rules applied here:
- every figure must have axis labels + units + title (Rule 55)
- PNG at >= 200 dpi; PDF/SVG preferred for vector output (Rule 56)
- deterministic output (explicit seed, no interactive backend)
- Chinese-friendly fonts when available (auto-probe), fallback English labels
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:  # optional dependency
    import matplotlib

    matplotlib.use("Agg")  # deterministic, headless
    import matplotlib.pyplot as plt

    HAVE_MPL = True
except Exception:  # pragma: no cover - environment without matplotlib
    HAVE_MPL = False


@dataclass
class RenderOutcome:
    """Result of one render attempt."""

    status: str  # RENDERED | DEGRADED | FAILED
    output: str = ""
    note: str = ""
    warnings: list[str] = field(default_factory=list)


def matplotlib_available() -> bool:
    """True when the optional matplotlib backend can actually render."""
    return HAVE_MPL


def _probe_cjk_font() -> list[str]:
    """Return matplotlib font names that can render CJK, best first.

    Probing is font-manager only (no rendering); the caller falls back to
    English labels if nothing matches.
    """
    if not HAVE_MPL:
        return []
    from matplotlib import font_manager

    candidates = [
        "Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Noto Sans SC",
        "Source Han Sans SC", "WenQuanYi Zen Hei", "PingFang SC", "Heiti SC",
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    return [c for c in candidates if c in available]


def _apply_style(labels_zh: bool) -> None:
    """Sensible scientific defaults; disable unicode minus."""
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 120
    plt.rcParams["savefig.dpi"] = 200
    plt.rcParams["font.size"] = 11
    plt.rcParams["axes.grid"] = True
    plt.rcParams["grid.alpha"] = 0.3
    plt.rcParams["axes.spines.top"] = False
    plt.rcParams["axes.spines.right"] = False
    if labels_zh:
        fonts = _probe_cjk_font()
        if fonts:
            plt.rcParams["font.family"] = fonts[0]


def _read_series_csv(path: Path) -> tuple[list[str], dict[str, list[float]]]:
    """Read a CSV into categories + series (columns after first are series)."""
    with path.open("r", encoding="utf-8-sig", errors="replace") as f:
        rows = list(csv.DictReader(f))
    cols = list(rows[0].keys()) if rows else []
    cats = [str(r[cols[0]]) for r in rows] if cols else []
    series: dict[str, list[float]] = {}
    for c in cols[1:]:
        series[c] = []
        for r in rows:
            try:
                series[c].append(float(r[c]))
            except (TypeError, ValueError):
                series[c].append(float("nan"))
    return cats, series


def _numeric(values: list[Any]) -> list[float]:
    out = []
    for v in values:
        try:
            out.append(float(v))
        except (TypeError, ValueError):
            out.append(float("nan"))
    return out


def render_figure(
    *,
    figure_type: str,
    output: Path,
    data_csv: Path | None = None,
    series: dict[str, list[float]] | None = None,
    x: list[Any] | None = None,
    y: list[Any] | None = None,
    xlabel: str = "",
    ylabel: str = "",
    unit: str = "",
    title: str = "",
    seed: int = 42,
    formats: tuple[str, ...] = ("png",),
) -> RenderOutcome:
    """Render one figure. `formats`: png/pdf/svg. Returns outcome, never raises.

    Data priority: data_csv (category + series columns) > series dict > x/y.
    """
    if not HAVE_MPL:
        return RenderOutcome("DEGRADED", note="matplotlib not installed "
                                              "(pip install ommw[plot])")
    try:
        import numpy as np  # noqa: F401  (needed by some figure types)

        warnings: list[str] = []
        labels_zh = bool(_probe_cjk_font())
        _apply_style(labels_zh)

        cats: list[str] = []
        sers: dict[str, list[float]] = {}
        if data_csv is not None and data_csv.exists():
            cats, sers = _read_series_csv(data_csv)
            if not sers:
                warnings.append("CSV has no numeric series columns")
        elif series:
            sers = {k: _numeric(v) for k, v in series.items()}
        elif x is not None and y is not None:
            sers = {"y": _numeric(y)}

        if not sers and figure_type not in ("histogram",):
            return RenderOutcome("FAILED", note=f"no numeric data for {figure_type}")

        ft = figure_type.lower()
        fig, ax = plt.subplots(figsize=(6.4, 4.2))

        if ft in ("line", "scenario-line", "convergence-line", "parameter-sweep", "trend"):
            for name, vals in sers.items():
                xs = range(len(vals)) if not cats else list(range(len(vals)))
                ax.plot(xs, vals, marker="o", markersize=3, linewidth=1.5, label=name)
            ax.set_xlabel(xlabel or ("category" if cats else "index"))
            ax.legend()
        elif ft in ("bar", "grouped-bar", "ablation-bar", "scenario-bar"):
            names = list(sers.keys())
            n = len(names)
            width = 0.8 / max(n, 1)
            for i, (name, vals) in enumerate(sers.items()):
                xs = [j + i * width for j in range(len(vals))] if n > 1 else list(range(len(vals)))
                ax.bar(xs, vals, width=width, label=name)
            if cats:
                ax.set_xticks(range(len(cats)), cats)
            ax.set_xlabel(xlabel or "category")
            ax.legend()
        elif ft in ("histogram", "kde"):
            allv = [v for vals in sers.values() for v in vals if v == v]
            if allv:
                ax.hist(allv, bins=max(10, min(50, len(set(allv)))), alpha=0.7)
            ax.set_xlabel(xlabel or "value")
        elif ft in ("box-plot", "violin"):
            data = [v for v in sers.values() if any(x == x for x in v)]
            if data:
                ax.boxplot(data, tick_labels=list(sers.keys()))
            ax.set_xlabel(xlabel or "series")
        elif ft in ("scatter", "error-bar", "interval-plot", "residual-plot"):
            vals = sers.get("y") or next(iter(sers.values()), [])
            xs = list(range(len(vals)))
            ax.scatter(xs, vals, s=18, alpha=0.8)
            ax.set_xlabel(xlabel or "index")
        elif ft == "heatmap":
            vals = list(sers.values())
            if vals:
                im = ax.imshow(vals, aspect="auto", cmap="viridis")
                ax.set_xticks(range(len(vals[0])))
                ax.set_yticks(range(len(vals)), list(sers.keys()))
                fig.colorbar(im, ax=ax)
        else:
            warnings.append(f"unsupported figure_type '{figure_type}', falling back to line")
            for name, vals in sers.items():
                ax.plot(range(len(vals)), vals, marker="o", markersize=3, label=name)
            ax.legend()

        if unit:
            ylabel = f"{ylabel} ({unit})" if ylabel else unit
        if ylabel:
            ax.set_ylabel(ylabel)
        if title:
            ax.set_title(title, fontsize=12)

        output.parent.mkdir(parents=True, exist_ok=True)
        produced = []
        for fmt in formats:
            if fmt not in ("png", "pdf", "svg"):
                warnings.append(f"unsupported format '{fmt}'")
                continue
            if fmt == "png":
                fig.savefig(output.with_suffix(".png"), dpi=200)
                produced.append(str(output.with_suffix(".png")))
            else:
                fig.savefig(output.with_suffix(f".{fmt}"), format=fmt)
                produced.append(str(output.with_suffix(f".{fmt}")))
        plt.close(fig)
        return RenderOutcome("RENDERED", output=produced[0], note=";".join(produced),
                             warnings=warnings)
    except Exception as exc:  # never crash the pipeline
        return RenderOutcome("FAILED", note=f"{type(exc).__name__}: {exc}")


def render_plan_to_file(
    plan: Any,
    output: Path,
    *,
    data_csv: Path | None = None,
    series: dict[str, list[float]] | None = None,
    xlabel: str = "",
    ylabel: str = "",
    unit: str = "",
    formats: tuple[str, ...] = ("png",),
) -> RenderOutcome:
    """Convenience wrapper: render a FigurePlan-like object."""
    return render_figure(
        figure_type=getattr(plan, "figure_type", "line"),
        output=output,
        data_csv=data_csv,
        series=series,
        xlabel=xlabel,
        ylabel=ylabel,
        unit=unit,
        title=getattr(plan, "question", "")[:60],
        formats=formats,
    )
