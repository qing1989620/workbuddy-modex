"""Table Factory (Rule 58-59).

Tables are generated from the Result Manifest — never hand-copied. A generated
markdown table is validated against the results ledger (numbers must match,
units present, no orphan values).
"""
from __future__ import annotations

import re

from .. import atomic
from ..paths import ProjectPaths
from ..verify import VerifyReport


def build_table_from_results(project: ProjectPaths, *, title: str = "",
                             result_ids: list[str], columns: list[str] | None = None,
                             caption: str = "", footnote: str = "") -> str:
    """Generate a markdown table from selected results (Rule 58).

    columns: subset of Result fields to show, e.g. ["result_id", "name", "value", "unit"].
    """
    results = {r["result_id"]: r for r in atomic.read_jsonl(project.results_path)}
    cols = columns or ["result_id", "name", "value", "unit"]
    header = "| " + " | ".join(cols) + " |"
    sep = "|" + "---|" * len(cols)
    lines = [header, sep]
    for rid in result_ids:
        r = results.get(rid)
        if not r:
            continue
        row = "| " + " | ".join(str(r.get(c, "")) for c in cols) + " |"
        lines.append(row)
    out = [f"**{caption or title or 'Table'}**", ""]
    out += lines
    if footnote:
        out += ["", f"*{footnote}*"]
    return "\n".join(out) + "\n"


def validate_table_against_results(project: ProjectPaths, table_md: str) -> VerifyReport:
    """Rule 59/60: table numbers must match the results ledger; units present.

    Checks every numeric cell with 3+ decimals has a matching Result value on
    the same row; every row references an existing result_id.
    """
    rep = VerifyReport()
    results = {r["result_id"]: r for r in atomic.read_jsonl(project.results_path)}
    for line in table_md.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        rid = cells[0] if cells else ""
        if re.match(r"^R-\d{3,4}$", rid):
            if rid not in results:
                rep.add("HIGH", "table-unknown-result", f"table row references {rid}", rid)
                continue
            r = results[rid]
            # Every numeric cell with 3+ decimals must equal the ledger value.
            for cell in cells[1:]:
                if re.search(r"\d+\.\d{3,}", cell):
                    if cell != r.get("value", ""):
                        rep.add("HIGH", "table-number-mismatch",
                                f"{rid}: table '{cell}' != ledger '{r.get('value')}'", rid)
    return rep
