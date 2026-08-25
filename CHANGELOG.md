# Changelog

All notable changes to Open Mathematical Modeling Workflow (OMMW) are documented
here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

OMMW versioning contract:
- **MAJOR**: workflow contract / state-schema breaking change (old projects must `ommw migrate`).
- **MINOR**: new backward-compatible capability (new renderer, provider, competition profile).
- **PATCH**: bug fix.

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
