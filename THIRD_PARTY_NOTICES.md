# Third-Party Notices

This file acknowledges third-party software referenced, fetched, or vendored by
Open Mathematical Modeling Workflow (OMMW). The OMMW portable core is original
work under the MIT License. Components below are governed by their own licenses.

The canonical, machine-readable provenance record is `provenance/SOURCES.lock.json`.
This human-readable file summarizes it; when the two disagree, the lock file wins.

## A. Runtime / system dependencies (NOT redistributed by OMMW)

Users install these on their own machine. OMMW only auto-detects and invokes them.

| Component | License | Purpose |
|---|---|---|
| Python | PSF-2.0 | Runtime for the OMMW CLI |
| TeX Live | LPPL | LaTeX rendering engine |
| Pandoc | GPL-2.0-or-later | Markdown -> DOCX conversion (Word mode) |
| LibreOffice (headless) | MPL-2.0 | Optional DOCX -> PDF visual QA |
| Git | GPL-2.0 | Version control |

## B. Python packages (declared in pyproject.toml, resolved by uv)

| Package | License | Purpose |
|---|---|---|
| typer | MIT | CLI framework |
| pydantic | MIT | State schema validation |
| pyyaml | MIT | YAML state files |
| rich | MIT | Terminal output |
| python-docx | MIT | DOCX postprocessing / structural QA |
| requests | Apache-2.0 | Citation metadata retrieval (Crossref/OpenAlex) |
| pytest (dev) | MIT | Testing |

## C. External OPTIONAL providers (NOT vendored; user installs separately)

### MathModelAgent
- Upstream: https://github.com/jihe520/MathModelAgent
- License: **Personal, non-commercial use only.** ("个人免费使用，请勿商业用途，商业用途联系我（作者）")
- OMMW trust level: `EXTERNAL_OPTIONAL`
- OMMW ships ONLY an adapter (`providers/mathmodelagent/`). It never copies,
  modifies, or re-licenses MathModelAgent source. Enabling it is opt-in and
  requires the user to clone MathModelAgent separately and accept its terms.
- The OMMW core MUST remain fully functional with MathModelAgent absent.

### scientific-agent-skills (K-Dense-AI)
- Upstream: https://github.com/K-Dense-AI/scientific-agent-skills
- Repo license: MIT (Copyright (c) 2026 K-Dense Inc.)
- IMPORTANT: each skill carries its own `license` field in its SKILL.md, which
  MAY differ from the repo MIT license (e.g. docx/pdf/pptx/xlsx are Anthropic's;
  DeepSpot-M is non-commercial). OMMW fetches individual skills at a PINNED
  commit and records the per-skill license in the provenance lock. Bulk
  vendoring of the whole repo is intentionally NOT performed.

## D. Permissive skills used as research reference (NOT vendored by default)

### latex-document-skill
- Upstream: https://github.com/ndpvt-web/latex-document-skill
- License: MIT
- Used as: design reference for compile/citation-audit/CJK/visual-QA behavior.
  May be vendored on request via `ommw provider add latex-document-skill` after
  pinning a commit and recording provenance. Not vendored by default.

### latex-arxiv-SKILL (arXiv Review Paper Harness)
- Upstream: https://github.com/appautomaton/latex-arxiv-SKILL
- License: MIT (arXiv/IEEEtran specific)
- Used as: design reference for issue-driven writing, citation verification,
  no-prose-before-evidence, compile-or-not-done discipline. The OMMW workflow
  RE-IMPLEMENTS these disciplines for competition modeling; it does NOT reuse
  the arXiv/IEEE harness.

## D2. Competition template providers (NOT vendored; user installs separately)

### cumcm-template-2026 (GaoZx13470)
- Upstream: https://github.com/GaoZx13470/cumcm-template-2026 (audited 2026-08-26, commit `809cf14`)
- License: **multi-license** — template source (`.cls`/`.tex`/build scripts): **CC BY-NC-SA 4.0**
  (non-commercial, share-alike); bundled fonts: **SIL OFL 1.1**; `bib/gbt7714-numeric.bst`: **LPPL 1.3c**
  (Copyright zepinglee).
- OMMW trust level: `EXTERNAL_OPTIONAL`. **The CC BY-NC-SA non-commercial +
  share-alike terms are incompatible with the MIT core — OMMW NEVER vendors this
  template.** Users who want it clone the repo themselves. Official CUMCM rules
  always override any template.

### mcmthesis (latexstudio-org)
- Upstream: https://github.com/latexstudio-org/mcmthesis (audited 2026-08-26, commit `8ac05e2`)
- License: **LPPL v1.3c or later** (last updated 2024-01 to the 2024 official sheet format).
- OMMW trust level: `EXTERNAL_OPTIONAL`. LPPL permits use/redistribution under LPPL
  conditions; OMMW ships no mcmthesis code. COMAP official rules are re-read every
  year — never assume template defaults equal current COMAP rules.

### sci-box (jihe520)
- Upstream: https://github.com/jihe520/sci-box (audited 2026-08-26, commit `9687d2a`)
- License: **no repository-level LICENSE file found** (assets in scibox-diagram note
  Tabler Icons MIT only).
- OMMW trust level: `REFERENCE`. No code from sci-box is copied into the public
  core; its figure patterns may inform OMMW's own matplotlib backend design.

## E. Vendored assets shipped in-tree

Any asset vendored into the repository tree is listed here with its upstream
repository, pinned commit SHA, license, files used, upstream version, and local
modifications. As of this release, NO third-party source is vendored in-tree.
(The competition/LaTeX/Word templates shipped under `templates/` are original
OMMW work, CC0-1.0 for template scaffolding, see `templates/LICENSE`.)
