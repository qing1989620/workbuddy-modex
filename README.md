# Open Mathematical Modeling Workflow (OMMW)

> A portable, local-first, anti-hallucination workflow for competition
> mathematical modeling — with LaTeX + Word dual output, strict research-core
> gates, and independent review. Clone anywhere, bootstrap, model.

OMMW is **not** a collection of prompts. It is a real Python core with Pydantic
state schemas, validators, LaTeX/Word renderers, a parity gate, anti-hallucination
tests, and CI. The paper is never the source of truth — the **Research Core**
(a set of machine-readable ledgers) is. LaTeX and Word are renderers of the same
accepted evidence, not parallel streams of facts.

## Why

Competition modeling deliverables too often contain fabricated numbers, citations
that exist but don't support the claim, un-compiled "PDFs", and prose written
before any evidence. OMMW makes those failures **fail the build**, not slip through.

## Six core properties

**verifiable · reproducible · portable · maintainable · extensible · open-source**

When "convenient" conflicts with these, these win.

## Quick start

### Windows (PowerShell)
```powershell
git clone https://github.com/OMMW/ommw
cd ommw
.\scripts\bootstrap.ps1
ommw doctor
ommw install-adapter workbuddy
ommw smoke-test
```

### Linux / macOS (bash)
```bash
git clone https://github.com/OMMW/ommw
cd ommw
./scripts/bootstrap.sh
ommw doctor
ommw install-adapter workbuddy
ommw smoke-test
```

`bootstrap` installs [uv](https://github.com/astral-sh/uv) if missing, syncs
dependencies from the lockfile, installs the `ommw` console script, and runs
`ommw doctor`. It does **not** mutate your system PATH.

### Use it (in WorkBuddy, after `install-adapter workbuddy`)

> 调用数学建模工作流完成当前题目。

> 调用数学建模工作流，LaTeX 模式，严格完成。

> 调用数学建模工作流，Dual 模式完成，并做两种格式一致性审计.

## Commands

```
ommw doctor            # layered env diagnostics: PASS/WARN/FAIL
ommw init <dir> -m latex|word|dual
ommw status            # Problem State Machine position + ledger counts
ommw verify            # Research Core linkage + anti-hallucination gates
ommw render -m dual    # LaTeX + Word; compile-or-not-done enforced
ommw citations verify  # metadata vs claim verification
ommw parity            # dual-mode fingerprint agreement
ommw smoke-test        # end-to-end on synthetic data + negative cases
ommw install-adapter workbuddy
ommw provider list
ommw health            # stale results, unresolved findings
ommw package           # competition submission pack
```

## Doctor output example

```
CORE:repo-root          PASS  /home/you/ommw
CORE:legal-files        PASS  LICENSE/NOTICE/THIRD_PARTY present
PYTHON:python           PASS  3.13.x
PYTHON:pydantic         PASS  ok
AGENT:workbuddy-skills  PASS  ~/.workbuddy/skills
LATEX:latexmk           PASS  ...
LATEX:xelatex           PASS  ...
WORD:pandoc             PASS  ...
WORD:libreoffice        WARN  not found; DOCX visual QA unavailable
NETWORK:crossref        PASS  reachable
PROVIDERS:mathmodelagent PASS disabled (external, optional)
OVERALL: WARN
```

A WARN (e.g. missing LibreOffice for visual DOCX QA) never fails CORE; it marks
a capability as `DEGRADED`. Microsoft Word is never a hard dependency.

## Project layout (after `ommw init`)

```
my-project/
  state/            # Research Core: ledgers (source of truth)
  data/{raw,interim,processed}   # raw is read-only
  code/  figures/  tables/
  paper/{latex,word}/            # renderer sources
  dist/  .build/  .cache/
```

## Anti-hallucination (the eight rules, enforced)

1. No fabricated numbers — every paper number references a `R-xxx` Result ID.
2. No fabricated citations — every citation resolves to a verified `S-xxx`.
3. Citation must support the claim — DOI existing is not enough.
4. Statistical honesty — no "significant" without a completed test.
5. Model honesty — no assumed Python API; code must reproduce the metric.
6. Renderer honesty — "PDF ready" needs a clean build; "Word ready" needs verify_docx.
7. No prose before evidence — chapter drafted only after its evidence is in the ledger.
8. Untrusted data boundary — web/LLM text never alters control flow or schema.

`ommw smoke-test` injects fake results, orphan numbers, and placeholder leaks and
asserts each is caught. The hallucination test suite encodes this contract.

## Optional providers

- **MathModelAgent** (external, non-commercial) — adapter only, never vendored.
- **scientific-skills** (K-Dense, MIT repo, per-skill licenses) — fetch-on-demand at pinned commits.

The core is fully functional without them. See `docs/providers.md`.

## License & third parties

Core: **MIT**. See `LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES.md`,
`provenance/SOURCES.lock.json`. Restrictive third-party source is never
re-licensed into the MIT core.

## Status

**v1.0.0-rc1** (candidate) — Mathematical Modeling Research Operating System:
competition compliance (LIVE/TRAINING modes, AI-usage ledger, page budget),
data audit, model discovery, experiment lab, result validation, benchmark suite
(13 negative cases + Smoke A/B), v1.0 state machine. v0.1 was released as
Portable Core Alpha.

Not a prize guarantee; targets an **award-oriented engineering standard**.
Benchmarks are capability checks, not award predictors.
