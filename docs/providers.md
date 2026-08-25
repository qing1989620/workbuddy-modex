# Providers

Providers are **optional** enhancements. The OMMW core is fully functional
without any of them (verified by `tests/integration/test_core_without_providers.py`).

## Trust levels

| Level | Meaning |
|---|---|
| `TRUSTED_CORE` | Original OMMW code, MIT, reviewed. |
| `AUDITED_VENDOR` | Permissive third-party, audited + pinned. |
| `EXTERNAL_OPTIONAL` | User-installed outside repo; restrictive license. |
| `UNTRUSTED` | Not audited; OMMW refuses to load without `--allow-untrusted`. |

## MathModelAgent — EXTERNAL_OPTIONAL

- Upstream: https://github.com/jihe520/MathModelAgent
- License: **personal, non-commercial only.**
- OMMW ships ONLY an adapter (`providers/mathmodelagent/`), never upstream
  source. Enabling is opt-in: clone separately, accept license, set
  `config.local.toml [providers.mathmodelagent] enabled=true path=<...>`.
- If it disappears, OMMW keeps modeling/coding/experimenting/writing/rendering.

## scientific-skills — AUDITED_VENDOR (fetch-on-demand)

- Upstream: https://github.com/K-Dense-AI/scientific-agent-skills (MIT repo)
- Each skill has its own `license` field that may differ from repo MIT
  (docx/pdf/pptx are Anthropic's; DeepSpot-M is non-commercial).
- OMMW fetches **individual** skills at a **pinned commit** (default `36d8f13`)
  and records per-skill license in `provenance/SOURCES.lock.json`. No bulk
  vendoring. The task router loads the relevant subset, not all at once.

## latex-document-skill & latex-arxiv-SKILL — research references

- Both MIT. Used as **design references**, not vendored by default.
- `latex-arxiv-SKILL` is arXiv/IEEEtran-specific; OMMW re-implements its
  discipline (issue-driven, no-prose-before-evidence, compile-or-not-done) for
  competition modeling rather than reusing the harness.

## Commands

```
ommw provider list                 # show providers + trust + license
ommw provider audit mathmodelagent # show recorded audit
ommw providers check-updates       # report newer commits (never auto-replace)
```

## Adding a provider (Rule 175)

fetch -> diff -> license check -> security check -> eval -> approve ->
update lock. Old pinned commits remain reproducible.
