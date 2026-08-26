# Competition Compliance & Research Discipline

Loaded when the workflow receives a competition task. Layer 1 of the
Research Operating System.

## Sequence (Rule 3)

```
DETECT COMPETITION -> DETECT YEAR -> DETECT PROBLEM -> DETECT LIVE/TRAINING
-> FETCH OFFICIAL RULES -> BUILD COMPETITION PROFILE
```

Never rely on model memory for competition rules. Run `ommw competition`
(heuristic detection) then FETCH and verify official sources; the profile
(`state/competition-profile.yaml`) records `official_sources` +
`verification_date` (Rule 134: re-fetch before each contest, cache
URL+hash+time).

## Modes (Rule 6)

- **LIVE**: contest in progress. If the profile's `internet_rule` restricts
  browsing, current-contest solution/answer/discussion content is HARD-BLOCKED.
  Legal sources only: official rules, academic literature, government/official
  statistics, public scientific databases, domain/software documentation,
  historical background. `check_query_allowed` enforces this for search queries.
- **TRAINING / REVIEW / RESEARCH**: past award papers, public solutions, and
  reviews may be studied — WITH attribution. LIVE gate excludes current-year
  current-problem material.

## Page budget (Rule 5)

`CompetitionProfile.effective_page_limit(user_pref, default)` resolves
Official rule > user preference > OMMW default. Nothing is hardcoded to
"30-40 pages".

## AI usage (Rule 7)

Every AI-assisted step appends to `state/ai_usage.jsonl`. `ommw ai-report`
generates the paper's AI-usage declaration and the detail report FROM THE
LEDGER. Never fabricated. If the profile's ai_policy requires a declaration,
`compliance_gate` fails when it is missing.

## Compliance gate (Rule 4, 75)

`ommw judge` runs compliance_gate (page limit, anonymization, AI declaration,
forbidden submission files) + research_verify. Findings are CRITICAL/HIGH/
MEDIUM/LOW. No CRITICAL/HIGH -> gate passes. This is an internal review, not
an official scoring model.

## Submission pack (Rule 99)

`ommw package` builds `submission/` per profile: filename, format, size,
anonymization, AI report, source code, data. Forbidden files fail the gate.
