# Paper Production Kernel — 政策文档（v0.2）

> 控制面入口：`src/ommw/paper/`（contract/density/gates/scorecard）。
> 运行：`ommw audit-paper`、`ommw quality-gate`、`ommw paper-contract`。

## 使命

把"能写出论文"升级为"能稳定生产结构完整、推导充分、实验充分、图表充分、
文字紧凑、可逐章审计的高水平论文"。**判定由确定性代码执行**，agent 只负责
把论文做成能通过判定的样子，不允许"声称通过"。

## 核心语义

1. **论文不是事实源**：唯一事实源是 Research Core 台账（state/*.jsonl + yaml）。
   论文中的每个数字必须能回溯台账行（R-ID），每个结论应有 claim 记录。
2. **空台账 = 空验证**：台账为空时 `research_verify` 零检查项，恒真——这是
   v0.1 的 vacuous pass 根因。v0.2 起：台账为空但论文含数值/结论 →
   `EXPERIMENT_EVIDENCE_MISSING`（CRITICAL）。
3. **诚实规则（§66）**：门只做结构检测（计数/存在性/链接），不假装理解数学。
   "公式是否逻辑正确"超出确定性门的能力，由台账+人工审阅兜底。文档/报告不得
   写"数学验证通过"，只能写"结构门通过"。

## 门清单（run_all_paper_gates 输出 9 项）

| gate | 关键 code（CRITICAL 加粗） | 判定 |
|---|---|---|
| abstract | **ABSTRACT_MISSING** | 双格式摘要缺失 = 硬否决 |
| placeholder | **PLACEHOLDER_SECTION** / **PAPER_CONTENT_INSUFFICIENT** | 桩章节 / 词数 < 模型章数×250 |
| formula_sufficiency | FORMULA_DENSITY_WARNING / FORMULA_INFLATION_SUSPECTED | 公式下限与堆砌 |
| visual_evidence | **PAPER_WITHOUT_VISUALS** / VISUAL_EVIDENCE_INSUFFICIENT | 全篇无资产 / 单章无资产 |
| figure_text_coupling | FIGURE_NOT_REFERENCED / ORPHAN_FIGURE_ASSET | label-ref 闭环 |
| experiment_sufficiency | **EXPERIMENT_EVIDENCE_MISSING** / UNSUPPORTED_CLAIM | 台账非空 / 百分比断言有 R-ID |
| narrative_continuity | NARRATIVE_CONTINUITY_WARNING | 章间依赖有共享证据 token |
| symbol_consistency | SYMBOL_TABLE_SMALL / NOTATION_TABLE_MISSING | 符号登记与正文一致 |
| latex_layout | **UNDEFINED_REFERENCES** / LAYOUT_OVERFULL / MISSING_GLYPHS | 真实编译日志审计 |

`has_critical()`：任一 CRITICAL ⇒ 论文 BLOCKED，无视总分。

## 评分卡（quality-gate）

12 维加权合计 100 分；`COMPETITION_READY >= 88`；verdict ∈
BLOCKED/APPROVED/REVISE/COMPETITION_READY。每个 subscore 必须带 evidence
字符串（空 evidence 的维不得满分）。**评分是内部工程门槛，不是评委模拟。**

## 章节 Manifest（目标态）

每章一票证据：该章的 R/F/C/T-ID 引用、公式数、资产、词数。当前由 scorecard
按章计分 + `audits/chapter-density-report.json` 提供，v0.3 落盘
`state/chapter-manifest.yaml`。

## 模板

本地模板经 `ommw template-import` 导入：原件只读存档（sha256），真实
xelatex 编译通过才写入 "verified"；`templates/template-registry.json` 记录
role（PRIMARY/SECONDARY）。模板内嵌的第三方硬编码路径仅审计标注，不修改。

## 回归保障

`evals/paper-production/`（10 case：缺摘要/薄章/纯文字算法/无讨论图/无锚点
断言/断链问题/坏排版/公式堆砌/全篇无图/精品对照）+ `pytest` + `ommw
smoke-test`（5 类负面注入全部捕获）共同防退化。
