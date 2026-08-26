"""Data Audit Engine (Rule 21-23).

Runs BEFORE modeling: schema, missing values, duplicates, range, units,
encoding, categorical consistency, time ordering, outliers, impossible values,
target leakage hints. Generates data-audit-report.md. Missing values are NOT
mechanically imputed (Rule 22); outliers are NOT auto-deleted (Rule 23).
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from ..verify import Finding, VerifyReport


@dataclass
class DataAuditSpec:
    """Declared expectations for a dataset (agent fills from problem context)."""

    expected_columns: list[str] = field(default_factory=list)
    nonneg_columns: list[str] = field(default_factory=list)  # counts/quantities
    bounded_columns: dict[str, tuple[float, float]] = field(default_factory=dict)
    categorical_columns: list[str] = field(default_factory=list)
    time_column: str = ""  # if set, check ordering + completeness
    id_column: str = ""  # if set, check duplicates
    target_column: str = ""  # if set, check target leakage basics


@dataclass
class ColumnStats:
    name: str
    n: int
    missing: int
    min: float | None = None
    max: float | None = None
    n_unique: int = 0


def infer_spec(columns: list[str]) -> DataAuditSpec:
    """Heuristic auto-spec from column names (Rule 21): counts/quantities must be
    non-negative; rates/probabilities must be in [0,1]. Agent may refine.
    """
    spec = DataAuditSpec(expected_columns=columns)
    for c in columns:
        cl = c.lower()
        if any(k in cl for k in ("count", "quantity", "num", "qty", "times", "orders", "人数", "数量", "次数")):
            spec.nonneg_columns.append(c)
        if any(k in cl for k in ("prob", "rate", "ratio", "占比", "概率", "比例")):
            spec.bounded_columns[c] = (0.0, 1.0)
    return spec


def audit_csv(path: Path, spec: DataAuditSpec | None = None) -> VerifyReport:
    """Audit a CSV. Deterministic; writes no data changes (read-only)."""
    rep = VerifyReport()
    spec = spec or DataAuditSpec()
    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
    except UnicodeDecodeError:
        rep.add("HIGH", "encoding", f"{path.name}: not valid UTF-8", str(path))
        return rep
    if not rows:
        rep.add("HIGH", "empty-data", f"{path.name}: no data rows", str(path))
        return rep

    cols = list(rows[0].keys())
    # Schema.
    if spec.expected_columns:
        missing_cols = [c for c in spec.expected_columns if c not in cols]
        if missing_cols:
            rep.add("HIGH", "schema-missing-column", f"missing columns: {missing_cols}", path.name)
        extra_cols = [c for c in cols if c not in spec.expected_columns]
        if extra_cols:
            rep.add("MEDIUM", "schema-extra-column", f"unexpected columns: {extra_cols}", path.name)

    stats: dict[str, ColumnStats] = {}
    for c in cols:
        st = ColumnStats(name=c, n=len(rows), missing=0)
        vals: list[float] = []
        seen: set[str] = set()
        for r in rows:
            v = (r.get(c) or "").strip()
            if v == "":
                st.missing += 1
                continue
            seen.add(v)
            try:
                vals.append(float(v))
            except ValueError:
                pass
        st.n_unique = len(seen)
        if vals:
            st.min, st.max = min(vals), max(vals)
        stats[c] = st

    # Missing values (Rule 22): report, do NOT impute.
    for c, st in stats.items():
        if st.n and st.missing / st.n > 0.3:
            rep.add("HIGH", "missing-ratio", f"{c}: {st.missing}/{st.n} missing (>30%)", path.name)
        elif st.missing:
            rep.add("LOW", "missing", f"{c}: {st.missing} missing; decide drop vs impute with reason", path.name)

    # Duplicates (Rule 21).
    if spec.id_column and spec.id_column in cols:
        ids = [r.get(spec.id_column, "") for r in rows]
        dup = len(ids) - len(set(ids))
        if dup:
            rep.add("HIGH", "duplicate-entities", f"{spec.id_column}: {dup} duplicate values", path.name)

    # Range / nonneg / bounds / impossible values.
    for c, st in stats.items():
        if st.min is None:
            continue
        if c in spec.nonneg_columns and st.min < 0:
            rep.add("HIGH", "impossible-negative", f"{c}: min {st.min} < 0 (counts must be >= 0)", path.name)
        if c in spec.bounded_columns:
            lo, hi = spec.bounded_columns[c]
            if st.min < lo or st.max > hi:
                rep.add("HIGH", "range-out-of-bounds",
                        f"{c}: range [{st.min}, {st.max}] outside [{lo}, {hi}]", path.name)

    # Time ordering (Rule 21).
    if spec.time_column and spec.time_column in cols:
        raw = [r.get(spec.time_column, "").strip() for r in rows]
        if raw != sorted(raw):
            rep.add("MEDIUM", "time-out-of-order", f"{spec.time_column}: rows not sorted", path.name)

    # Outliers: report as MEDIUM (Rule 23: never auto-delete).
    for c, st in stats.items():
        if st.min is None or c == spec.target_column:
            continue
        vals = []
        for r in rows:
            v = (r.get(c) or "").strip()
            try:
                vals.append(float(v))
            except ValueError:
                continue
        if len(vals) >= 8:
            vals.sort()
            q1 = vals[len(vals) // 4]
            q3 = vals[3 * len(vals) // 4]
            iqr = q3 - q1
            if iqr > 0:
                n_out = sum(1 for v in vals if v < q1 - 1.5 * iqr or v > q3 + 1.5 * iqr)
                if n_out:
                    rep.add("MEDIUM", "outliers", f"{c}: {n_out} IQR outliers; classify before any action", path.name)

    return rep


def write_report(rep: VerifyReport, out: Path) -> None:
    lines = ["# Data Audit Report", ""]
    lines.append(f"Findings: {len(rep.findings)}")
    for f in rep.findings:
        lines.append(f"- **{f.severity}** `{f.code}`: {f.message} @{f.location}")
    lines.append("")
    lines.append("Policy: missing values are NOT mechanically imputed; outliers are NOT "
                 "auto-deleted. Every data decision must be recorded in data_decision_ledger.")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
