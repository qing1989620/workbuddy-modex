# 可视化证据与图文耦合（v0.2）

> 实现：`paper/gates.py::visual_evidence_gate` / `figure_text_coupling_gate` /
> `latex_layout_gate`。

## 可视证据门

- 每个核心问题（model 角色）章须有 ≥1 个资产（figure/table/tikz/algorithm），
  否则 `VISUAL_EVIDENCE_INSUFFICIENT`（HIGH）。
- 全篇资产为 0 ⇒ `PAPER_WITHOUT_VISUALS`（CRITICAL）。
- 豁免：`contract.justified_no_visual`（须审阅签字）。

## 图文耦合门

- `\label{fig:*}`/`\label{tab:*}` 必须被正文 `\ref`/`\eqref` 引用：
  `FIGURE_NOT_REFERENCED` / `TABLE_NOT_REFERENCED`（HIGH）。
  "图存在但正文从未讨论 = 没有图"。
- `\includegraphics` 段落缺 `\caption` ⇒ `FIGURE_NO_CAPTION`（MEDIUM）。
- `figures.jsonl` 注册表有、论文未引用的资产 ⇒ `ORPHAN_FIGURE_ASSET`（HIGH）。

## 排版审计（真实编译日志）

- 无 main.pdf ⇒ `PDF_NOT_BUILT`（MEDIUM，布局审计受限）。
- overfull hbox > 15pt（**含小数 pt，isdigit 归零 bug 已修**）⇒ `LAYOUT_OVERFULL`（HIGH）。
- undefined references ⇒ `UNDEFINED_REFERENCES`（CRITICAL）。
- Missing character ⇒ `MISSING_GLYPHS`（HIGH）；multiply defined labels ⇒
  `MULTIPLY_DEFINED_LABELS`（HIGH）。

## agent 义务

1. 每个核心问题至少一张图：结果对比图（带误差带）、模型结构图（tikz）、
   或数据可视化（台账 figures.jsonl 登记 F-ID）。
2. 图必须有 caption + label，且正文有一段"最重要的 pattern 是什么、为什么
   重要"的讨论（对照 EV04 负面样例）。
3. 论文交付前必须真实编译，把 log 交给 `latex_layout_gate` 审计；undefined
   refs 清零才可上报 VERIFIED。
