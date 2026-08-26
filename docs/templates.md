# Template Providers (Rule 79-84, 133)

Template providers are EXTERNAL. They are never defaulted into the MIT core;
each must pass license/commit/font/BibTeX audits and be recorded in
`provenance/SOURCES.lock.json`. Official current-year rules always beat any
template (Rule 80, 135: TEMPLATE CONFLICT -> official rules win).

## CUMCM template provider
- Upstream: `GaoZx13470/cumcm-template-2026` (audited 2026-08-26, commit `809cf14`)
- License: **multi-license** — template source (`.cls`/`.tex`/build scripts):
  **CC BY-NC-SA 4.0** (non-commercial + share-alike); bundled fonts: **SIL OFL 1.1**;
  `bib/gbt7714-numeric.bst`: **LPPL 1.3c** (zepinglee).
- Status: **AUDITED — EXTERNAL_OPTIONAL only**. The CC BY-NC-SA terms are
  incompatible with the MIT core: OMMW NEVER vendors this template. Users who
  want it clone the repo themselves and accept its terms. Official CUMCM rules
  always override the template.

## MCM/ICM template provider
- Upstream: `latexstudio-org/mcmthesis` (audited 2026-08-26, commit `8ac05e2`)
- License: LPPL v1.3c or later (LaTeX Project Public License); last updated
  2024-01-25 synced to the 2024 official sheet (a4paper/newtx/AI citation style).
- Status: **AUDITED — EXTERNAL_OPTIONAL**. LPPL permits use with LPPL conditions;
  the provider is external. COMAP official rules are re-read EVERY year; never
  assume template defaults equal current COMAP rules.

## Generic template (in-tree, original)
- `templates/latex/main.tex` (CJK-safe xelatex), `templates/word/reference.docx`
  (A4/2.5cm/12pt). OMMW-original scaffold, no third-party code.

## Priority (Rule 80)
```
Official current-year template
  > Official rules + validated local template
  > Audited third-party template
  > OMMW generic template
```
Third-party templates never override official rules. `ommw doctor` reports the
`TEMPLATES:competition` status; the profile's `page_limit`/rules always win.
