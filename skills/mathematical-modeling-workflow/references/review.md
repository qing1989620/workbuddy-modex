# Review: Three-Layer + Adversarial

Each critical chapter passes three reviewers, then optionally an adversarial one.

## 1. Mathematical reviewer
- Correctness of formulations, derivations, and units.
- Notation consistency with `notation.yaml` (unique symbols).
- Dimensional/units consistency.
- Numerical stability of proposed solvers.

## 2. Scientific reviewer
- Does the evidence (Result IDs) actually support the claim?
- Statistical validity (assumptions, effect size, CI, sample size, multiple testing).
- Experimental validity (data hash + code hash recorded; reproducible).
- Baseline present and fair.

## 3. Competition judge reviewer
- Presentation clarity and structure.
- Highlights and scoring value for the target competition profile.
- Conciseness; no AI filler / no unsupported superlatives.
- Figure/table quality and caption adequacy.

## 4. Adversarial reviewer (Medium/High-risk chapters)
Goal: *try to prove the chapter wrong*. Probe assumptions, edge cases,
counterexamples, data leakage, overfitting, cherry-picked seeds.

## Finding structure
```
finding_id, severity (CRITICAL|HIGH|MEDIUM|LOW), section, claim,
problem, evidence, required_fix, status, verification
```

## Closure workflow
`OPEN -> FIXED -> REVERIFIED -> CLOSED`. A finding is not CLOSED until
re-verified. CRITICAL/HIGH findings block chapter acceptance.

## Judge reads evidence only
The judge reviewer reads problem + paper + evidence manifest — **never the
writer's self-assessment** — to avoid anchoring. Quality is a gate (any
CRITICAL/HIGH open finding = not accepted), not a numeric score.
