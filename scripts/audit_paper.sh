#!/usr/bin/env bash
# OMMW v0.2 paper-production audit wrapper (spec section 74).
# One-click entry to every deterministic audit dimension. Each step maps to
# the corresponding CLI command; outputs land under audits/.
#
# Usage:
#   bash scripts/audit_paper.sh [PROJECT_DIR]      (default: current dir)
set -euo pipefail
PY=".venv2/Scripts/python.exe"
[ -x "$PY" ] || PY=python
PROJECT="${1:-.}"

step() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

step "1/8 structure+content gates (abstract/placeholder/visual/coupling/...)"
"$PY" -m ommw audit-paper --project "$PROJECT" --outdir "$PROJECT/audits" || true

step "2/8 chapter density report"
"$PY" - <<'EOF'
import sys; sys.path.insert(0, "src")
from pathlib import Path
from ommw.paths import ProjectPaths
from ommw.paper.density import build_density_report, write_density_report
pp = ProjectPaths(root=Path(sys.argv[1] or "."))
rep = build_density_report(pp.latex_dir)
p = write_density_report(pp.latex_dir, pp.root / "audits" / "chapter-density-report.json")
print("density ->", p)
EOF
"$PY" -m ommw audit-paper --project "$PROJECT" --outdir "$PROJECT/audits" >/dev/null 2>&1 || true

step "3/8 symbol consistency"
"$PY" - <<'EOF'
import sys; sys.path.insert(0, "src")
from pathlib import Path
from ommw.paths import ProjectPaths
from ommw.paper.gates import symbol_consistency_gate
pp = ProjectPaths(root=Path(sys.argv[1] or "."))
rep = symbol_consistency_gate(pp)
for f in rep.findings: print(f.severity, f.code, "-", f.message[:90])
EOF

step "4/8 figures (visual evidence + coupling)"
"$PY" - <<'EOF'
import sys; sys.path.insert(0, "src")
from pathlib import Path
from ommw.paths import ProjectPaths
from ommw.paper.gates import visual_evidence_gate, figure_text_coupling_gate
pp = ProjectPaths(root=Path(sys.argv[1] or "."))
for g, rep in [("visual_evidence", visual_evidence_gate(pp)),
               ("figure_text_coupling", figure_text_coupling_gate(pp))]:
    for f in rep.findings: print(g, "|", f.severity, f.code, "-", f.message[:90])
EOF

step "5/8 cross-references (latex_layout log audit)"
"$PY" - <<'EOF'
import sys; sys.path.insert(0, "src")
from pathlib import Path
from ommw.paths import ProjectPaths
from ommw.paper.gates import latex_layout_gate
pp = ProjectPaths(root=Path(sys.argv[1] or "."))
rep = latex_layout_gate(pp)
for f in rep.findings: print(f.severity, f.code, "-", f.message[:90])
EOF

step "6/8 result consistency (claims vs ledger)"
"$PY" - <<'EOF'
import sys; sys.path.insert(0, "src")
from pathlib import Path
from ommw.paths import ProjectPaths
from ommw.paper.gates import result_consistency_gate, experiment_sufficiency_gate
pp = ProjectPaths(root=Path(sys.argv[1] or "."))
for g, rep in [("result_consistency", result_consistency_gate(pp)),
               ("experiment_sufficiency", experiment_sufficiency_gate(pp))]:
    for f in rep.findings: print(g, "|", f.severity, f.code, "-", f.message[:90])
EOF

step "7/8 narrative continuity"
"$PY" - <<'EOF'
import sys; sys.path.insert(0, "src")
from pathlib import Path
from ommw.paths import ProjectPaths
from ommw.paper.gates import narrative_continuity_gate
pp = ProjectPaths(root=Path(sys.argv[1] or "."))
rep = narrative_continuity_gate(pp)
for f in rep.findings: print(f.severity, f.code, "-", f.message[:90])
EOF

step "8/8 quality scorecard (100-point, BLOCKED on critical)"
"$PY" -m ommw quality-gate --project "$PROJECT" --out "$PROJECT/audits/paper-quality-scorecard.json" || true

printf '\n\033[1mdone — reports under %s/audits/\033[0m\n' "$PROJECT"
