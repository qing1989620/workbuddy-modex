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

## E. Vendored assets shipped in-tree

Any asset vendored into the repository tree is listed here with its upstream
repository, pinned commit SHA, license, files used, upstream version, and local
modifications. As of this release, NO third-party source is vendored in-tree.
(The competition/LaTeX/Word templates shipped under `templates/` are original
OMMW work, CC0-1.0 for template scaffolding, see `templates/LICENSE`.)
