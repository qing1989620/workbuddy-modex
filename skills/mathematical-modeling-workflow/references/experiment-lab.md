# Experiment Lab & Benchmarks (v1.0)

## Experiment lifecycle (Rule 33-36)

```
PLAN (experiment.yaml: id/hypothesis/data_hash/model/params/seed/baseline/
      metric/split/success_condition)
-> EXECUTE (runner persists result.json/metrics.csv/predictions.csv)
-> VALIDATE (result validator)
-> LEDGER (results.jsonl reads from artifacts, never from chat)
```

- Portfolio is problem-driven (`ommw plan-experiments`): simple problem =
  EDA(if data)+baseline+1-2 candidates; complex = + sensitivity/robustness/
  scenario/multi-seed. NOT everything, and NOT algorithm soup.
- Cherry-picking is forbidden: all legal runs are kept; exclusions are recorded
  with reasons (Rule 36).
- Randomized methods: multiple seeds; report mean/std/median/best/worst +
  convergence + runtime (Rule 31).

## Result validation (Rule 40-44)

`ommw validate-results` checks each result for: unit/scale, range/probability,
statistical honesty (p needs effect size/CI), reproducibility (run_id +
data_hash). Independent sanity checks (closed-form vs numerical, aggregate vs
raw) give numbers a second verification (Rule 41).

## Benchmarks (Rule 101-106, 140-142)

`ommw benchmark` runs the internal capability suite:
- 13 negative cases: fake citation, orphan number, wrong unit, probability>1,
  broken figure, table->missing result, unverified conclusion, stale
  experiment, page-limit violation, missing AI declaration, LIVE-search block,
  anti-overengineering, model-simple-over-complex.
- Smoke A (CUMCM-style, zh profile) and Smoke B (MCM/ICM-style, en profile):
  full chain with competition profile + AI usage.

Benchmarks are NOT award predictors (Rule 106). They gate regressions: any
skill/renderer/schema/routing change must re-run the core benchmark (Rule 142).
