# MathModelAgent Provider (EXTERNAL_OPTIONAL)

## Status
- **Trust level:** `EXTERNAL_OPTIONAL`
- **Upstream:** https://github.com/jihe520/MathModelAgent
- **License:** Personal, non-commercial use only.
  ("个人免费使用，请勿商业用途，商业用途联系我（作者）")
- **OMMW relationship:** OMMW ships ONLY this adapter. It NEVER copies,
  modifies, or re-licenses MathModelAgent source. The OMMW core is fully
  functional with MathModelAgent absent; enabling it is opt-in enhancement.

## What it adds (when enabled)
- End-to-end multi-agent modeling (modeling/coding/paper agents).
- 17 Typst/LaTeX competition templates.
- 9-step acceptance + 4-layer fault tolerance + human-in-the-loop gates.
- RAG knowledge base (ChromaDB) of modeling methods.

## Enabling
1. Clone MathModelAgent separately and accept its non-commercial license:
   `git clone https://github.com/jihe520/MathModelAgent <path>`
2. In `config.local.toml`:
   ```toml
   [providers.mathmodelagent]
   enabled = true
   path = "<path>"
   ```
3. `ommw provider audit mathmodelagent` shows the recorded audit.
4. `ommw doctor` reports the provider as PASS at the configured path.

## What this directory contains
- `provider.toml` — declarative provider descriptor.
- `detect.py` — locate a local MathModelAgent install (no network).
- `adapter.py` — a thin interface describing how OMMW *would* call it.
  It contains NO upstream code; only adapter contracts and provenance notes.

## If MathModelAgent disappears
OMMW continues to analyze problems, model, code, experiment, write, and render
LaTeX/Word, because the core orchestration belongs to OMMW (Rule 173). This
provider is an enhancement, never a single point of failure.
