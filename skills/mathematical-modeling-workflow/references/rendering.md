# Rendering: LaTeX + Word + Dual

## Shared (both renderers derive from the same Research Core)
raw data, processed data, programs, models, assumptions, results, claims,
references, figures, tables, notation, chapter contracts, review findings.
**Facts are never maintained separately across renderers.**

## LaTeX mode
- Agent writes `paper/latex/sections/*.tex` directly (not a one-shot conversion).
- Incremental per chapter: draft -> audit -> add to LaTeX -> compile -> inspect
  log -> fix -> recompile -> chapter pass.
- Engine: xelatex default (CJK-safe). Auto-detect TeX Live bin; prepend to PATH
  for the subprocess only (never mutate global PATH).
- Compile-or-not-done: "PDF ready" = clean build + zero undefined citations.
- CJK via `xeCJK`; figures as PDF/SVG; tables via `booktabs`.

## Word mode
- Source: `paper/word/sections/*.md` (strict pandoc-markdown).
- Pipeline: pandoc + `reference.docx` -> python-docx **deterministic**
  postprocessor (styles, captions, spacing, numbering, headers, image sizing)
  -> `verify_docx` structural QA -> (optional) LibreOffice headless docx->pdf
  visual QA.
- python-docx never modifies research content, only presentation.
- Equations: TeX math source converted by the pipeline; no equation screenshots.
- Figures: high-DPI PNG/EMF/SVG; keep PDF/SVG sources.
- Microsoft Word is never a hard dependency.

## Dual mode
- One accepted Research Core feeds both renderers (no separate rewriting).
- `ommw parity` enforces agreement on: claim IDs, result IDs, citations,
  equation count, figure IDs, table IDs, chapter structure, conclusion values.
- Binary equality of PDF/DOCX is NOT required (non-deterministic metadata,
  timestamps, zip ordering). Reproducibility is structural, not binary.

## Renderer failure != research failure
`RESEARCH_VERIFIED + LATEX_FAILED + WORD_VERIFIED` is a legal state. A renderer
failure is never misreported as a model/research failure. All degradation is
written to `progress.json` `degraded[]` and surfaced in the final status block.

## Word visual QA fallback
If LibreOffice absent and Word absent: DOCX still generated, but flagged
`DOCX STRUCTURAL QA: VERIFIED / DOCX VISUAL QA: NOT VERIFIED`. Never claim
"Word formatting fully correct" without visual QA.

## Build manifest (Rule 117)
Each render writes `dist/manifests/build-manifest.json`: workflow_version,
project_version, mode, dataset_hashes, code_commit, result_manifest_hash,
citation_manifest_hash, renderer_version, tool_versions, timestamp, status.
