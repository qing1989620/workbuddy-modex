# Architecture

OMMW is a **local-first, portable, anti-hallucination** workflow for competition
mathematical modeling. The single design principle: **the paper is never the
source of truth; the Research Core is.** LaTeX and Word are renderers of the
same accepted evidence, not parallel streams of facts.

## The five layers (Rule 2)

```
+---------------------------------------------------------------+
|  Portable Core          (MIT, no machine paths, no secrets)   |
|  src/ommw  +  skills/mathematical-modeling-workflow           |
+---------------------------------------------------------------+
        |                 |                  |
+----------------+  +-------------+  +-----------------------+
| Runtime        |  | Optional    |  | Local Config          |
| Adapters       |  | Providers   |  | config.local.toml     |
| (workbuddy...) |  | (MMA, sci)  |  | .env  (git-ignored)   |
+----------------+  +-------------+  +-----------------------+
        |
+---------------------------------------------------------------+
|  Project Workspace (decoupled; lives anywhere, even CJK paths) |
|  data/  code/  figures/  paper/{latex,word}  state/  dist/     |
+---------------------------------------------------------------+
```

- **Portable Core**: the GitHub subject. MIT, no `D:\`/`/Users/x`, no API keys,
  no competition data, no private papers. Cross-platform Python + pathlib.
- **Runtime Adapters**: thin wrappers so WorkBuddy/Claude Code/Codex can invoke
  the core. Business logic never duplicated.
- **Optional Providers**: MathModelAgent (external, non-commercial, adapter-only)
  and scientific-skills (fetch-on-demand, pinned). The core runs without them.
- **Local Configuration**: `config.local.toml` + `.env`, git-ignored. Holds
  TeX Live / Pandoc / WorkBuddy paths and any API keys.
- **Project Workspace**: the actual competition problem — data, code, paper.
  Decoupled from the core; can live at `D:\比赛\...` or `/home/x/cup2026`.

## Research Core (state as source of truth)

`workspace/state/` holds machine-readable ledgers:

```
state/
  project.yaml          mode, rigor, chapters, versions
  progress.json         Problem State Machine position (atomic)
  capabilities.json     what the workflow may honestly claim
  claims.jsonl          only SUPPORTED/VERIFIED -> conclusions
  results.jsonl         every paper number references a Result ID
  sources.jsonl         metadata vs claim verification
  experiments.jsonl     data_hash + code_hash + metrics
  figures.jsonl  tables.jsonl        result_ids linkage
  assumptions.yaml      impact + sensitivity_required
  notation.yaml         unique symbols
```

LLM prose and rendered PDF/DOCX are **derived** from these, validated back
against them, and never the source of truth.

## Anti-hallucination spine

Eight rules (see `skills/.../references/anti-hallucination.md`), enforced by:
- `ommw verify` (research linkage + orphan-number scan)
- `ommw citations verify` (metadata vs claim)
- `ommw render` (compile-or-not-done / verify_docx)
- `ommw parity` (dual-mode fingerprint agreement)
- negative-case injection in `ommw smoke-test` + the hallucination test suite

## Dependency graph & staleness

`DATA -> PREPROCESS -> MODEL -> RESULT -> FIGURE/TABLE -> CLAIM -> CHAPTER
-> ABSTRACT/CONCLUSION`. Any upstream change marks downstream `STALE`.

## Renderer independence

Renderer failure is never research failure. `RESEARCH_VERIFIED + LATEX_FAILED +
WORD_VERIFIED` is legal. All degradation is recorded in `progress.json` and
surfaced in the final status block — never silently downgraded.

## v1.0: Mathematical Modeling Research Operating System

v1.0 organizes the core into nine layers. Deterministic engines live in
`src/ommw/`; judgment stays in the agent workflow (Rule 112).

```
Layer 1  Competition Compliance  src/ommw/competition/
           profile detect/build/cache (official rules first), LIVE/TRAINING/
           REVIEW/RESEARCH modes, LIVE search gate, AI usage ledger,
           page budget (official > user > default)
Layer 3  Data Intelligence       src/ommw/data_engine/
           data audit (schema/missing/duplicates/range/units/outliers/
           impossible values), auto spec inference, audit report
Layer 4  Model Discovery         src/ommw/modeling.py
           problem-type router; baseline always present; no algorithm soup
Layer 5  Experiment Lab          src/ommw/experiment_lab/
           experiment.yaml pre-registration, portfolio planner (Rule 35),
           runner persisting result.json/metrics.csv/predictions.csv
Layer 6  Evidence & Verification src/ommw/validation/
           result validator (unit/range/statistical/reproducibility),
           independent sanity checks (closed-form vs numerical)
Layer 10 Benchmarks              src/ommw/benchmarks/
           13 negative cases + Smoke A (CUMCM) + Smoke B (MCM/ICM)
Layers 2/7/8/9 (research intelligence, visualization lab, paper factory,
publishing) are agent-driven over these engines; the Research Core ledgers
remain the single source of truth.
```

New project state files: `state/competition-profile.yaml`,
`state/ai_usage.jsonl`, `state/experiment-plan.json`, `state/model-candidates.json`,
`state/innovation-ledger.jsonl`, `experiment_lab/<id>/` artifacts.

New CLI commands (deterministic): `competition`, `audit-data`, `models`,
`plan-experiments`, `run-experiment`, `validate-results`, `ai-report`,
`judge`, `benchmark`, `reproduce`.

## What OMMW is NOT

Not 50 markdown prompts (real Python, schemas, validators, renderers, tests, CI).
Not over-engineered (no DB server, web server, microservices). Not a prize
guarantee (award-oriented engineering standard). Not a place for restrictive
third-party source inside the MIT core. Benchmarks are capability checks, not
award predictors.
