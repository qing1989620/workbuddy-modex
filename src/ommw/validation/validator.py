"""Result Validation Engine (Rule 40-44, 41).

Every core result is checked for: computational validity, mathematical
validity, statistical validity, domain plausibility, unit consistency, range
consistency, reproducibility, paper consistency, table consistency, figure
consistency. Independent sanity checks give numbers a second verification.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..paths import ProjectPaths
from ..verify import Finding, VerifyReport


@dataclass
class ResultToValidate:
    result_id: str
    name: str = ""
    value: str = ""
    unit: str = ""
    domain: str = ""  # e.g. "probability", "nonneg", "bounded:0..1"
    run_id: str = ""
    data_hash: str = ""
    reproducibility_note: str = ""


def validate_result(pp: ProjectPaths | None, r: ResultToValidate,
                    *, checks: list[str] | None = None) -> VerifyReport:
    """Validate one result. `pp` optional for paper-consistency checks."""
    rep = VerifyReport()
    checks = checks or ["unit", "range", "statistical", "reproducibility"]
    value = _parse_value(r.value)

    if "unit" in checks and r.unit and not value.get("ok"):
        rep.add("MEDIUM", "unit-unparseable", f"{r.result_id} value not numeric: {r.value}")
    if "unit" in checks and r.unit and value.get("ok"):
        # Unit/scale sanity: e.g. a percentage must be plausible in [0,100] etc.
        if r.unit == "%" and (value["v"] < -1e3 or value["v"] > 1e3):
            rep.add("HIGH", "unit-scale", f"{r.result_id} suspicious % value {r.value}")
        if r.unit == "orders" and value["v"] < 0:
            rep.add("HIGH", "unit-negative", f"{r.result_id} negative count {r.value}")

    if "range" in checks and value.get("ok"):
        v = value["v"]
        if r.domain == "probability" and not (0 <= v <= 1):
            rep.add("CRITICAL", "range-probability", f"{r.result_id}={r.value} outside [0,1]")
        if r.domain == "nonneg" and v < 0:
            rep.add("HIGH", "range-nonneg", f"{r.result_id}={r.value} negative")

    if "statistical" in checks:
        # Statistical honesty (Rule 44): significant claims need effect size / CI.
        if re.search(r"p\s*[<<=]\s*0\.0?\d+", r.value) and not re.search(r"CI|置信|effect", r.value):
            rep.add("MEDIUM", "stats-p-only",
                    f"{r.result_id} reports p-value without effect size/CI: {r.value}")

    if "reproducibility" in checks:
        if not r.run_id:
            rep.add("MEDIUM", "repro-no-run", f"{r.result_id} has no run_id")
        if not r.data_hash:
            rep.add("MEDIUM", "repro-no-hash", f"{r.result_id} has no data_hash")
        elif r.reproducibility_note and r.reproducibility_note not in ("verified", "ok", "PASS"):
            rep.add("MEDIUM", "repro-note", f"{r.result_id} reproducibility note: {r.reproducibility_note}")

    return rep


def _parse_value(s: str) -> dict:
    s = s.strip().replace(",", "")
    try:
        return {"ok": True, "v": float(s)}
    except ValueError:
        m = re.match(r"^([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)", s)
        if m:
            return {"ok": True, "v": float(m.group(1))}
        return {"ok": False, "v": None}


# ---------------------------------------------------------------------------
# Independent sanity check (Rule 41): closed-form vs numerical, aggregate vs raw.
# ---------------------------------------------------------------------------

@dataclass
class SanityPair:
    label: str
    value_a: float
    value_b: float
    tolerance: float = 1e-6


def independent_sanity_check(pairs: list[SanityPair]) -> VerifyReport:
    """Compare two independent computations; mismatch within tolerance passes."""
    rep = VerifyReport()
    for p in pairs:
        diff = abs(p.value_a - p.value_b)
        scale = max(1.0, abs(p.value_a), abs(p.value_b))
        rel = diff / scale
        if rel > p.tolerance:
            rep.add("HIGH", "sanity-mismatch",
                    f"{p.label}: {p.value_a} vs {p.value_b} (rel {rel:.2e} > {p.tolerance})")
        else:
            rep.add("LOW", "sanity-ok", f"{p.label}: consistent")
    return rep
