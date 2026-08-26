# Local Template Comparison (generated from template-registry.json)

Both archives were REALLY compiled with the local TeX Live (xelatex, relative-path invocation); statuses come from the registry, not from assumptions.

| dimension | 2025-latex-ai | latex-1 |
| --- | --- | --- |
| role (spec §13) | PRIMARY | PRIMARY |
| compile status | PASS | PASS |
| required engine | xelatex | xelatex |
| Chinese support | no | yes |
| abstract slot | YES | YES |
| keywords slot | YES | YES |
| document class | mcmthesis | cumcmthesis |
| math packages | - | - |
| algorithm/diagram | - | tikz/algorithmicx |
| bibliography | bibtex | bibtex |
| stress demo (status/pages) | PASS/4p | PASS/5p |

## Positioning

- **2025-latex-ai** (mcmthesis): *PRIMARY* — PRIMARY for MCM/ICM (English papers); Summary sheet, keywords, AI-use report environment built in.
- **latex-1** (cumcmthesis): *PRIMARY* — PRIMARY for CUMCM (全国大学生数学建模竞赛, Chinese papers); abstract+keywords in Chinese, gbt7714 bibliography.

## Selection rule (runtime)
`ommw template-select --competition cumcm --language zh` picks the CUMCM PRIMARY; `--competition mcm --language en` picks the MCM PRIMARY. Selection is registry-driven; no hardcoded paths.

> Honesty rule: every PASS above reflects an actual compile of both > the audited main tex and a generated stress-test demo.