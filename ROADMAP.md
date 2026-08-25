# Roadmap

OMMW targets **award-oriented engineering standards** (see `docs/architecture.md`),
not a guaranteed prize. The roadmap prioritizes the six core properties:
verifiable, reproducible, portable, maintainable, extensible, open-source.

## v0.1 — Foundation (this release)
- Portable core: config, paths, atomic writes, Pydantic state schemas.
- `ommw` CLI with doctor/init/status/verify/render/citations/results/parity/
  install-adapter/provider/migrate/smoke-test/health/package.
- Master Skill orchestrator + staged references.
- LaTeX + Word renderers with shared Research Core + dual parity gate.
- WorkBuddy adapter; MathModelAgent + scientific-skills external providers.
- JSON Schemas, test suites (incl. hallucination + portability), CI, docs,
  smoke example.

## v0.2 — Robustness
- Full Problem State Machine enforcement in `ommw status`/`verify`.
- Dependency-graph staleness propagation (DATA -> RESULT -> CLAIM -> CHAPTER).
- Adversarial reviewer harness with structured findings + closure workflow.
- Competition submission pack generator (`ommw package`) per profile rules.

## v0.3 — Providers
- `ommw provider add` / `check-updates` with pinned-commit fetch + verification.
- Optional vendoring of MIT skills (latex-document-skill) after audit.
- Additional competition profiles: cn-mcm, mcm-icm, graduate-mcm.

## v0.4 — Resilience
- Crash recovery + resume from any gate via atomic `progress.json`.
- Offline citation mode with `UNVERIFIED_OFFLINE` marking.
- Cache invalidation on data hash change.

## v1.0 — Stabilization
- Frozen state-schema v1 contract; backward-compat migration suite.
- Release gate (legal audit, secret scan, abs-path scan, lock validation,
  Windows/Linux tests, Skill validation, E2E, LaTeX/DOCX smoke, README install).
- Fresh-machine + clean-venv reproducibility attestation.

## Out of scope (by design)
- A database server, web server, message queue, or microservices.
- Bundling restrictive-license third-party source into the MIT core.
- Treating LLM prose or web text as trusted state.
- Guaranteeing competition awards.
