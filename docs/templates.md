# Template Providers (Rule 79-84, 133)

Template providers are EXTERNAL. They are never defaulted into the MIT core;
each must pass license/commit/font/BibTeX audits and be recorded in
`provenance/SOURCES.lock.json`. Official current-year rules always beat any
template (Rule 80, 135: TEMPLATE CONFLICT -> official rules win).

## CUMCM template provider
- Upstream: `GaoZx13470/cumcm-template-2026`
- Status: **PENDING AUDIT** — must check license, commit SHA, font licenses,
  BibTeX style license before any use. Not vendored.

## MCM/ICM template provider
- Upstream: `latexstudio-org/mcmthesis`
- License: LPPL (LaTeX Project Public License).
- Status: **PENDING AUDIT** — LPPL permits use with attribution; the provider
  is external. COMAP official rules are re-read EVERY year; never assume
  template defaults equal current COMAP rules.

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
