# Security Policy

## Reporting a Vulnerability

Please report security issues privately by opening a *draft* GitHub Security
Advisory (Security tab -> "Report a vulnerability") rather than a public issue.
We aim to acknowledge within 72 hours and coordinate a fix before disclosure.

## Trust Model

OMMW is **local-first**: the core runs on your machine and only reaches the
network when you explicitly request citation metadata lookups
(Crossref/OpenAlex/arXiv). It never auto-submits papers, never pushes to git,
and never modifies your system PATH without consent.

## Skill / Plugin Trust Levels

Every skill or provider carries a trust level recorded in `provenance/SOURCES.lock.json`:

| Level | Meaning | Examples |
|---|---|---|
| `TRUSTED_CORE` | Original OMMW code, MIT-licensed, reviewed. | `src/ommw`, `skills/mathematical-modeling-workflow` |
| `AUDITED_VENDOR` | Permissive (MIT/BSD/Apache) third-party skill, audited and pinned. | (none vendored by default) |
| `EXTERNAL_OPTIONAL` | Installed by the user outside the repo; restrictive license. | MathModelAgent (non-commercial) |
| `UNTRUSTED` | Not audited. OMMW will refuse to load without explicit `--allow-untrusted`. | ad-hoc user-added skills |

## Skill Security Audit (mandatory before adding any skill)

A new skill is code that executes on your machine. Before adding one, review:
shell execution, network access, file writes/deletes, secret access, prompt
injection vectors, hidden downloads, subprocess spawning, and new dependencies.
Run `ommw provider audit <name>` to produce a report; P0 findings block install.

## Secrets

- `.env`, `config.local.toml`, and any `*.key`/`*.pem` are git-ignored.
- The CI secret-scan job fails the build on leaked tokens (OpenAI/Anthropic/
  Gemini/Tavily/Crossref/CNB/GitHub PAT patterns).
- Example/synthetic data only. Real competition data lives outside the repo.

## Untrusted Data Boundary

Web pages, paper text, and LLM outputs are **untrusted data**. They may never
alter the workflow's control flow or state schema. Citation metadata retrieved
from the network is validated against the Source schema before being written to
the ledger; unverifiable entries are marked `UNVERIFIED`, never silently trusted.
