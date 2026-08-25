# Troubleshooting

## `ommw doctor` says FAIL
- `CORE:legal-files FAIL` -> missing LICENSE/NOTICE/THIRD_PARTY_NOTICES; you're
  not at the repo root or the files were removed.
- `PYTHON:pydantic FAIL` -> run `uv sync` (or `pip install -e ".[dev]"`).
- `LATEX:texlive FAIL` -> set `TEXLIVE_HOME` or `[latex] texlive_root`.
- `WORD:pandoc WARN` -> install Pandoc (Word mode needs it). Visual QA also needs
  LibreOffice.
- `AGENT:workbuddy-skills WARN` -> set `WORKBUDDY_SKILLS_DIR` or
  `[workbuddy] skills_dir`.

## `ommw verify` fails
- `unresolved-result` (CRITICAL) -> a claim cites a `R-xxx` not in
  `state/results.jsonl`. Add the result or fix the claim.
- `unresolved-source` (CRITICAL) -> a citation cites a `S-xxx` not in
  `state/sources.jsonl`.
- `unverified-citation` (HIGH) -> source is `UNVERIFIED`; run
  `ommw citations verify` and confirm claim support.
- `orphan-number` (MEDIUM) -> a numeric value in prose lacks a nearby Result ID.

## `ommw render` says FAILED
- LaTeX: check `paper/latex/output/main.log`. Undefined citations -> verify
  sources. Fatal errors -> fix the `.tex`. Renderer failure is NOT research
  failure; the ledgers are still valid.
- Word: `structural_qa FAILED` -> see the finding codes (placeholder-leak,
  missing-part, no-headings). Fix the section markdown.

## `ommw parity` MISMATCH
LaTeX and Word fingerprints disagree on claims/results/citations/figures/tables/
chapters. Both renderers must derive from the SAME accepted Research Core; do not
maintain facts separately. Re-accept the chapter and re-render.

## Windows symlink denied for `install-adapter`
The adapter falls back to junction, then to a thin wrapper copy. All three are
valid; the wrapper always references the repo. Re-run after edits to refresh.

## pip upgrade blocked by sandbox
If `pip install --upgrade pip` fails with `windows-sandbox-recycle-bin-unavailable`,
skip the upgrade — Python 3.12+ venv ships a recent pip. Just
`pip install -e ".[dev]"`.
