# Word Mode

## Pipeline
`paper/word/sections/*.md` (strict pandoc-markdown)
-> pandoc + `reference.docx`
-> python-docx **deterministic** postprocessor
-> `verify_docx` structural QA
-> (optional) LibreOffice headless docx->pdf visual QA

## Why not "AI driving Word UI"
Word mode is deterministic: Pandoc for conversion, python-docx for **style only**
(captions, spacing, numbering, headers, image sizing), never for content. This is
reproducible across machines; UI automation is not.

## reference.docx
- Project-local: `paper/word/reference.docx` (drop an official competition
  template here to override).
- Core default: `templates/word/reference.docx` (A4, 2.5cm, 12pt). Generate it
  with `python templates/word/make_reference.py`.
- If a competition official template is provided, OMMW copies it in and builds a
  template adapter; it never changes the official format (Rule 115).

## Equations
TeX math source converted by the pipeline to Word math objects. No equation
screenshots (Rule 43).

## Figures
High-DPI PNG/EMF/SVG embedded; PDF/SVG sources kept. (Rule 44)

## verify_docx (Rule 46)
Checks: valid OpenXML zip, required parts, heading hierarchy, table/figure
counts, citation count, unresolved tokens (TODO/FIXME/PLACEHOLDER/`R-???`),
duplicate/missing captions, missing Result IDs, broken internal references.

## Visual QA & fallback (Rule 47-48)
- LibreOffice headless present -> DOCX->PDF visual QA -> `VISUAL_QA: VERIFIED`.
- Absent (and no Word) -> DOCX still generated, flagged
  `DOCX STRUCTURAL QA: VERIFIED / DOCX VISUAL QA: NOT VERIFIED`. Never claim
  "Word formatting fully correct" without visual QA.
- Microsoft Word is NEVER a hard dependency.

## CSL citations
Word mode uses CSL; LaTeX uses BibTeX/BibLaTeX per competition profile. Both pull
bibliography metadata from the SAME `sources.jsonl` ledger (Rule 116).
