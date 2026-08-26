# Paper Production Postmortem — 为什么低质量论文能通过旧 Gate

> 范围：OMMW v0.1 最后一次真实论文产物 `.build/demo4/`（城市配送需求预测题）。
> 目标：找出"占位符论文被标记 VERIFIED"的**系统性**根因，禁止归因于"模型能力有限"。
> 时间：2026-08-26。

## 1. 失败对象与证据

`.build/demo4/` 的量化体检：

| 指标 | 实测 | 高水平论文期望 |
|---|---|---|
| LaTeX 章节文件 | 10 个（abstract/introduction/models/results/…） | ≥8 个章节 |
| 章节真实内容 | 全部为 9 词占位符注释 | 每章 ≥250 有效词 |
| 显示公式 | 0 | 每模型章 ≥2，全篇 ≥8 |
| 图片 / 表格 | 0 / 0 | 每核心问题 ≥1 视觉证据 |
| 引用（\cite） | 0 | ≥10 |
| claims.jsonl | 0 行 | 与论文结论一一对应 |
| results.jsonl | 0 行 | 论文中每个数值都有台账行 |
| experiments.jsonl | 0 行 | 每个可复现实验有记录 |
| progress.json | `current_stage=RECEIVED, completed_stages=[]` | 逐阶段推进 |

**核心事实**：一个 progress 停留在 RECEIVED（什么都没做）的项目，曾被标记为 **VERIFIED** 并作为最终产物交付。

## 2. 根因分析（五个，全部是系统设计缺陷）

### R1. 空台账 ⇒ 空验证（vacuous pass）
`research_verify` 只检查"论文中的 claim/result 引用是否指向台账中的行"。台账为空时，**检查项为零个**，`passed=True` 恒成立。
- 数学上：`∀x∈∅: P(x)` 为真。
- 后果：占位符论文没有引用任何 ID → 没有可断言的链接 → 全绿。

### R2. 渲染器 Gate 只验证"能编译"
final-audit 对 LaTeX 产物的全部检查是"编译成功、PDF 存在"。一个 `% TODO` 注释也能编译成 PDF。
- "VERIFIED" 的实际语义退化为 "xelatex 退出码为 0"，与论文质量无关。

### R3. 没有内容门（摘要/公式/视觉/字数）
v0.1 不存在任何检查论文**内容**的确定性断言：
- 无摘要存在性检查（摘要缺失=CRITICAL 的规则缺失）；
- 无公式充分性检查（算法纯文字描述也可通过）；
- 无视觉证据检查（0 图 0 表不报警）；
- 无占位符/字数下限检查（9 词章节与 300 词章节同权）。

### R4. 状态机可无证据跳变
progress 从 RECEIVED 到 VERIFIED 之间没有"证据门槛"：没有 EVIDENCE_FREEZE、没有 CHAPTER_BLOCKED 回退，状态只增不减，到达即宣称。

### R5. 没有事后回捞机制
低质量产物一旦"通过"，不会进入任何复盘。失败发生在"最后一跳"，且没有任何日志解释它是如何发生的（demo4 的编译日志/台账时间线均为空）。

## 3. 为什么 demo4 能通过旧的最终 Gate（时序重建）

1. 章节文件被"写"出（含注释占位符）→ 结构计数通过；
2. `\documentclass`+`\begin{document}` 存在 → main.tex 可编译 → PDF 产出；
3. 论文无任何 R-/F-/C- ID → research_verify 零检查项 → passed；
4. final-audit 14 维中"论文质量"维度不存在或为空；
5. 状态推进到 VERIFIED，交付。

**没有一步检查过"这篇论文有没有内容"。**

## 4. 修复映射（根因 → v0.2 机制）

| 根因 | 修复 | 实现位置 |
|---|---|---|
| R1 空台账 vacuous pass | 台账为空且论文有数值/结论 → CRITICAL；论文数值必须能回溯台账 | `paper/gates.py` experiment/result gates；`verify.py` stub-section 扫描 |
| R2 只验编译 | 摘要硬门、公式充分性、视觉证据、图文耦合、实验充分性、叙事连续性、符号一致性、结果一致性、排版审计 共 9 类内容门 | `paper/gates.py` `run_all_paper_gates()` |
| R3 无内容断言 | 章节字数下限（模型章数×250）、占位符正则、公式密度双向异常（过稀/过胀） | `paper/density.py` + placeholder/formula gates |
| R4 状态跳变 | 状态机新增 EVIDENCE_FREEZE / CHAPTER_BLOCKED / ABSTRACT_GATE / FINAL_PAPER_GATE 等证据阶段，BLOCKED 终态 | `schemas/progress.py` Stage 枚举 |
| R5 无回捞 | 本章（postmortem）成为标准流程；`audit-paper` CLI 把一切失败落盘为审计报告 | `cli.py` audit-paper |

## 5. 回归证明（同一产物，新 Gate 下的行为）

对 `.build/demo4/` 原样重跑 v0.2 全部论文门 + research_verify：

```
CRITICAL:  ABSTRACT_MISSING, PAPER_CONTENT_INSUFFICIENT,
           PAPER_WITHOUT_VISUALS, PLACEHOLDER_SECTION
failed gates: abstract, placeholder, visual_evidence,
              figure_text_coupling, experiment_sufficiency
research_verify: passed=False
```

即：**demo4 的"VERIFIED"已被四个 CRITICAL 硬否决**。占位符论文不再可能静默通过。

## 6. 残留风险（诚实清单）

- 门是**确定性结构检查**，不"理解"数学：偷换证明步骤、伪公式（结构合法但逻辑错误）仍可能漏过——由 `parity`/人工审阅/章节 Manifest 兜底；
- 摘要硬门只验存在性与长度/量化线索，不评"摘要写得是否精彩"；
- 所有阈值（250 词、min 2 公式等）为工程门槛，需随真实论文语料校准；
- 双格式（latex/word）漂移只部分覆盖（ABSTRACT_NOT_IN_LATEX_SOURCES 为 MEDIUM）。

## 7. 结论

demo4 事件不是一次模型失误，而是**验证系统在"内容"维度上的结构性缺失**。v0.2 通过引入内容门 + 空台账硬否决 + 状态机证据门槛 + 复盘流程，把"能否通过"从"能否编译"修正为"内容是否真实完整可审计"。
