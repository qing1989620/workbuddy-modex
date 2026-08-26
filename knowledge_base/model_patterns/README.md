# Model pattern example (decision-focused, not a textbook)

Entry schema: when_to_use / when_not_to_use / assumptions / strength / weakness
/ validation / common_failure / alternatives.

## Pattern: Linear regression for prediction
- **when_to_use**: tabular data, near-linear relation, need interpretability,
  small-medium n, baseline comparison required.
- **when_not_to_use**: strong nonlinearity, high collinearity without
  regularization, heteroscedastic heavy-tail errors.
- **assumptions**: linearity, independence, homoscedasticity, no exact
  multicollinearity.
- **strength**: interpretable coefficients, closed-form, fast, low variance.
- **weakness**: bias under misspecification.
- **validation**: residual analysis, CV/time-based split.
- **common_failure**: forgetting to check residuals; treating R^2 as proof.
- **alternatives**: ridge/lasso, GAM, tree ensembles (only if evidenced).

## Pattern: LP/MILP for optimization
- **when_to_use**: linear objective + linear constraints; integer decisions.
- **when_not_to_use**: non-convex objective without integer structure — then
  consider dedicated solvers or (only with reason) metaheuristics.
- **common_failure**: using GA "to look advanced" when a solver terminates in
  milliseconds with a global optimum.

Sources: recorded in provenance/SOURCES.lock.json. Do not treat this file as
exhaustive — extend it only with verified, sourced entries.
