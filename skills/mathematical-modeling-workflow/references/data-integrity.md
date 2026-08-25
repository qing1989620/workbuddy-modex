# Data Integrity

## Immutability
- `data/raw` is read-only. Never overwrite. Source of truth.
- Derivatives: `data/interim`, `data/processed`.

## Hashing
- Every raw file: SHA256, recorded in `experiments.jsonl` `dataset_hash`.
- If data changes, prior experiments are `STALE` automatically.

## Code hash
- `experiments.jsonl` records `code_hash` so a code change invalidates results.

## Dependency graph & staleness
```
DATA -> PREPROCESS -> MODEL -> RESULT -> FIGURE/TABLE -> CLAIM
     -> CHAPTER -> ABSTRACT/CONCLUSION
```
Any upstream change marks all downstream `STALE` and forces re-verification.

## Atomic writes
Important JSON/YAML written via `atomic.py`: temp file -> fsync -> os.replace.
Prevents crash corruption of `progress.json` and ledgers.

## Schema validation
Core state files validate against Pydantic models (`src/ommw/schemas`) and JSON
Schemas (`schemas/`). The agent may not invent fields that break later reads.

## Cache policy
- Crossref/OpenAlex metadata cached locally (SQLite/JSON) with `retrieved_at`.
- Cache key includes the query hash. Hash mismatch -> re-run.
- Cache never overrides authenticity (Rule 122).

## Offline mode (`--offline`)
- Use verified cache only. Cache miss -> `UNVERIFIED_OFFLINE`, never fabricated.
