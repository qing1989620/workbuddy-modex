# Contributing to OMMW

Thanks for considering a contribution. OMMW is a portable, local-first
mathematical-modeling workflow; keep contributions consistent with the six
core properties: **verifiable, reproducible, portable, maintainable,
extensible, open-source**.

## Quick contribution paths

- **Competition template** -> add under `templates/competition/<profile>/` with
  a `profile.toml`, a LaTeX skeleton, and a `reference.docx`. See
  `templates/competition/generic/` for the contract.
- **Renderer improvement** -> `renderers/` + `src/ommw/render/`. Renderers must
  share the Research Core and must not fabricate facts (see
  `docs/architecture.md`).
- **Provider** -> `providers/<name>/` with `provider.toml`, `detect.py`,
  `adapter.py`, and a provenance entry in `provenance/SOURCES.lock.json`.
  External/restrictive-license providers stay out-of-tree adapters only.
- **Modeling method / Skill reference** -> `skills/mathematical-modeling-workflow/references/`.
- **Test** -> add under `tests/<suite>/`. Anti-hallucination and portability
  suites are first-class; prefer them over yet-another-happy-path.

## Development setup

```bash
git clone <repo> && cd ommw
# Python 3.12+ required. Use uv for reproducible deps.
uv sync --frozen
uv run pytest
uv run ommw doctor
```

Windows (PowerShell) and Linux/macOS (bash) bootstrap wrappers exist under
`scripts/`; the canonical logic lives in the cross-platform `ommw` CLI.

## Before opening a PR

1. `uv run ruff check .` and `uv run ruff format --check .` pass.
2. `uv run pytest` passes, including portability and hallucination suites.
3. No absolute machine paths leaked (CI portability job enforces this).
4. No secrets committed (CI secret-scan enforces this).
5. If you add a dependency, update `uv.lock` and justify it in the PR.
6. If you add a third-party skill, record provenance with a pinned commit
   SHA and license; non-permissive licenses are not vendored.

## Commit & PR style

- Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`).
- Small, reviewable PRs. One logical change per PR.
- Don't bypass hooks (`--no-verify`) or signing without explicit maintainer ask.

## License

By contributing you agree your contributions are licensed under the project's
MIT License. Third-party code you bring in must keep its own license and be
recorded in `THIRD_PARTY_NOTICES.md` + `provenance/SOURCES.lock.json`.
