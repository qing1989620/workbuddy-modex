# Paper-production eval report

- generated: 2026-08-26T21:54:27
- cases: 10, failures: 0

| case | result | mutation |
|---|---|---|
| EV01-missing-abstract | PASS | abstract emptied in BOTH renderers |
| EV02-thin-question-chapter | PASS | models chapter reduced to a comment stub |
| EV03-text-only-algorithm | PASS | model chapter is prose-only algorithm, zero display equations |
| EV04-figure-without-discussion | PASS | every textual reference to fig:forecast removed |
| EV05-unsupported-result-claim | PASS | floating percentage claim with no Result-ID anchor |
| EV06-disconnected-questions | PASS | declared models->results coupling with no shared evidence |
| EV07-bad-layout-overfull | PASS | real xelatex run produced layout_probe.log/pdf as output/main.* |
| EV08-formula-inflation | PASS | 45 near-identical equations with thin prose in ONE chapter only |
| EV09-missing-visualization | PASS | all figure/table environments and registry entries removed |
| EV10-excellent-compact-paper | PASS | base untouched |