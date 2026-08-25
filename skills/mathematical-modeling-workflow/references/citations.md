# Citations: Metadata vs Claim Verification

## Two tiers (Rule 26)
1. **Metadata verification** — the source actually exists (Crossref/OpenAlex/arXiv).
2. **Claim verification** — the source actually supports the cited claim.

A DOI existing is NOT sufficient. Both tiers must pass for a citation to back a
conclusion.

## Retrieval order
Crossref, OpenAlex, arXiv, PubMed (when applicable), publisher, official
reports. Google Scholar may help discovery but is NOT sole scientific evidence.
Search-result snippets are never the only evidence.

## Source schema fields
`source_id, title, authors, year, venue, doi, url, retrieved_at,
metadata_verified, content_verified, verification, claims_supported`

`verification` enum: `UNVERIFIED | METADATA_VERIFIED | CLAIM_VERIFIED |
UNVERIFIED_OFFLINE`.

## Local cache
Metadata cached with `retrieved_at` to reduce repeated network calls.

## Offline mode
Cache miss -> `UNVERIFIED_OFFLINE`. Never fabricate a source.

## CSL vs BibTeX
- Word mode: CSL citation style.
- LaTeX mode: BibTeX/BibLaTeX per competition profile.
- Both bibliography metadata come from the SAME `sources.jsonl` ledger.
