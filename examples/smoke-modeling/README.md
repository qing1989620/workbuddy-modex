# Smoke Example: city-delivery demand forecast & routing

A minimal, self-contained end-to-end project that exercises the **entire** chain:

```
raw data -> audit -> hash -> baseline -> model -> metrics
-> robustness -> figure -> table -> chapter -> citation
-> LaTeX -> DOCX -> parity
```

plus injected negative cases (fake result, orphan number) that the gates MUST catch.

## Run it

```bash
ommw smoke-test --dest ./_smoke --mode dual
```

(Use `--mode latex` or `--mode word` to exercise a single renderer.)

## What it produces

A project at `./_smoke` with:
- `data/raw/demand.csv` — 30 days of synthetic city-delivery demand.
- `data/processed/demand_stats.json` — mean + source hash.
- `state/` ledgers: 1 experiment, 3 results (R-001..R-003), 1 assumption,
  1 notation entry, 1 figure, 1 table, 1 verified source (real DOI),
  1 supported claim (C-001).
- `paper/{latex,word}/sections/results.*` — a chapter whose numbers reference
  the Result IDs.
- `dist/` — rendered PDF/DOCX (if TeX/Pandoc present; else DEGRADED, non-fatal).
- `dist/parity-report.json` — dual-mode fingerprint agreement.

## What it asserts

- `research_verify` PASSES on the clean state.
- Three negative injections are each caught:
  1. claim citing missing `R-999` -> `unresolved-result`
  2. orphan number with no Result anchor -> `orphan-number`
  3. (placeholder-leak covered in `tests/rendering`)
- Rendering degradation (no TeX/Pandoc) is non-fatal for the Research Core gates.
- Final line: `OVERALL: PASS`.

## Why synthetic data only

The repo never ships real competition data (Rule 100-101). This example uses
self-generated data so the pipeline is reproducible by anyone, anywhere.
