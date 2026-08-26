# Paper Factory & Visualization (Layer 7-8, Rule 49-71)

## Visualization
- `ommw plot` pre-registers a figure with Question / Claim / Data / Why
  (Rule 50). A figure that cannot answer these is not drawn.
- Type recommendation by claim type (data/model/experiment catalogs, Rule 51-53).
- QA: caption checks, grayscale/black-white readability (Rule 97), output
  format (PDF/SVG preferred; PNG >= 300 dpi, Rule 56).

## Paper factory
- `ommw paper-plan`: dynamic blueprint from problem types + competition profile
  (Rule 64 — no fixed template). Abstract is a placeholder until experiments
  settle; final abstract is regenerated from Verified Results (Rule 70-71).
- `ommw chapter <id>`: chapter contract binding claims/models/experiments/
  results/figures/tables/citations (Rule 67).
- `build_table_from_results`: tables generated from the Result Manifest, never
  hand-copied; `validate_table_against_results` fails on number mismatches
  (Rule 58-60).
- Red thread: Problem -> Question -> Data -> Assumption -> Model -> Experiment
  -> Evidence -> Interpretation -> Conclusion; chapters must not break the
  chain (Rule 65).

## Final audit
`ommw final-audit` runs the 13 audit dimensions (Rule 138) and writes
`paper-manifest.json` (Rule 136). `PAPER VERIFIED` only when no CRITICAL/HIGH
finding remains.
