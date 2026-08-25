# Modeling Discipline

## Model candidate generation
- Per sub-question: 2-5 model **families** (not 10 near-duplicates).
- Build a comparison matrix: assumptions, complexity, data needs, expected
  behavior, failure modes, interpretability.
- State *why* the winner was chosen, on evidence, not aesthetics.

## Baseline (mandatory)
- Prediction/classification/optimization/evaluation: a reasonable baseline is
  required. No baseline -> a complex model may not claim "excellent".
- Examples: mean/last-value forecaster, majority class, greedy heuristic,
  naive LP relaxation.

## Complexity budget
For every added layer/feature, answer:
1. What real problem does it solve?
2. What measurable gain does it bring?
3. What new assumption does it introduce?
4. What new risk does it carry?
No measurable gain -> delete it.

## Optimization recognition
Recognize first: LP, QP, MILP, convex, network flow, DP, nonlinear.
Prefer mature solvers. Do NOT reach for GA/PSO/ACO/SA just to look advanced —
use them only when the problem is genuinely non-convex/black-box and a
deterministic solver is inapplicable, and then report multi-seed statistics.

## Randomized algorithms
- Multiple seeds (>=5 recommended).
- Report mean, std, best, worst. Never cherry-pick best.
- Record seeds in `experiments.jsonl`.

## Time series
- Default: no random split (data leakage).
- Use time-based, rolling, or expanding splits.

## Statistical gate
Any statistical conclusion checks: distribution assumptions, effect size,
confidence interval, sample size, multiple-testing correction.
`p < 0.05` is never "proof". "Significant" requires an actual completed test.

## Robustness
Pick the *relevant* subset, not all mechanically:
sensitivity analysis, bootstrap, perturbation, scenario, cross-validation,
parameter sweep, Monte Carlo, alternate-model, noise test.

## Numerical precision
Follow `precision-policy.yaml`: precision is governed by measurement precision,
metric, and competition style. Do not arbitrarily vary decimal places per chapter.

## Innovation gate
Do not write "首次提出 / 国际领先 / 显著优于现有方法 / 证明了" without
sufficient evidence. Unsupported superlatives fail review.
