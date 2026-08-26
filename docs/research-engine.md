# Research Engine (Layer 2, Rule 12-15)

Research must answer real questions, not "collect keywords":

- How has this problem been studied before?
- Which model families are mainstream, and under which conditions are they valid?
- Which data sources exist? Which metrics are standard?
- Which parameters have theoretical justification?
- What are known weaknesses of prior methods?
- What is the KEY difference between this problem and prior problems?

## Search priority (Rule 13)
1. Official competition sources
2. Original academic papers
3. Publisher pages
4. DOI metadata (Crossref/OpenAlex/arXiv/Semantic Scholar)
5. Government/institutional reports
6. Official datasets
7. High-quality review papers
8. Academic books
9. Verified technical documentation
10. General webpages

Blogs/知乎/CSDN are CLUES only — never the sole basis for an important
theoretical conclusion.

## Citation zero-hallucination (Rule 14-15)
- Never generate authors/title/year/venue/DOI from memory.
- Verify: title, authors, year, venue, DOI/stable id, **claim relevance**.
- Ledger states: DISCOVERED -> METADATA_VERIFIED -> CLAIM_VERIFIED -> APPROVED /
  REJECTED. A paper existing is NOT claim support.

## LIVE mode gate (Rule 18)
Award-paper retrieval automatically excludes current-year/current-problem
content when the profile is LIVE with restrictions. Hard gate.

Deterministic support: `ommw citations verify` (metadata vs claim),
`state/ai_usage.jsonl`, `state/competition-profile.yaml`.
