# Changelog

All notable changes to Open Mathematical Modeling Workflow (OMMW) are documented
here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

OMMW versioning contract:
- **MAJOR**: workflow contract / state-schema breaking change (old projects must `ommw migrate`).
- **MINOR**: new backward-compatible capability (new renderer, provider, competition profile).
- **PATCH**: bug fix.

## [1.0.0-rc1] - 2026-08-26

### Added — Mathematical Modeling Research Operating System
- `competition/`: competition profile detect/build/cache, LIVE/TRAINING/REVIEW/
  RESEARCH modes, LIVE current-contest search hard gate, AI usage ledger + report,
  page budget engine (official > user > default), compliance gate.
- `data_engine/`: data audit (schema/missing/duplicates/range/unit/outliers) with
  auto spec inference.
- `modeling.py`: problem-type router (8 families), mandatory baseline, no
  algorithm-soup guard.
- `experiment_lab/`: experiment.yaml pre-registration, portfolio planner, runner
  persisting result.json/metrics.csv/predictions.csv.
- `validation/`: result validator (unit/range/statistical/reproducibility) +
  independent sanity checks.
- `visualization/`: figure planner (Q/C/D/Why gate) + real matplotlib backend
  (`ommw plot --render`, PNG@200dpi/PDF/SVG, CJK font probe, graceful DEGRADED).
- `paper_factory/`: dynamic blueprint, chapter contracts, consistency graph +
  stale propagation, table factory from Result Manifest.
- `knowledge/`: structured award-paper extraction + verbatim-copy detector.
- `benchmarks/`: 13 negative cases + Smoke A (CUMCM) + Smoke B (MCM/ICM).
- `health`, `final-audit` (13 dimensions), paper-manifest.json,
  supporting-material-manifest; CLI now 33 commands; doctor v2; 46-stage state machine.
- Template provider audits (2026-08-26): cumcm-template-2026 = CC BY-NC-SA 4.0
  (never vendored into MIT core) + OFL 1.1 fonts + LPPL 1.3c bst; mcmthesis =
  LPPL 1.3c+; sci-box = reference only.
- CI: benchmark job added; PR #3 (Ubuntu + Windows) green.

## [Unreleased]

### Added
- Initial portable core: config loading, state schemas (Pydantic), atomic writes.
- `ommw` CLI: `doctor`, `init`, `status`, `verify`, `render`, `citations`,
  `results`, `parity`, `install-adapter`, `provider`, `migrate`, `smoke-test`,
  `health`, `package`.
- Master Skill `mathematical-modeling-workflow` as orchestrator/control-plane.
- LaTeX renderer (xelatex/latexmk, CJK, incremental build, compile diagnosis).
- Word renderer (pandoc + reference.docx + python-docx postprocessor + verify-docx
  + LibreOffice headless visual QA with graceful degradation).
- WorkBuddy adapter (thin wrapper, symlink/junction/wrapper fallback).
- Provider system: MathModelAgent (external, non-commercial) and
  scientific-skills (pinned-commit provenance) adapters.
- JSON Schemas for project/claim/result/source/progress state.
- Test suites: unit, integration, e2e, hallucination, rendering, portability
  (absolute-path scan + Chinese-path).
- GitHub Actions CI (Windows + Ubuntu), Dependabot, issue/PR templates.
- Smoke example: synthetic city-delivery demand-forecasting-and-routing project.
- Docs: architecture, workflow, workbuddy, latex, word, providers, portability,
  troubleshooting, plus README (en) and README.zh-CN.

[Unreleased]: https://github.com/OMMW/ommw/compare/v0.1.0...HEAD
