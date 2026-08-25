# State Machine & Resume

## Stages (in order)

```
RECEIVED
DISCOVERY                read the problem verbatim; preserve user's terms
COMPETITION_PROFILE      pick templates/competition/<profile>; page/section rules
PROBLEM_DECOMPOSITION    split into sub-questions Q1..Qn; record in project.yaml
DATA_AUDIT               hash raw data (SHA256); mark data/raw read-only
LITERATURE_RESEARCH      Crossref/OpenAlex/arXiv first; cache metadata; offline flag
ASSUMPTIONS              each assumption gets impact + sensitivity_required flag
MODEL_CANDIDATES         2-5 model families; comparison matrix; state WHY chosen
BASELINE                 mandatory baseline; complex models cannot claim "excellent"
MODEL_SCREENING          pick winner on evidence, not aesthetics
FORMULATION              full math formulation; notation.yaml unique symbols
IMPLEMENTATION           code under code/; deterministic seeds; record env
EXPERIMENT               experiments.jsonl: data_hash + code_hash + metrics
VALIDATION               statistical gate: assumptions/effect-size/CI/sample/multiple-testing
ROBUSTNESS               relevant subset only; multi-seed for randomized
INTERPRETATION           what the numbers mean; do not overclaim
PAPER_BLUEPRINT          chapter contract shared by both renderers
CHAPTER_LOOP             per-chapter: evidence -> draft -> 3 reviews -> accept -> render
GLOBAL_AUDIT             cross-chapter consistency; abstract last; conclusion audit
RENDER                   latex/word/dual; compile-or-not-done; verify_docx
OUTPUT_QA                parity (dual); visual QA; no placeholders/leaks
FINAL_VERIFY             emit the final status block; nothing claimed unverified
```

## Resume rules

- `ommw status` reads `progress.json` (current_stage + completed_stages).
- Continue from the last completed gate. Never regenerate completed work.
- Atomic writes (`atomic.py`) prevent crash corruption.
- If `progress.json` is missing/corrupt, refuse to fabricate progress; report.

## Staleness propagation

Dependency graph: `DATA -> PREPROCESS -> MODEL -> RESULT -> FIGURE/TABLE
-> CLAIM -> CHAPTER -> ABSTRACT/CONCLUSION`. Any upstream change marks all
downstream `STALE` and requires re-verification (Rule 58).
