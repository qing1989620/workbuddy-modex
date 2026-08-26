# 实验充分性 — 证据锚点门（v0.2）

> 实现：`paper/gates.py::experiment_sufficiency_gate`。

## 判定规则

1. **台账非空**：`contract.requires_experiments` 为真时，`experiments.jsonl`
   为空且论文含 claims/结果 ⇒ `EXPERIMENT_EVIDENCE_MISSING`（CRITICAL，
   伪造实验风险）；论文也无数值 ⇒ `NO_EXPERIMENTS`（HIGH）。
2. **比较类 claim**（type=comparative/causal）必须带 `evidence_ids`，
   否则 `UNSUPPORTED_CLAIM`（HIGH）。
3. **百分比提升断言**：正文出现
   `improve/reduce/outperform/提高/提升/降低/减少 + 数字 + %/％/个百分点`
   时，该行必须有 R-ID 锚点，或数字必须在 `results.jsonl` 的 value 集合中；
   否则 `UNSUPPORTED_CLAIM`（HIGH）。

## 工程陷阱（已修复）

- `%` 在 LaTeX 中是注释符，论文写作必须用 `23.5\%`；门正则须容忍转义
  （`\\?`），否则标准写法全部漏检。fixture EV05 用真实 `\%` 写法回归。

## agent 义务

- 每个实验结果写入 `state/experiments.jsonl`（run_id、模型、参数、指标、
  dataset_hash、code_hash），数值进 `state/results.jsonl` 并 `verified=True`
  后才允许进正文。
- 论文中每个提升/降低结论都要写 "（实验 R-XXX）" 或在同句给出台账值。
- 实验缺失时如实声明 `NO_EXPERIMENTS`，不虚构。
