# scientific-skills Provider (AUDITED_VENDOR, fetch-on-demand)

## Status
- **Trust level:** `AUDITED_VENDOR` (fetched individually, per-skill license audited)
- **Upstream:** https://github.com/K-Dense-AI/scientific-agent-skills
- **Repo license:** MIT (Copyright (c) 2026 K-Dense Inc.)
- **IMPORTANT:** each skill carries its own `license` field in its SKILL.md,
  which MAY differ from the repo MIT license (e.g. docx/pdf/pptx/xlsx are
  Anthropic's; DeepSpot-M is non-commercial). OMMW fetches individual skills at
  a PINNED commit and records the per-skill license in
  `provenance/SOURCES.lock.json`. Bulk vendoring of the whole repo is
  intentionally NOT performed.

## Audited skill subset (Rule 19)
Of the 14 candidate skills, 13 exist as standalone skills (scipy is only a
dependency, not a standalone skill). Not all are loaded by default; the task
router loads the relevant subset:

| Skill | Present | Loaded when |
|---|---|---|
| scientific-writing | yes | paper writing |
| scientific-critical-thinking | yes | review |
| literature-review | yes | LITERATURE_RESEARCH |
| citation-management | yes | citation verification |
| exploratory-data-analysis | yes | DATA_AUDIT |
| statistical-analysis | yes | VALIDATION |
| experimental-design | yes | EXPERIMENT |
| peer-review | yes | review |
| sympy | yes | FORMULATION (symbolic math) |
| uncertainty-and-units | yes | VALIDATION (GUM) |
| statsmodels | yes | statistical modeling |
| scikit-learn | yes | ML models |
| networkx | yes | graph/network models |
| scipy | (dep only) | always available via numpy/scipy stack |

## Update policy (Rule 174-175)
Updates are NOT automatic. `ommw providers check-updates` only reports newer
commits. Updating requires: fetch -> diff -> license check -> security check ->
eval -> approve -> update lock. Old pinned commits remain reproducible.
