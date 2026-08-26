# Benchmarks (v1.0)

Internal capability checks — **not award predictors** (Rule 106).

## Negative cases (13)
| ID | Family | Detects |
|---|---|---|
| NEG-001 | citation | fake/unresolved source |
| NEG-002 | results | orphan number with no Result ID |
| NEG-003 | units | negative count |
| NEG-004 | units | probability > 1 |
| NEG-005 | figure | broken figure output file |
| NEG-006 | table | table → missing result |
| NEG-007 | claims | unverified conclusion claim |
| NEG-008 | experiment | result from STALE experiment |
| NEG-009 | compliance | page-limit violation |
| NEG-010 | compliance | missing AI declaration |
| NEG-011 | compliance | LIVE contest solution search blocked |
| NEG-012 | overengineering | simple problem must not get algorithm soup |
| NEG-013 | model-selection | simple model preferred |

## Smoke projects
- **SMOKE-A**: CUMCM-style (zh profile, `cumcm`, page limit, AI usage ledger).
- **SMOKE-B**: MCM/ICM-style (en profile, LIVE mode, anonymization rule).

Both run the full chain: profile → data → ledgers → verify → AI report.

## Usage
```
ommw benchmark                  # full suite
ommw benchmark --only NEG-001   # single case
```

## Regression policy (Rule 142)
Any change to skills/renderer/schema/model-routing must re-run the core
benchmark. `pytest` covers unit level; `ommw benchmark` covers capability
level; GitHub CI runs both.
