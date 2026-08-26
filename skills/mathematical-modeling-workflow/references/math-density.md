# 公式充分性 — 双向密度检测（v0.2）

> 实现：`paper/density.py`（统计）+ `paper/gates.py::formula_sufficiency_gate`。
> 词数口径：**散文词数**（先剔除 display/inline 数学环境再计词，防止公式堆砌
> 自我抬高词数）。

## 阈值

| 检查 | 触发条件 | 级别 |
|---|---|---|
| 纯文字模型章 | display+inline == 0 且 words > 100 | HIGH `FORMULA_DENSITY_WARNING` |
| 公式不足 | display < `min_display_equations`（默认 2）且 words > 150 | HIGH `FORMULA_DENSITY_WARNING` |
| 墙式文字 | words / effective_equations > WORDS_PER_EQ_ANOMALY | MEDIUM `FORMULA_DENSITY_ANOMALY` |
| **公式堆砌** | display > 40 且 words < 200 | MEDIUM `FORMULA_INFLATION_SUSPECTED` |

`min_display_equations` 可经 `state/paper-contract.yaml` 按章定制；豁免章
写入 `justified_low_formula_density`（须人工审阅签字，见 contract）。

## 工程陷阱（已修复，回归锁定）

1. 词数必须剔除数学 token：修复前公式越多 words 越大，`words < 200` 的
   堆砌检测永远不触发（自我抵消）。
2. `RE_DISPLAY_EQ` 必须匹配**整个环境体**（含 `\end{...}` 反向引用），仅匹配
   `\begin{...}` 标记会导致剔除无效。

## agent 义务

- 算法/模型章至少 2 个 display 公式（推导、定义、估计式），并给标签
  `eq:*` 供正文 `\eqref`。
- 禁止"凑公式"：同式多次复制、无释义的公式 dump 会触发堆砌标记。
- 公式要解释：每个公式后应有 1-3 句"它为什么长这样"。

## 诚实边界

门验证"公式存在且成体系"，不验证"公式推导正确"。推导正确性由台账
（符号定义、实验复现）与人审负责。
