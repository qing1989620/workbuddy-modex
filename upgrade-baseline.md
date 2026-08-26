# OMMW v0.2 Upgrade Baseline — 模块级审计结论

> 审计范围：本次升级涉及的全部核心模块（论文生产链路）。
> 结论格式：KEEP / IMPROVE / REPLACE / MERGE / REMOVE / MISSING，每条附证据。
> 原则：不重复建设；不破坏 WorkBuddy 入口（`ommw install-adapter workbuddy` 与
> `~/.workbuddy/skills` 符号链接保持有效）。

## KEEP（保持原样，已满足需求）

| 模块 | 证据 |
|---|---|
| `src/ommw/paths.py` | ProjectPaths 纯 pathlib、可移植、CJK 路径安全（模板编译已验证） |
| `src/ommw/config.py` | 环境变量 > local toml > PATH 的引擎探测正确，无硬编码绝对路径 |
| `src/ommw/providers/` | 仅 adapter 壳，不参与论文内容判定，无需改动 |
| `src/ommw/adapters/` | WorkBuddy 入口 symlink 机制不变 |
| `schemas/*.json` | 5 个 JSON schema 结构稳定，doctor 校验通过 |

## IMPROVE（已改动，列改动点）

| 模块 | 改动 | 证据 |
|---|---|---|
| `src/ommw/verify.py` | 新增 `scan_for_stub_section` 桩章节扫描；`_effective_words` 剔注释计词 | 空台账 vacuous pass 修复的组件之一 |
| `src/ommw/final_audit.py` | 第 14 维接入 `run_all_paper_gates`，LOW 降噪，`paper:*` 前缀并入 | demo4 现被 4 CRITICAL 否决 |
| `src/ommw/cli.py` | 新增 paper-contract / audit-paper / quality-gate / template-import / template-list / template-select | 审计与模板管理 CLI 化 |
| `src/ommw/doctor.py` | 新增 PAPER:kernel / PAPER:production-evals / TEMPLATES:local-registry | doctor 可验证 v0.2 新面 |
| `src/ommw/smoke.py` | 冒烟项目升级为最小完整真实论文；5 类负面注入 | 正向全过 + 注入全捕获 |
| `src/ommw/schemas/progress.py` | Stage 追加 EVIDENCE_FREEZE/PAPER_CONTRACT/NARRATIVE_BACKBONE/VISUAL_PLAN/ABSTRACT_SYNTHESIS/ABSTRACT_GATE/CHAPTERS_VERIFIED/CHAPTER_BLOCKED/EVIDENCE_GAP/LATEX_VERIFIED/PDF_VISUAL_QA/CITATION_AUDIT/RESULT_CONSISTENCY/FINAL_PAPER_GATE/COMPETITION_READY/BLOCKED | 状态机证据门槛 |

## NEW（本次新增）

| 模块 | 职责 | 证据 |
|---|---|---|
| `src/ommw/paper/density.py` | 章节密度静态分析（CJK 计词、公式/图/表/引用计数、AI 味短语、双向异常） | EV03/EV08 回归 |
| `src/ommw/paper/gates.py` | 9 类内容门 + `run_all_paper_gates` + CRITICAL_CODES + 审计捆绑 | 10/10 evals |
| `src/ommw/paper/scorecard.py` | 12 维加权评分卡，88 分 COMPETITION_READY，critical 一票否决 | quality-gate CLI |
| `src/ommw/paper/contract.py` | QuestionContract / PaperContract / gate_options 展平 | paper-contract CLI |
| `src/ommw/templates_local.py` | 模板导入管线（raw→staging→normalized→reports→registry）+ 真实编译 | 双模板 PASS + demo 压测 |
| `templates/local/reports/*` | 导入报告 ×2、demo 压测报告 ×2、对比报告 ×1 | 全部真实编译生成 |
| `evals/paper-production/` | cases.yaml + run_evals.py，10 个回归 Eval | EV01-EV10 全 PASS |
| `scripts/make_template_demos.py` | §73 压力测试 demo 生成 + 真编译 | 双模板 PASS/5p |
| `scripts/finalize_template_registry.py` | role 写入 + 13 维对比报告 | registry 双 PRIMARY |

## REPLACE / MERGE / REMOVE（无需发生）

- 无模块被整体替换：Kernel 以新增 `paper/` 包实现，不与旧链路冲突。
- 无模块需要合并。
- 无删除：`_compile_test` 等产物目录以 `_` 前缀 + gitignore 隔离，不进入交付。

## MISSING（本次明确补上，未来仍需演进）

| 缺口 | 现状 | 后续 |
|---|---|---|
| 章节 Manifest（每章一票证据） | scorecard 按章计分但未导出 manifest 文件 | v0.3 `state/chapter-manifest.yaml` |
| PDF 视觉 QA 自动化 | PDF_PAGES 仅计数页数 | 图像化 PDF 渲染 + 空白页检测 |
| 结果一致性对台账数值的字面匹配 | gate 依赖 R-ID 锚点 | 数字归一化对账（如 0.7054 vs .705） |
| evals 覆盖双格式 parity | 现有 evals 只测 LaTeX 侧 gate | word 侧 gate 回归 |

## 未审计模块（诚实清单，v0.3 队列）

`src/ommw/research/`、`render/`（latex/word 渲染器核心）、`state/`（台账读写之外的业务）、
`knowledge_base/`、`docs/`、`providers/scientific-skills` 适配细节——
本次升级聚焦论文生产链路，未逐行复审上述模块；doctor 全绿，但"未审 ≠ 已审"。

## 不变量保持（§83 抽查）

- 无硬编码 `D:\`、`/Users/`、`/home/` 进入核心源码（新增代码全部经 config/paths 间接引用）；
- 原压缩包只读（`templates/local/raw/` sha256 存档，`staging/` 可重建）；
- "Template verified" 只在真实编译产出 PDF 后写入（`verified_at` 字段）；
- WorkBuddy 入口：`ommw install-adapter workbuddy` 链不触碰。
