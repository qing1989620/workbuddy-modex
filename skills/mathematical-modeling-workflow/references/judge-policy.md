# 评分卡与判卷政策（v0.2）

> 实现：`paper/scorecard.py`。CLI：`ommw quality-gate`。

## 12 维权重（合计 100）

| 维度 | 权重 | 要点 |
|---|---|---|
| mathematical_formulation | 15 | 公式充分性、推导链、符号一致 |
| experimental_evidence | 12 | 台账非空、R-ID 锚点、实验完整性 |
| visualization | 10 | 可视证据、图文耦合 |
| results_consistency | 10 | 论文数值 ↔ 台账一致 |
| abstract_quality | 8 | 摘要硬门 + 三要素 |
| structure_completeness | 8 | 章节清单、词数下限 |
| narrative_coherence | 8 | 问题依赖链、章节衔接 |
| citation_quality | 8 | 引用真实、格式、与 claim 匹配 |
| latex_layout | 8 | 编译日志审计 |
| symbol_discipline | 5 | 符号表、定义-使用一致 |
| language_density | 4 | 无套话、AI 味短语少 |
| competition_compliance | 4 | 页数、AI 使用声明、赛事约束 |

## 判卷政策（§62 精神）

1. **CRITICAL 一票否决**：`has_critical()` 非空 ⇒ verdict 恒为 BLOCKED，
   不看总分。摘要缺失/全篇无图/占位符章节/台账为空都属此类。
2. 总分门槛：`COMPETITION_READY >= 88`；`APPROVED >= 75`；否则 REVISE。
3. **每个 subscore 必须带 evidence 字符串**——没有证据的维不得给满分，
   空 evidence 视为未检查。
4. **评分是内部工程门槛，不是评委模拟**：分数只反映"结构完备度"，
   不承诺获奖等级。对外报告不得把分数当"预测评委给分"。
5. 分数与 verdict 是给 agent 自身的反馈回路：REVISE/BLOCKED 时必须回退到
   对应章节修改，而不是改分数。

## 输出

`audits/paper-quality-scorecard.json`（12 维 + total + verdict + critical
列表）+ 控制台表格。CLI 在 BLOCKED 时 exit 1（CI 可挂接）。
