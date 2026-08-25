# Workflow

## The Problem State Machine

`ommw status` shows where a project is. Stages (full list in
`skills/mathematical-modeling-workflow/references/state-machine.md`):

```
RECEIVED -> DISCOVERY -> COMPETITION_PROFILE -> PROBLEM_DECOMPOSITION
-> DATA_AUDIT -> LITERATURE_RESEARCH -> ASSUMPTIONS -> MODEL_CANDIDATES
-> BASELINE -> MODEL_SCREENING -> FORMULATION -> IMPLEMENTATION
-> EXPERIMENT -> VALIDATION -> ROBUSTNESS -> INTERPRETATION
-> PAPER_BLUEPRINT -> CHAPTER_LOOP -> GLOBAL_AUDIT -> RENDER
-> OUTPUT_QA -> FINAL_VERIFY
```

## Per-chapter lifecycle

```
PLANNED -> EVIDENCE_READY -> DRAFTED -> MATH_REVIEWED
-> SCIENTIFIC_REVIEWED -> JUDGE_REVIEWED -> REVISED
-> CONTENT_ACCEPTED -> RENDERED -> FORMAT_VERIFIED
```

A chapter is never drafted before its evidence (Result/Source IDs) is in the
ledger (no-prose-before-evidence). Even if the user says "do it all at once",
internally you iterate chapters and each must pass its gate.

## Modes

- `latex` — agent writes `paper/latex/sections/*.tex` directly; incremental
  compile per chapter.
- `word` — `paper/word/sections/*.md` (strict pandoc-markdown) -> pandoc +
  reference.docx -> python-docx postprocessor -> verify_docx -> optional
  LibreOffice visual QA.
- `dual` — one accepted Research Core feeds both; `ommw parity` enforces
  agreement on claims/results/citations/figures/tables/equations/chapters.

## Rigor

- `quick` — narrows model-candidate breadth, literature depth, reviewer count;
  but NEVER disables Evidence Gate, numeric verification, citation
  verification, or build verification.
- `strict` (default) — deeper literature, baseline comparison, robustness,
  independent + adversarial review, dual-output cross-check if available.
- `competition` — time-budgeted; the agent compresses secondary analyses as
  time runs out but never fabricates unfinished results.
- `research` — no time limit; deeper sensitivity, alternatives, uncertainty.

## Resume

Interrupted? `ommw status` reads `progress.json` and continues from the last
completed gate. Never regenerate completed work.

## Final status block (always emitted)

```
RESEARCH:    VERIFIED
MODELING:    VERIFIED
EXPERIMENTS: VERIFIED
CITATIONS:   VERIFIED
LATEX:       VERIFIED
WORD:        NOT REQUESTED
VISUAL_QA:   VERIFIED
OVERALL:     VERIFIED
```

Never claim `VERIFIED` for something unchecked. If unsure: `NOT VERIFIED`.
