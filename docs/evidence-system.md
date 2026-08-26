# Evidence System (Layer 6, Rule 40-44, 60-62)

Every paper number must be a VERIFIED RESULT; every citation must be a VERIFIED
CITATION. The paper consumes only verified claims.

## Verification dimensions (Rule 40)
Each core result is checked for: computational validity, mathematical validity,
statistical validity, domain plausibility, unit consistency, range consistency,
reproducibility, paper/table/figure consistency.

`ommw validate-results` implements unit/range/statistical/reproducibility
checks deterministically. Independent sanity checks (Rule 41) give a second
verification path: closed-form vs numerical, solver vs constraint check,
aggregate vs raw reconstruction, model vs independent recompute.

## Evidence graph & staleness (Rule 60, 111)
`Dataset -> Experiment -> Result -> Claim -> Figure/Table -> Section ->
Abstract/Conclusion`. `ommw paper-plan` builds the graph; `propagate_stale`
marks dependents of a changed result STALE and records them in
`progress.json['stale_dependents']` for re-verification.

## Gates
- Claim ledger: only SUPPORTED/VERIFIED -> conclusions (`ommw verify`).
- Citation ledger: metadata vs claim verification (`ommw citations verify`).
- Result ledger: every numeric value in the paper references a Result ID
  (`ommw verify` orphan-number scan).
- Table factory: numbers auto-generated from the ledger; mismatches fail
  (`ommw material-manifest` + table validation).
